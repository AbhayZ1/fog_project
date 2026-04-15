"""
RUN 1: No-DP Client B — NO Differential Privacy
Same training loop but without Opacus PrivacyEngine.
Uses GroupNorm (via ModuleValidator.fix) for architecture consistency.
"""
import os
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import flwr as fl
from collections import OrderedDict
from architecture import get_model
from sklearn.metrics import f1_score
from opacus.validators import ModuleValidator

DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

print(f"\n{'='*70}")
print(f"🏥 [NO-DP] CLIENT B (Hospital B) - No Differential Privacy")
print(f"{'='*70}\n")


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

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32)
    test_loader = DataLoader(test_dataset, batch_size=32)

    return train_loader, val_loader, test_loader


trainloader, valloader, testloader = load_data()

# Model setup — use GroupNorm for consistency
net = get_model().to(DEVICE)
net = ModuleValidator.fix(net)
print("✅ Model: GroupNorm (consistent with original architecture)")

criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(net.parameters(), lr=0.001)

# NO PrivacyEngine — standard training
print("✅ No Differential Privacy — standard SGD training\n")


def set_parameters(net, parameters):
    params_dict = zip(net.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
    net.load_state_dict(state_dict, strict=True)


def get_parameters(net):
    return [val.cpu().numpy() for _, val in net.state_dict().items()]


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
                print(f"   [NO-DP Client B] Epoch {epoch+1}/{epochs}, Batch {i}/{len(trainloader)}, Loss: {loss.item():.4f}")


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
        print(f"\n🔄 [NO-DP Client B] Starting local training (10 epochs)...")
        train(net, trainloader, optimizer, epochs=10)
        return get_parameters(net), len(trainloader.dataset), {}

    def evaluate(self, parameters, config):
        set_parameters(net, parameters)
        val_loss, val_acc, val_f1 = test_step(net, valloader)
        test_loss, test_acc, test_f1 = test_step(net, testloader)

        print(f"\n{'='*70}")
        print(f"[NO-DP CLIENT B EVAL]")
        print(f"   Val Acc: {val_acc:.4f}, Test Acc: {test_acc:.4f}, F1: {test_f1:.4f}")
        print(f"{'='*70}\n")

        return float(test_loss), len(testloader.dataset), {
            "val_accuracy": float(val_acc),
            "test_accuracy": float(test_acc),
            "val_f1": float(val_f1),
            "test_f1": float(test_f1),
            "privacy_epsilon": 0.0,
            "privacy_delta": 0.0,
            "privacy_risk": "N/A"
        }


if __name__ == "__main__":
    server_address = os.environ.get("FL_SERVER_ADDRESS", "127.0.0.1:8080")
    print(f"🔌 Connecting to FL server at {server_address}...\n")
    fl.client.start_client(
        server_address=server_address,
        client=PneumoniaClient().to_client()
    )
