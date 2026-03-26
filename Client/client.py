# --- PATH SETUP ---
import os
import argparse
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import flwr as fl
from collections import OrderedDict
from architecture import get_model
from sklearn.metrics import f1_score 

# Import Opacus for Differential Privacy
from opacus import PrivacyEngine
from opacus.validators import ModuleValidator

# --- Configuration ---
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Differential Privacy Configuration
TARGET_EPSILON = 2.0      # Privacy budget (ε) - lower = more private
TARGET_DELTA = 1e-5       # Probability of privacy breach (δ)
MAX_GRAD_NORM = 1.0       # Gradient clipping threshold
NOISE_MULTIPLIER = 1.1    # Noise scale for DP

# Argument Parser
parser = argparse.ArgumentParser(description='Flower Client')
parser.add_argument('--client_id', type=str, required=True, help='Client ID (e.g., Hospital A)')
parser.add_argument('--data_dir', type=str, required=True, help='Path to local data directory')
args = parser.parse_args()

CLIENT_ID = args.client_id
DATA_DIR = args.data_dir

print(f"\n{'='*70}")
print(f"🏥 CLIENT: {CLIENT_ID} - Initializing")
print(f"{'='*70}")
print(f"Data Source: {DATA_DIR}")
print(f"Privacy Budget: ε={TARGET_EPSILON}, δ={TARGET_DELTA}")
print(f"Gradient Clipping: {MAX_GRAD_NORM}")
print(f"Noise Multiplier: {NOISE_MULTIPLIER}")
print(f"{'='*70}\n")


def calculate_privacy_spent(epsilon, delta, steps):
    """Calculate cumulative privacy budget spent"""
    privacy_spent = {
        "epsilon": epsilon,
        "delta": delta,
        "steps": steps,
        "risk_level": "LOW" if epsilon < 3 else "MEDIUM" if epsilon < 6 else "HIGH"
    }
    return privacy_spent


def load_data():
    """Load training, validation, and test data."""
    
    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.ToTensor(),
    ])
    
    if not os.path.exists(DATA_DIR):
        print(f"ERROR: Dataset not found at {DATA_DIR}.")
        import sys
        sys.exit(1)

    train_dataset = datasets.ImageFolder(os.path.join(DATA_DIR, "train"), transform=transform)
    val_dataset = datasets.ImageFolder(os.path.join(DATA_DIR, "val"), transform=transform)
    test_dataset = datasets.ImageFolder(os.path.join(DATA_DIR, "test"), transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32)
    test_loader = DataLoader(test_dataset, batch_size=32)
    
    return train_loader, val_loader, test_loader


# Load data
trainloader, valloader, testloader = load_data()

# --- Model Components ---
net = get_model().to(DEVICE)

# Fix BatchNorm for Opacus BEFORE wrapping
net = ModuleValidator.fix(net)
ModuleValidator.validate(net, strict=False)
print("✅ Model fixed for Opacus compatibility (BatchNorm → GroupNorm)")

criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(net.parameters(), lr=0.001)

# Attach Privacy Engine
privacy_engine = PrivacyEngine()

net, optimizer, trainloader = privacy_engine.make_private(
    module=net,
    optimizer=optimizer,
    data_loader=trainloader,
    noise_multiplier=NOISE_MULTIPLIER,
    max_grad_norm=MAX_GRAD_NORM,
)

print(f"✅ Differential Privacy enabled with Opacus")
print(f"   Target: ε={TARGET_EPSILON}, δ={TARGET_DELTA}\n")


def set_parameters(net, parameters):
    """Sets model weights from server."""
    params_dict = zip(net._module.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
    net._module.load_state_dict(state_dict, strict=True)


def get_parameters(net):
    """Returns model weights to send to server."""
    return [val.cpu().numpy() for _, val in net._module.state_dict().items()]


def train(net, trainloader, optimizer, epochs: int):
    """Train with Differential Privacy."""
    net.train()
    for epoch in range(epochs):
        for i, (inputs, labels) in enumerate(trainloader):
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = net(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            if i % 10 == 0:
                print(f"   [{CLIENT_ID}] Epoch {epoch+1}/{epochs}, Batch {i}/{len(trainloader)}, Loss: {loss.item():.4f}")
    
    # Calculate actual privacy spent
    epsilon = privacy_engine.get_epsilon(delta=TARGET_DELTA)
    print(f"   [{CLIENT_ID}] Privacy spent: ε={epsilon:.2f} (target: {TARGET_EPSILON}, δ={TARGET_DELTA})")


def test_step(net, loader):
    """Evaluate model and return loss, accuracy, and F1 score."""
    net.eval()
    loss, total, correct = 0.0, 0, 0
    y_true, y_pred = [], []
    
    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            outputs = net(inputs)
            loss += criterion(outputs, labels).item()
            
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            y_true.extend(labels.cpu().numpy())
            y_pred.extend(predicted.cpu().numpy())
            
    accuracy = correct / total
    f1 = f1_score(y_true, y_pred, average='weighted', labels=[0,1], zero_division=0)
    
    return loss / len(loader), accuracy, f1


# --- Flower Client ---
class PneumoniaClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return get_parameters(net)

    def fit(self, parameters, config):
        set_parameters(net, parameters)
        print(f"\n🔄 [{CLIENT_ID}] Starting local training (10 epochs)...")
        train(net, trainloader, optimizer, epochs=10) 
        return get_parameters(net), len(trainloader.dataset), {}

    def evaluate(self, parameters, config):
        set_parameters(net, parameters)
        
        # Evaluate on validation and test sets
        val_loss, val_acc, val_f1 = test_step(net, valloader)
        test_loss, test_acc, test_f1 = test_step(net, testloader)
        
        # Calculate privacy spent
        total_steps = len(trainloader) * config.get("epochs", 10)
        current_epsilon = privacy_engine.get_epsilon(delta=TARGET_DELTA)
        privacy_info = calculate_privacy_spent(
            epsilon=current_epsilon,
            delta=TARGET_DELTA,
            steps=total_steps
        )
        
        print(f"\n{'='*70}")
        print(f"[{CLIENT_ID} EVAL] Privacy Budget Status:")
        print(f"   ε (epsilon): {privacy_info['epsilon']:.2f}")
        print(f"   δ (delta): {privacy_info['delta']:.2e}")
        print(f"   Risk Level: {privacy_info['risk_level']}")
        print(f"{'='*70}")
        print(f"   Val Acc: {val_acc:.4f}, Test Acc: {test_acc:.4f}, F1: {test_f1:.4f}")
        print(f"{'='*70}\n")
        
        return float(test_loss), len(testloader.dataset), {
            "val_accuracy": float(val_acc),
            "test_accuracy": float(test_acc),
            "val_f1": float(val_f1),
            "test_f1": float(test_f1),
            # Privacy tracking
            "privacy_epsilon": float(privacy_info['epsilon']),
            "privacy_delta": float(privacy_info['delta']),
            "privacy_risk": privacy_info['risk_level']
        }


if __name__ == "__main__":
    server_address = os.environ.get("FL_SERVER_ADDRESS", "127.0.0.1:8080")
    print(f"🔌 Connecting to FL server at {server_address}...\n")
    fl.client.start_client(
        server_address=server_address, 
        client=PneumoniaClient().to_client()
    )
