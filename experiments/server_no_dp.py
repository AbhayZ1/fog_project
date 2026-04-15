"""
RUN 1: No-DP Baseline Server
Same as original server.py but saves metrics to fl_metrics_no_dp.json.
Still uses FedProx (mu=0.01) — only DP is disabled on clients.
"""
import flwr as fl
import torch
from collections import OrderedDict
from typing import Dict, Optional, Tuple, List
from architecture import get_model
from opacus.validators import ModuleValidator
import json
import os
import time
from datetime import datetime
import shutil

# Model versioning configuration
MODELS_DIR = "model_registry_no_dp"
MAX_VERSIONS_TO_KEEP = 5

# --- Configuration ---
NUM_ROUNDS = 25
NUM_CLIENTS = 2
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
METRICS_FILE = "fl_metrics_no_dp.json"
MODEL_FILE = "global_model_no_dp.pth"

# FedProx Configuration (same as original)
PROXIMAL_MU = 0.01

# Track training statistics
training_start_time = None


def get_initial_parameters() -> fl.common.Parameters:
    net = get_model()
    # Keep GroupNorm for consistency with original architecture
    net = ModuleValidator.fix(net)
    print("✅ Server model fixed (BatchNorm → GroupNorm) for consistency")
    state_dict = net.state_dict()
    parameters = [val.cpu().numpy() for _, val in state_dict.items()]
    return fl.common.ndarrays_to_parameters(parameters)


def calculate_training_stats(round_num, total_rounds, start_time):
    elapsed = time.time() - start_time
    rounds_remaining = total_rounds - round_num
    avg_time_per_round = elapsed / round_num if round_num > 0 else 0
    eta_seconds = avg_time_per_round * rounds_remaining
    return {
        "elapsed_minutes": elapsed / 60,
        "eta_minutes": eta_seconds / 60,
        "training_speed": round_num / (elapsed / 60) if elapsed > 0 else 0,
        "progress_percentage": (round_num / total_rounds) * 100
    }


def save_metrics_realtime(round_num, metrics):
    global training_start_time
    if training_start_time is None:
        training_start_time = time.time()

    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = []
    else:
        history = []

    training_stats = calculate_training_stats(round_num, NUM_ROUNDS, training_start_time)

    round_data = {
        "round": round_num,
        "accuracy": metrics.get("accuracy", 0.0),
        "val_accuracy": metrics.get("val_accuracy", 0.0),
        "test_accuracy": metrics.get("test_accuracy", 0.0),
        "val_f1": metrics.get("val_f1", 0.0),
        "test_f1": metrics.get("test_f1", 0.0),
        "privacy_epsilon": 0.0,  # No DP
        "privacy_delta": 0.0,    # No DP
        "privacy_risk": "N/A",
        "hospital_a_accuracy": metrics.get("hospital_a_accuracy", 0.0),
        "hospital_b_accuracy": metrics.get("hospital_b_accuracy", 0.0),
        "fairness_score": metrics.get("fairness_score", 1.0),
        "fairness_gap": metrics.get("fairness_gap", 0.0),
        "elapsed_minutes": training_stats["elapsed_minutes"],
        "eta_minutes": training_stats["eta_minutes"],
        "training_speed": training_stats["training_speed"],
        "progress_percentage": training_stats["progress_percentage"],
        "timestamp": datetime.now().isoformat()
    }
    history.append(round_data)

    with open(METRICS_FILE, 'w') as f:
        json.dump(history, f, indent=4)

    print(f"💾 [NO-DP] Metrics for Round {round_num} saved to {METRICS_FILE}")
    print(f"   ⏱️  Elapsed: {training_stats['elapsed_minutes']:.1f}m | ETA: {training_stats['eta_minutes']:.1f}m")


def save_model_checkpoint(parameters, round_num):
    try:
        os.makedirs(MODELS_DIR, exist_ok=True)
        model = get_model()
        model = ModuleValidator.fix(model)
        params_list = fl.common.parameters_to_ndarrays(parameters)
        params_dict = zip(model.state_dict().keys(), params_list)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        model.load_state_dict(state_dict, strict=True)

        version_file = os.path.join(MODELS_DIR, f"model_v{round_num}.pth")
        torch.save({'round': round_num, 'model_state_dict': model.state_dict(),
                     'timestamp': datetime.now().isoformat()}, version_file)
        torch.save(model.state_dict(), MODEL_FILE)
        print(f"✅ [NO-DP] Model v{round_num} saved")
    except Exception as e:
        print(f"⚠️  Failed to save model (Round {round_num}): {e}")


def aggregate_metrics_fn(metrics: List[Tuple[int, Dict]]) -> Dict:
    if not metrics:
        return {}

    total_examples = sum([num for num, _ in metrics])
    weighted_metrics = {
        "val_accuracy": 0.0, "test_accuracy": 0.0,
        "val_f1": 0.0, "test_f1": 0.0,
    }
    client_metrics = []

    for num_examples, m in metrics:
        for key in weighted_metrics:
            weighted_metrics[key] += num_examples * m.get(key, 0.0)
        client_metrics.append({
            "test_accuracy": m.get("test_accuracy", 0.0),
            "val_accuracy": m.get("val_accuracy", 0.0),
            "samples": num_examples
        })

    final_metrics = {k: v / total_examples for k, v in weighted_metrics.items()}

    if len(client_metrics) >= 2:
        accuracies = [c["test_accuracy"] for c in client_metrics]
        fairness_gap = max(accuracies) - min(accuracies)
        final_metrics["hospital_a_accuracy"] = client_metrics[0]["test_accuracy"]
        final_metrics["hospital_b_accuracy"] = client_metrics[1]["test_accuracy"]
        final_metrics["fairness_score"] = 1.0 - fairness_gap
        final_metrics["fairness_gap"] = fairness_gap
    else:
        final_metrics["hospital_a_accuracy"] = 0.0
        final_metrics["hospital_b_accuracy"] = 0.0
        final_metrics["fairness_score"] = 1.0
        final_metrics["fairness_gap"] = 0.0

    print(f"\n{'='*70}")
    print(f"[NO-DP SERVER] Round Evaluation Report:")
    print(f"{'='*70}")
    print(f"   ► Val Accuracy:  {final_metrics['val_accuracy']:.4f}")
    print(f"   ► Test Accuracy: {final_metrics['test_accuracy']:.4f}")
    print(f"   ► Val F1:        {final_metrics['val_f1']:.4f}")
    print(f"   ► Test F1:       {final_metrics['test_f1']:.4f}")
    print(f"   ► Hospital A:    {final_metrics['hospital_a_accuracy']:.4f}")
    print(f"   ► Hospital B:    {final_metrics['hospital_b_accuracy']:.4f}")
    print(f"   ► Fairness Gap:  {final_metrics['fairness_gap']:.4f}")
    print(f"{'='*70}\n")

    return {"accuracy": final_metrics['val_accuracy'], **final_metrics}


class FedProxWithMetrics(fl.server.strategy.FedProx):
    def aggregate_fit(self, server_round, results, failures):
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(
            server_round, results, failures)
        if aggregated_parameters is not None:
            save_model_checkpoint(aggregated_parameters, server_round)
        return aggregated_parameters, aggregated_metrics

    def aggregate_evaluate(self, server_round, results, failures):
        aggregated_loss, aggregated_metrics = super().aggregate_evaluate(
            server_round, results, failures)
        if aggregated_metrics:
            save_metrics_realtime(server_round, aggregated_metrics)
        return aggregated_loss, aggregated_metrics


if __name__ == "__main__":
    if os.path.exists(METRICS_FILE):
        os.remove(METRICS_FILE)
    if os.path.exists(MODEL_FILE):
        os.remove(MODEL_FILE)
    if os.path.exists(MODELS_DIR):
        shutil.rmtree(MODELS_DIR)

    print("\n" + "="*70)
    print("🚀 [RUN 1] NO-DP BASELINE — FedProx WITHOUT Differential Privacy")
    print("="*70)
    print(f"Strategy:     FedProx (μ={PROXIMAL_MU})")
    print(f"DP:           DISABLED")
    print(f"Rounds:       {NUM_ROUNDS}")
    print(f"Local Epochs: 10 per client")
    print(f"Device:       {DEVICE}")
    print(f"Clients:      {NUM_CLIENTS}")
    print("="*70 + "\n")

    strategy = FedProxWithMetrics(
        min_fit_clients=NUM_CLIENTS,
        min_available_clients=NUM_CLIENTS,
        on_fit_config_fn=lambda server_round: {
            "epochs": 10,
            "proximal_mu": PROXIMAL_MU
        },
        evaluate_metrics_aggregation_fn=aggregate_metrics_fn,
        initial_parameters=get_initial_parameters(),
        proximal_mu=PROXIMAL_MU,
    )

    print("✅ Starting No-DP server on 0.0.0.0:8080...")
    print("Waiting for clients...\n")

    history = fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=NUM_ROUNDS),
        strategy=strategy,
    )

    print("\n" + "="*70)
    print("🎉 [RUN 1] NO-DP TRAINING COMPLETE!")
    print(f"📊 Metrics: {METRICS_FILE}")
    print(f"🤖 Model:   {MODEL_FILE}")
    if training_start_time:
        total = (time.time() - training_start_time) / 60
        print(f"⏱️  Time:    {total:.1f} minutes")
    print("="*70 + "\n")
