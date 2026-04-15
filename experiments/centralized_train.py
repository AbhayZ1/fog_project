"""
RUN 3: Centralized Baseline — No Federation, No DP
Trains the same model architecture on ALL data combined.
Uses early stopping (patience=10 on val accuracy).
Saves results to centralized_baseline.json.
"""
import os
import sys
import json
import time
import torch
import torch.nn as nn
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, ConcatDataset
from sklearn.metrics import f1_score

sys.path.insert(0, os.path.dirname(__file__))
from architecture import get_model

DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
MAX_EPOCHS = 250  # 25 rounds × 10 local epochs equivalent
EARLY_STOP_PATIENCE = 10
BATCH_SIZE = 32
LR = 0.001
OUTPUT_FILE = "centralized_baseline.json"

print(f"\n{'='*70}")
print(f"🚀 [RUN 3] CENTRALIZED BASELINE — No Federation, No DP")
print(f"{'='*70}")
print(f"Max Epochs:    {MAX_EPOCHS}")
print(f"Early Stop:    patience={EARLY_STOP_PATIENCE}")
print(f"Batch Size:    {BATCH_SIZE}")
print(f"Learning Rate: {LR}")
print(f"Device:        {DEVICE}")
print(f"{'='*70}\n")


def load_combined_data():
    """Combine data from both hospitals."""
    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.ToTensor(),
    ])

    base = os.path.join(os.path.dirname(__file__), "..", "demo")
    base = os.path.abspath(base)

    train_datasets, val_datasets, test_datasets = [], [], []

    for hospital in ["Hospital_A", "Hospital_B"]:
        data_dir = os.path.join(base, hospital, "local_storage", "data")
        if not os.path.exists(data_dir):
            print(f"ERROR: Data not found at {data_dir}")
            sys.exit(1)

        train_datasets.append(datasets.ImageFolder(os.path.join(data_dir, "train"), transform=transform))
        val_datasets.append(datasets.ImageFolder(os.path.join(data_dir, "val"), transform=transform))
        test_datasets.append(datasets.ImageFolder(os.path.join(data_dir, "test"), transform=transform))

    train_combined = ConcatDataset(train_datasets)
    val_combined = ConcatDataset(val_datasets)
    test_combined = ConcatDataset(test_datasets)

    print(f"📊 Combined dataset:")
    print(f"   Train: {len(train_combined)} samples")
    print(f"   Val:   {len(val_combined)} samples")
    print(f"   Test:  {len(test_combined)} samples\n")

    return (DataLoader(train_combined, batch_size=BATCH_SIZE, shuffle=True),
            DataLoader(val_combined, batch_size=BATCH_SIZE),
            DataLoader(test_combined, batch_size=BATCH_SIZE))


def evaluate(model, loader, criterion):
    model.eval()
    loss, total, correct = 0.0, 0, 0
    y_true, y_pred = [], []

    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            outputs = model(inputs)
            loss += criterion(outputs, labels).item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            y_true.extend(labels.cpu().numpy())
            y_pred.extend(predicted.cpu().numpy())

    acc = correct / total
    f1 = f1_score(y_true, y_pred, average='weighted', labels=[0, 1], zero_division=0)
    return loss / len(loader), acc, f1


def main():
    trainloader, valloader, testloader = load_combined_data()

    # Use original architecture (BatchNorm is fine here, no Opacus)
    model = get_model().to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    print(f"Model: {model.__class__.__name__}")
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {total_params:,}\n")

    best_val_acc = 0.0
    patience_counter = 0
    history = []
    start_time = time.time()

    for epoch in range(1, MAX_EPOCHS + 1):
        # Training
        model.train()
        epoch_loss = 0.0
        batch_count = 0
        for i, (inputs, labels) in enumerate(trainloader):
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            batch_count += 1

            if i % 20 == 0:
                print(f"   [Centralized] Epoch {epoch}/{MAX_EPOCHS}, Batch {i}/{len(trainloader)}, Loss: {loss.item():.4f}")

        avg_train_loss = epoch_loss / batch_count

        # Validation
        val_loss, val_acc, val_f1 = evaluate(model, valloader, criterion)
        test_loss, test_acc, test_f1 = evaluate(model, testloader, criterion)

        elapsed = (time.time() - start_time) / 60

        epoch_data = {
            "epoch": epoch,
            "train_loss": round(avg_train_loss, 6),
            "val_loss": round(val_loss, 6),
            "val_accuracy": round(val_acc, 6),
            "val_f1": round(val_f1, 6),
            "test_accuracy": round(test_acc, 6),
            "test_f1": round(test_f1, 6),
            "elapsed_minutes": round(elapsed, 2)
        }
        history.append(epoch_data)

        print(f"\n   Epoch {epoch}: Train Loss={avg_train_loss:.4f} | "
              f"Val Acc={val_acc:.4f} | Test Acc={test_acc:.4f} | "
              f"F1={test_f1:.4f} | Time={elapsed:.1f}m")

        # Early stopping
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), "centralized_model_best.pth")
            print(f"   ✅ New best val accuracy: {val_acc:.4f}")
        else:
            patience_counter += 1
            print(f"   ⏳ No improvement ({patience_counter}/{EARLY_STOP_PATIENCE})")

        if patience_counter >= EARLY_STOP_PATIENCE:
            print(f"\n🛑 Early stopping at epoch {epoch} (no improvement for {EARLY_STOP_PATIENCE} epochs)")
            break

        # Save intermediate results
        with open(OUTPUT_FILE, 'w') as f:
            json.dump({
                "config": {
                    "max_epochs": MAX_EPOCHS,
                    "early_stop_patience": EARLY_STOP_PATIENCE,
                    "batch_size": BATCH_SIZE,
                    "learning_rate": LR,
                    "federation": "NONE (centralized)",
                    "dp": "DISABLED"
                },
                "epochs_completed": epoch,
                "best_val_accuracy": round(best_val_acc, 6),
                "history": history
            }, f, indent=4)

    total_time = (time.time() - start_time) / 60

    # Final evaluation with best model
    model.load_state_dict(torch.load("centralized_model_best.pth", map_location=DEVICE))
    final_test_loss, final_test_acc, final_test_f1 = evaluate(model, testloader, criterion)
    final_val_loss, final_val_acc, final_val_f1 = evaluate(model, valloader, criterion)

    result = {
        "config": {
            "max_epochs": MAX_EPOCHS,
            "early_stop_patience": EARLY_STOP_PATIENCE,
            "batch_size": BATCH_SIZE,
            "learning_rate": LR,
            "federation": "NONE (centralized)",
            "dp": "DISABLED"
        },
        "epochs_completed": len(history),
        "best_val_accuracy": round(best_val_acc, 6),
        "final_val_accuracy": round(final_val_acc, 6),
        "final_val_f1": round(final_val_f1, 6),
        "final_test_accuracy": round(final_test_acc, 6),
        "final_test_f1": round(final_test_f1, 6),
        "total_time_minutes": round(total_time, 2),
        "history": history
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=4)

    print(f"\n{'='*70}")
    print(f"🎉 [RUN 3] CENTRALIZED TRAINING COMPLETE!")
    print(f"{'='*70}")
    print(f"Epochs:        {len(history)}")
    print(f"Best Val Acc:  {best_val_acc:.4f}")
    print(f"Final Test Acc:{final_test_acc:.4f}")
    print(f"Final Test F1: {final_test_f1:.4f}")
    print(f"Time:          {total_time:.1f} minutes")
    print(f"Results:       {OUTPUT_FILE}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
