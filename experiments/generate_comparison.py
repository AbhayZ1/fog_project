"""
Comparison Summary Generator
Reads all experiment results and generates comparison_summary.txt
"""
import json
import os
import sys
from datetime import datetime

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPERIMENTS_DIR = os.path.dirname(__file__)

OUTPUT_FILE = os.path.join(PROJECT_DIR, "comparison_summary.txt")


def load_fl_metrics(filepath):
    """Load FL metrics JSON and extract final round results."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        if not data:
            return None
        return data
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def get_final_round(data):
    """Get the last round's metrics."""
    if not data:
        return {}
    return data[-1]


def main():
    lines = []
    lines.append("=" * 70)
    lines.append("  COMPARISON SUMMARY — Federated Learning Experiments")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)
    lines.append("")

    # Configuration
    lines.append("EXPERIMENT CONFIGURATION")
    lines.append("-" * 40)
    lines.append("Model:          Net (3-block CNN, GroupNorm, Dropout 0.5)")
    lines.append("Dataset:        PneumoniaMNIST (28x28, binary)")
    lines.append("Data Split:     Non-IID (SKEW_RATIO=0.8)")
    lines.append("Rounds:         25")
    lines.append("Local Epochs:   1 per round")
    lines.append("Batch Size:     32")
    lines.append("Learning Rate:  0.001 (Adam)")
    lines.append("Clients:        2 (Hospital A + Hospital B)")
    lines.append("")

    # --- Load all results ---
    experiments = {
        "Original (FedProx + DP)": os.path.join(PROJECT_DIR, "fl_metrics.json"),
        "No-DP (FedProx only)": os.path.join(PROJECT_DIR, "fl_metrics_no_dp.json"),
        "FedAvg (+ DP)": os.path.join(PROJECT_DIR, "fl_metrics_fedavg.json"),
    }

    # Results table header
    lines.append("=" * 70)
    lines.append("  RESULTS COMPARISON")
    lines.append("=" * 70)
    lines.append("")

    header = f"{'Metric':<30} | {'Original':>12} | {'No-DP':>12} | {'FedAvg':>12}"
    lines.append(header)
    lines.append("-" * len(header))

    results = {}
    for name, path in experiments.items():
        data = load_fl_metrics(path)
        if data:
            final = get_final_round(data)
            results[name] = {
                "rounds": len(data),
                "val_accuracy": final.get("val_accuracy", "N/A"),
                "test_accuracy": final.get("test_accuracy", "N/A"),
                "test_f1": final.get("test_f1", "N/A"),
                "val_f1": final.get("val_f1", "N/A"),
                "hospital_a_acc": final.get("hospital_a_accuracy", "N/A"),
                "hospital_b_acc": final.get("hospital_b_accuracy", "N/A"),
                "fairness_gap": final.get("fairness_gap", "N/A"),
                "fairness_score": final.get("fairness_score", "N/A"),
                "epsilon": final.get("privacy_epsilon", "N/A"),
                "elapsed_min": final.get("elapsed_minutes", "N/A"),
            }
        else:
            results[name] = None
            lines.append(f"\n⚠️  {name}: Data NOT FOUND at {path}")

    def fmt(val, decimals=4):
        if val is None or val == "N/A":
            return "N/A"
        if isinstance(val, (int, float)):
            return f"{val:.{decimals}f}"
        return str(val)

    metrics_to_show = [
        ("Rounds Completed", "rounds", 0),
        ("Global Val Accuracy", "val_accuracy", 4),
        ("Global Test Accuracy", "test_accuracy", 4),
        ("Global Val F1", "val_f1", 4),
        ("Global Test F1", "test_f1", 4),
        ("Hospital A Test Acc", "hospital_a_acc", 4),
        ("Hospital B Test Acc", "hospital_b_acc", 4),
        ("Fairness Gap", "fairness_gap", 4),
        ("Fairness Score", "fairness_score", 4),
        ("Privacy ε (epsilon)", "epsilon", 4),
        ("Training Time (min)", "elapsed_min", 1),
    ]

    names = list(experiments.keys())
    for label, key, dec in metrics_to_show:
        vals = []
        for name in names:
            r = results.get(name)
            if r:
                vals.append(fmt(r.get(key, "N/A"), dec))
            else:
                vals.append("N/A")
        line = f"{label:<30} | {vals[0]:>12} | {vals[1]:>12} | {vals[2]:>12}"
        lines.append(line)

    lines.append("")

    # --- Centralized baseline ---
    centralized_path = os.path.join(PROJECT_DIR, "centralized_baseline.json")
    if os.path.exists(centralized_path):
        try:
            with open(centralized_path, 'r') as f:
                centralized = json.load(f)
            lines.append("=" * 70)
            lines.append("  CENTRALIZED BASELINE")
            lines.append("=" * 70)
            lines.append(f"  Epochs Completed:  {centralized.get('epochs_completed', 'N/A')}")
            lines.append(f"  Best Val Accuracy: {fmt(centralized.get('best_val_accuracy'), 4)}")
            lines.append(f"  Final Test Acc:    {fmt(centralized.get('final_test_accuracy'), 4)}")
            lines.append(f"  Final Test F1:     {fmt(centralized.get('final_test_f1'), 4)}")
            lines.append(f"  Training Time:     {fmt(centralized.get('total_time_minutes'), 1)} min")
            lines.append("")
        except Exception as e:
            lines.append(f"\n⚠️  Error reading centralized baseline: {e}")
    else:
        lines.append("\n⚠️  Centralized baseline not found (Run 3 not completed)")

    # --- Analysis ---
    lines.append("=" * 70)
    lines.append("  ANALYSIS")
    lines.append("=" * 70)
    lines.append("")

    orig = results.get("Original (FedProx + DP)")
    no_dp = results.get("No-DP (FedProx only)")
    fedavg = results.get("FedAvg (+ DP)")

    if orig and no_dp:
        orig_acc = orig.get("test_accuracy", 0) if isinstance(orig.get("test_accuracy"), (int, float)) else 0
        nodp_acc = no_dp.get("test_accuracy", 0) if isinstance(no_dp.get("test_accuracy"), (int, float)) else 0
        dp_cost = orig_acc - nodp_acc
        lines.append(f"DP Privacy Cost (accuracy drop): {dp_cost:.4f}")
        if dp_cost < 0:
            lines.append("  → DP actually IMPROVED accuracy (noisy gradients may act as regularization)")
        elif dp_cost < 0.05:
            lines.append("  → Minimal privacy cost (<5 percentage points)")
        else:
            lines.append(f"  → Significant privacy cost ({abs(dp_cost)*100:.1f} percentage points)")
        lines.append("")

    if orig and fedavg:
        orig_acc = orig.get("test_accuracy", 0) if isinstance(orig.get("test_accuracy"), (int, float)) else 0
        fedavg_acc = fedavg.get("test_accuracy", 0) if isinstance(fedavg.get("test_accuracy"), (int, float)) else 0
        prox_benefit = orig_acc - fedavg_acc
        lines.append(f"FedProx Benefit (vs FedAvg): {prox_benefit:.4f}")
        if prox_benefit > 0:
            lines.append("  → FedProx IMPROVED convergence (proximal term helps with non-IID data)")
        elif prox_benefit < -0.02:
            lines.append("  → FedAvg performed BETTER (surprising for non-IID data)")
        else:
            lines.append("  → Similar performance (proximal term effect is minimal)")
        
        # Fairness comparison
        orig_fair = orig.get("fairness_gap", 0) if isinstance(orig.get("fairness_gap"), (int, float)) else 0
        fedavg_fair = fedavg.get("fairness_gap", 0) if isinstance(fedavg.get("fairness_gap"), (int, float)) else 0
        lines.append(f"\nFairness Gap: FedProx={orig_fair:.4f} vs FedAvg={fedavg_fair:.4f}")
        if orig_fair < fedavg_fair:
            lines.append("  → FedProx achieves BETTER fairness between hospitals")
        else:
            lines.append("  → FedAvg achieves BETTER fairness between hospitals")
        lines.append("")

    lines.append("")
    lines.append("=" * 70)
    lines.append("  END OF COMPARISON SUMMARY")
    lines.append("=" * 70)

    # Write output
    output = "\n".join(lines)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(output)

    print(output)
    print(f"\n✅ Summary saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
