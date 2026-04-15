"""
Re-run launcher: No-DP and FedAvg experiments with epochs=10.
"""
import subprocess, sys, os, time, json, shutil, signal

PROJECT_DIR = "/home/abhay/Documents/fog_project"
EXPERIMENTS_DIR = os.path.join(PROJECT_DIR, "experiments")

UV_PATH = shutil.which("uv")
if not UV_PATH:
    for p in [os.path.expanduser("~/.local/bin/uv"), os.path.expanduser("~/.cargo/bin/uv")]:
        if os.path.exists(p): UV_PATH = p; break

CMD_PREFIX = [UV_PATH, "run", "--project", PROJECT_DIR, "python"] if UV_PATH else [sys.executable]
print(f"Using: {' '.join(CMD_PREFIX)}")


def run_federated(name, server_script, client_a, client_b, log_file, metrics_file):
    print(f"\n{'='*70}\n  {name}\n  Expected: ~35-50 min\n{'='*70}")

    log_f = open(log_file, "w")
    log_f.write(f"=== {name} ===\nStarted: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    log_f.flush()

    procs = []
    try:
        # Server
        srv = subprocess.Popen(CMD_PREFIX + [os.path.join(EXPERIMENTS_DIR, server_script)],
                               stdout=log_f, stderr=subprocess.STDOUT, cwd=EXPERIMENTS_DIR)
        procs.append(srv)
        print(f"  Server PID: {srv.pid}")
        time.sleep(10)

        if srv.poll() is not None:
            print(f"  ❌ Server exited early: {srv.returncode}")
            log_f.close()
            return False

        # Client A
        ca = subprocess.Popen(CMD_PREFIX + [os.path.join(EXPERIMENTS_DIR, client_a)],
                              stdout=log_f, stderr=subprocess.STDOUT, cwd=EXPERIMENTS_DIR)
        procs.append(ca)
        print(f"  Client A PID: {ca.pid}")
        time.sleep(5)

        # Client B
        cb = subprocess.Popen(CMD_PREFIX + [os.path.join(EXPERIMENTS_DIR, client_b)],
                              stdout=log_f, stderr=subprocess.STDOUT, cwd=EXPERIMENTS_DIR)
        procs.append(cb)
        print(f"  Client B PID: {cb.pid}")

        print(f"  Waiting for completion... (monitor: tail -f {log_file})")

        start = time.time()
        while srv.poll() is None:
            elapsed = time.time() - start
            if elapsed > 10800:  # 3hr timeout
                print(f"  ⚠️ TIMEOUT"); break

            # Progress check every 60s
            mpath = os.path.join(EXPERIMENTS_DIR, metrics_file)
            if int(elapsed) % 60 == 0 and elapsed > 30 and os.path.exists(mpath):
                try:
                    with open(mpath) as f: data = json.load(f)
                    print(f"  📊 {len(data)}/25 rounds ({elapsed/60:.1f}m)")
                except: pass
            time.sleep(5)

        elapsed = time.time() - start
        print(f"  Server done (exit: {srv.returncode}, {elapsed/60:.1f}m)")

        time.sleep(5)
        for p in procs[1:]:
            if p.poll() is None:
                p.terminate()
                try: p.wait(10)
                except: p.kill()

        log_f.write(f"\n=== COMPLETED ===\nDuration: {elapsed/60:.1f} minutes\nServer exit: {srv.returncode}\n")
        log_f.close()
        print(f"  ✅ {name} done in {elapsed/60:.1f}m")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        for p in procs:
            try: p.kill()
            except: pass
        log_f.close()
        return False


# RUN 1: No-DP
ok1 = run_federated(
    "RUN 1: No-DP (epochs=10)", "server_no_dp.py", "client_A_no_dp.py", "client_B_no_dp.py",
    os.path.join(PROJECT_DIR, "logs_no_dp_10epochs.txt"), "fl_metrics_no_dp.json")
time.sleep(10)

# RUN 2: FedAvg
ok2 = run_federated(
    "RUN 2: FedAvg+DP (epochs=10)", "server_fedavg.py", "client_A_fedavg.py", "client_B_fedavg.py",
    os.path.join(PROJECT_DIR, "logs_fedavg_10epochs.txt"), "fl_metrics_fedavg.json")

# Copy results
os.makedirs(os.path.join(PROJECT_DIR, "results"), exist_ok=True)
for src, dst in [
    (os.path.join(EXPERIMENTS_DIR, "fl_metrics_no_dp.json"), "fl_metrics_no_dp_10epochs.json"),
    (os.path.join(EXPERIMENTS_DIR, "fl_metrics_fedavg.json"), "fl_metrics_fedavg_10epochs.json"),
    (os.path.join(PROJECT_DIR, "logs_no_dp_10epochs.txt"), "logs_no_dp_10epochs.txt"),
    (os.path.join(PROJECT_DIR, "logs_fedavg_10epochs.txt"), "logs_fedavg_10epochs.txt"),
]:
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(PROJECT_DIR, "results", dst))
        print(f"  ✅ Copied → results/{dst}")

# Quick comparison
print(f"\n{'='*60}")
print("RE-RUN RESULTS (epochs=10)")
print(f"{'='*60}")
for name, path in [("No-DP", "fl_metrics_no_dp.json"), ("FedAvg+DP", "fl_metrics_fedavg.json")]:
    fpath = os.path.join(EXPERIMENTS_DIR, path)
    if os.path.exists(fpath):
        with open(fpath) as f: data = json.load(f)
        last = data[-1]
        print(f"\n{name} ({len(data)} rounds):")
        for k in ["val_accuracy","test_accuracy","test_f1","hospital_a_accuracy","hospital_b_accuracy",
                   "fairness_gap","privacy_epsilon","elapsed_minutes"]:
            print(f"  {k}: {last.get(k, 'N/A')}")
    else:
        print(f"\n{name}: MISSING")

print(f"\n{'='*60}")
print(f"No-DP: {'SUCCESS' if ok1 else 'FAILED'}")
print(f"FedAvg: {'SUCCESS' if ok2 else 'FAILED'}")
print(f"{'='*60}")
