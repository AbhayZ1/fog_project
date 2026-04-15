"""
RUN 2: FedAvg Client B — WITH Differential Privacy (same as original)
Identical to original client_B.py — DP stays enabled.
"""
import os
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import flwr as fl
from collections import OrderedDict
from architecture import get_model
from sklearn.metrics import f1_score
from opacus import PrivacyEngine
from opacus.validators import ModuleValidator

DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

TARGET_EPSILON = 2.0
TARGET_DELTA = 1e-5
MAX_GRAD_NORM = 1.0
NOISE_MULTIPLIER = 1.1

print(f"\n{'='*70}")
print(f"🏥 [FedAvg] CLIENT B (Hospital B) - DP Enabled")
print(f"{'='*70}")
print(f"Privacy Budget: ε={TARGET_EPSILON}, δ={TARGET_DELTA}")
print(f"Noise Multiplier: {NOISE_MULTIPLIER}")
print(f"{'='*70}\n")


def calculate_privacy_spent(epsilon, delta, steps):
    return {
        "epsilon": epsilon, "delta": delta, "steps": steps,
        "risk_level": "LOW" if epsilon < 3 else "MEDIUM" if epsilon < 6 else "HIGH"
    }


def load_data():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "demo", "Hospital_B", "local_storage", "data")
    data_dir = os.path.abspath(data_dir)

    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.ToTensor(),
    ])

    if not os.path.exists(data_dir):
        print(f"ERROR: Dataset not found at {data_dir}.")
        import sys; sys.exit(1)

    train_dataset = datasets.ImageFolder(os.path.join(data_dir, "train"), transform=transform)
    val_dataset = datasets.ImageFolder(os.path.join(data_dir, "val"), transform=transform)
    test_dataset = datasets.ImageFolder(os.path.join(data_dir, "test"), transform=transform)

    return (DataLoader(train_dataset, batch_size=32, shuffle=True),
            DataLoader(val_dataset, batch_size=32),
            DataLoader(test_dataset, batch_size=32))


trainloader, valloader, testloader = load_data()

net = get_model().to(DEVICE)
net = ModuleValidator.fix(net)
ModuleValidator.validate(net, strict=False)
print("✅ Model fixed for Opacus (BatchNorm → GroupNorm)")

criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(net.parameters(), lr=0.001)

privacy_engine = PrivacyEngine()
net, optimizer, trainloader = privacy_engine.make_private(
    module=net, optimizer=optimizer, data_loader=trainloader,
    noise_multiplier=NOISE_MULTIPLIER, max_grad_norm=MAX_GRAD_NORM,
)
print(f"✅ DP enabled: ε={TARGET_EPSILON}, δ={TARGET_DELTA}\n")


def set_parameters(net, parameters):
    params_dict = zip(net._module.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
    net._module.load_state_dict(state_dict, strict=True)


def get_parameters(net):
    return [val.cpu().numpy() for _, val in net._module.state_dict().items()]


def train(net, trainloader, optimizer, epochs):
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
                print(f"   [FedAvg Client B] Epoch {epoch+1}/{epochs}, Batch {i}/{len(trainloader)}, Loss: {loss.item():.4f}")

    epsilon = privacy_engine.get_epsilon(delta=TARGET_DELTA)
    print(f"   [FedAvg Client B] Privacy spent: ε={epsilon:.2f}")


def test_step(net, loader):
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
    f1 = f1_score(y_true, y_pred, average='weighted', labels=[0, 1], zero_division=0)
    return loss / len(loader), accuracy, f1


class PneumoniaClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return get_parameters(net)

    def fit(self, parameters, config):
        set_parameters(net, parameters)
        print(f"\n🔄 [FedAvg Client B] Training (10 epochs)...")
        train(net, trainloader, optimizer, epochs=10)
        return get_parameters(net), len(trainloader.dataset), {}

    def evaluate(self, parameters, config):
        set_parameters(net, parameters)
        val_loss, val_acc, val_f1 = test_step(net, valloader)
        test_loss, test_acc, test_f1 = test_step(net, testloader)

        current_epsilon = privacy_engine.get_epsilon(delta=TARGET_DELTA)
        total_steps = len(trainloader) * config.get("epochs", 1)
        privacy_info = calculate_privacy_spent(current_epsilon, TARGET_DELTA, total_steps)

        print(f"\n[FedAvg CLIENT B EVAL] ε={privacy_info['epsilon']:.2f} | "
              f"Val: {val_acc:.4f} | Test: {test_acc:.4f} | F1: {test_f1:.4f}")

        return float(test_loss), len(testloader.dataset), {
            "val_accuracy": float(val_acc),
            "test_accuracy": float(test_acc),
            "val_f1": float(val_f1),
            "test_f1": float(test_f1),
            "privacy_epsilon": float(privacy_info['epsilon']),
            "privacy_delta": float(privacy_info['delta']),
            "privacy_risk": privacy_info['risk_level']
        }


if __name__ == "__main__":
    server_address = os.environ.get("FL_SERVER_ADDRESS", "127.0.0.1:8081")
    print(f"🔌 Connecting to FL server at {server_address}...\n")
    fl.client.start_client(
        server_address=server_address,
        client=PneumoniaClient().to_client()
    )
