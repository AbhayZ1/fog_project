import json, os

BASE = "/home/abhay/Documents/fog_project"

def load_json(path):
    try:
        with open(path) as f: return json.load(f)
    except: return None

def load_fl_final(path):
    data = load_json(path)
    if data and isinstance(data, list) and len(data) > 0: return data[-1], len(data)
    return None, 0

orig_final, orig_rounds = load_fl_final(os.path.join(BASE, "results", "fl_metrics_original.json"))
nodp_final, nodp_rounds = load_fl_final(os.path.join(BASE, "results", "fl_metrics_no_dp.json"))
fedavg_final, fedavg_rounds = load_fl_final(os.path.join(BASE, "results", "fl_metrics_fedavg.json"))
centralized = load_json(os.path.join(BASE, "results", "centralized_baseline.json"))

# Fallback: check experiments/ dir
if not nodp_final: nodp_final, nodp_rounds = load_fl_final(os.path.join(BASE, "experiments", "fl_metrics_no_dp.json"))
if not fedavg_final: fedavg_final, fedavg_rounds = load_fl_final(os.path.join(BASE, "experiments", "fl_metrics_fedavg.json"))
if not centralized: centralized = load_json(os.path.join(BASE, "experiments", "centralized_baseline.json"))
if not orig_final: orig_final, orig_rounds = load_fl_final(os.path.join(BASE, "fl_metrics.json"))

with open(os.path.join(BASE, "experiments", "qc_output.txt"), "w") as dbg:
    dbg.write(f"orig: {orig_final is not None} ({orig_rounds})\n")
    dbg.write(f"nodp: {nodp_final is not None} ({nodp_rounds})\n")
    dbg.write(f"fedavg: {fedavg_final is not None} ({fedavg_rounds})\n")
    dbg.write(f"centralized: {centralized is not None}\n")

def g(d, key, default=None):
    if d is None: return default
    return d.get(key, default)

def fmt_pct(v):
    if v is None: return "FAILED"
    if isinstance(v, (int, float)): return f"{v*100:.2f}%"
    return "FAILED"

def fmt_f(v, d=4):
    if v is None: return "FAILED"
    if isinstance(v, (int, float)): return f"{v:.{d}f}"
    return "FAILED"

def fmt_min(v):
    if v is None: return "FAILED"
    if isinstance(v, (int, float)): return f"{v:.1f} min"
    return "FAILED"

cent_val = centralized.get("final_val_accuracy", centralized.get("best_val_accuracy")) if centralized else None
cent_test = centralized.get("final_test_accuracy") if centralized else None
cent_f1 = centralized.get("final_test_f1") if centralized else None
cent_time = centralized.get("total_time_minutes") if centralized else None

lines = []
lines.append("=" * 72)
lines.append("EXPERIMENT COMPARISON — FINAL RESULTS")
lines.append("=" * 72)
lines.append("")
lines.append(f"{'':28s} {'Original':>12s} {'No-DP':>12s} {'FedAvg':>12s} {'Centralized':>12s}")
lines.append(f"{'':28s} {'(FedProx':>12s} {'(FedProx':>12s} {'(FedAvg':>12s} {'(No FL,':>12s}")
lines.append(f"{'':28s} {'+ DP)':>12s} {'no DP)':>12s} {'+ DP)':>12s} {'No DP)':>12s}")
lines.append("-" * 72)

def row(label, v1, v2, v3, v4, fmt):
    return f"{label:<28s} {fmt(v1):>12s} {fmt(v2):>12s} {fmt(v3):>12s} {fmt(v4):>12s}"

lines.append(row("Val Accuracy:", g(orig_final,"val_accuracy"), g(nodp_final,"val_accuracy"), g(fedavg_final,"val_accuracy"), cent_val, fmt_pct))
lines.append(row("Test Accuracy:", g(orig_final,"test_accuracy"), g(nodp_final,"test_accuracy"), g(fedavg_final,"test_accuracy"), cent_test, fmt_pct))
lines.append(row("Test F1:", g(orig_final,"test_f1"), g(nodp_final,"test_f1"), g(fedavg_final,"test_f1"), cent_f1, lambda v: fmt_f(v)))
lines.append(row("Hospital A Acc:", g(orig_final,"hospital_a_accuracy"), g(nodp_final,"hospital_a_accuracy"), g(fedavg_final,"hospital_a_accuracy"), None, lambda v: fmt_pct(v) if v is not None else "N/A"))
lines.append(row("Hospital B Acc:", g(orig_final,"hospital_b_accuracy"), g(nodp_final,"hospital_b_accuracy"), g(fedavg_final,"hospital_b_accuracy"), None, lambda v: fmt_pct(v) if v is not None else "N/A"))
lines.append(row("Fairness Gap:", g(orig_final,"fairness_gap"), g(nodp_final,"fairness_gap"), g(fedavg_final,"fairness_gap"), None, lambda v: fmt_f(v) if v is not None else "N/A"))
lines.append(row("Privacy ε (final):", g(orig_final,"privacy_epsilon"), None, g(fedavg_final,"privacy_epsilon"), None, lambda v: fmt_f(v) if v is not None else "N/A"))
lines.append(row("Training Time:", g(orig_final,"elapsed_minutes"), g(nodp_final,"elapsed_minutes"), g(fedavg_final,"elapsed_minutes"), cent_time, fmt_min))
lines.append("-" * 72)
lines.append("")
lines.append("KEY FINDINGS:")

o_acc = g(orig_final, "test_accuracy")
n_acc = g(nodp_final, "test_accuracy")
f_acc = g(fedavg_final, "test_accuracy")

if o_acc and n_acc:
    dp_cost = (n_acc - o_acc) * 100
    lines.append(f"1. DP Cost: Accuracy drop from No-DP to Original = {dp_cost:+.2f}% {'(DP hurts accuracy)' if dp_cost > 0 else '(DP helps via regularization)'}")
else:
    lines.append("1. DP Cost: Cannot compute")

if o_acc and f_acc:
    prox = (o_acc - f_acc) * 100
    lines.append(f"2. FedProx Benefit: Accuracy gain over FedAvg = {prox:+.2f}% {'(FedProx better)' if prox > 0 else '(FedAvg better)'}")
else:
    lines.append("2. FedProx Benefit: Cannot compute")

if o_acc and cent_test:
    fed_cost = (cent_test - o_acc) * 100
    lines.append(f"3. Federation Cost: Centralized vs Federated = {fed_cost:+.2f}% {'(centralized better)' if fed_cost > 0 else '(federated better)'}")
else:
    lines.append("3. Federation Cost: Cannot compute")

fg_o = g(orig_final, "fairness_gap")
fg_f = g(fedavg_final, "fairness_gap")
if fg_o is not None and fg_f is not None:
    lines.append(f"4. Fairness: FedProx gap ({fg_o:.4f}) vs FedAvg gap ({fg_f:.4f}) — {'FedProx fairer' if fg_o < fg_f else 'FedAvg fairer'}")

lines.append("=" * 72)

output = "\n".join(lines)
os.makedirs(os.path.join(BASE, "results"), exist_ok=True)
with open(os.path.join(BASE, "results", "quick_comparison.txt"), 'w') as f:
    f.write(output)

with open(os.path.join(BASE, "experiments", "qc_output.txt"), "a") as dbg:
    dbg.write("\n" + output + "\n")
