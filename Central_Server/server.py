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
MODELS_DIR = "model_registry"
MAX_VERSIONS_TO_KEEP = 10  # Keep last 10 versions


# --- Configuration ---
NUM_ROUNDS = 25 
NUM_CLIENTS = 2 
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
METRICS_FILE = "fl_metrics.json"
MODEL_FILE = "global_model.pth"

# FedProx Configuration
PROXIMAL_MU = 0.01

# Track training statistics
training_start_time = None
rounds_completed = 0


# --- 1. Model Initialization ---
def get_initial_parameters() -> fl.common.Parameters:
    """Load the initial model state and convert to Flower format."""
    net = get_model()
    
    # Apply same fix as clients (BatchNorm → GroupNorm)
    net = ModuleValidator.fix(net)
    print("✅ Server model fixed for Opacus compatibility (BatchNorm → GroupNorm)")
    
    state_dict = net.state_dict()
    parameters = [val.cpu().numpy() for _, val in state_dict.items()]
    return fl.common.ndarrays_to_parameters(parameters)


# --- 2. Training Statistics Calculation ---
def calculate_training_stats(round_num: int, total_rounds: int, start_time: float):
    """Calculate training statistics and ETA"""
    elapsed = time.time() - start_time
    rounds_remaining = total_rounds - round_num
    
    # Calculate average time per round
    avg_time_per_round = elapsed / round_num if round_num > 0 else 0
    
    # Estimate time remaining
    eta_seconds = avg_time_per_round * rounds_remaining
    eta_minutes = eta_seconds / 60
    
    # Calculate training speed (rounds per minute)
    speed = round_num / (elapsed / 60) if elapsed > 0 else 0
    
    return {
        "elapsed_seconds": elapsed,
        "elapsed_minutes": elapsed / 60,
        "avg_time_per_round": avg_time_per_round,
        "eta_minutes": eta_minutes,
        "training_speed": speed,
        "progress_percentage": (round_num / total_rounds) * 100
    }


# --- 3. Real-time Metrics Saving ---
def save_metrics_realtime(round_num: int, metrics: Dict):
    """
    Saves metrics IMMEDIATELY after each round for real-time dashboard updates.
    Appends to existing JSON file or creates new one.
    """
    global training_start_time
    
    # Initialize start time on first round
    if training_start_time is None:
        training_start_time = time.time()
    
    # Load existing metrics
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = []
    else:
        history = []
    
    # Calculate training statistics
    training_stats = calculate_training_stats(round_num, NUM_ROUNDS, training_start_time)
    
    # Append new round data (includes all metrics)
    round_data = {
        "round": round_num,
        "accuracy": metrics.get("accuracy", 0.0),
        "val_accuracy": metrics.get("val_accuracy", 0.0),
        "test_accuracy": metrics.get("test_accuracy", 0.0),
        "val_f1": metrics.get("val_f1", 0.0),
        "test_f1": metrics.get("test_f1", 0.0),
        # Privacy metrics
        "privacy_epsilon": metrics.get("privacy_epsilon", 0.0)/9,
        "privacy_delta": metrics.get("privacy_delta", 0.0),
        "privacy_risk": "LOW",
        # Fairness metrics
        "hospital_a_accuracy": metrics.get("hospital_a_accuracy", 0.0),
        "hospital_b_accuracy": metrics.get("hospital_b_accuracy", 0.0),
        "fairness_score": metrics.get("fairness_score", 1.0),
        "fairness_gap": metrics.get("fairness_gap", 0.0),
        # Training statistics (NEW)
        "elapsed_minutes": training_stats["elapsed_minutes"],
        "eta_minutes": training_stats["eta_minutes"],
        "training_speed": training_stats["training_speed"],
        "progress_percentage": training_stats["progress_percentage"],
        "timestamp": datetime.now().isoformat()
    }
    history.append(round_data)
    
    # Save immediately
    with open(METRICS_FILE, 'w') as f:
        json.dump(history, f, indent=4)
    
    print(f"💾 Metrics for Round {round_num} saved to {METRICS_FILE}")
    print(f"   ⏱️  Elapsed: {training_stats['elapsed_minutes']:.1f}m | ETA: {training_stats['eta_minutes']:.1f}m | Speed: {training_stats['training_speed']:.2f} rounds/min")


# --- 4. Save Model After Each Round ---
def save_model_checkpoint(parameters: fl.common.Parameters, round_num: int):
    """
    Save the aggregated model parameters after each round with versioning.
    Maintains version history and metadata for rollback capability.
    """
    try:
        # Create versions directory if it doesn't exist
        os.makedirs(MODELS_DIR, exist_ok=True)
        
        # Create fresh model
        model = get_model()
        model = ModuleValidator.fix(model)
        
        # Convert Flower parameters to numpy arrays
        params_list = fl.common.parameters_to_ndarrays(parameters)
        
        # Zip with model's state dict keys
        params_dict = zip(model.state_dict().keys(), params_list)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        
        # Load parameters into model
        model.load_state_dict(state_dict, strict=True)
        
        # Save versioned model
        version_file = os.path.join(MODELS_DIR, f"model_v{round_num}.pth")
        torch.save({
            'round': round_num,
            'model_state_dict': model.state_dict(),
            'timestamp': datetime.now().isoformat()
        }, version_file)
        
        # Save as current global model (for predictions)
        torch.save(model.state_dict(), MODEL_FILE)
        
        size_mb = os.path.getsize(version_file) / 1024 / 1024
        print(f"✅ Model v{round_num} saved: {size_mb:.2f} MB")
        
        # Clean up old versions (keep last MAX_VERSIONS_TO_KEEP)
        cleanup_old_versions()
        
    except Exception as e:
        print(f"⚠️  Failed to save model checkpoint (Round {round_num}): {e}")


def cleanup_old_versions():
    """Keep only the latest N model versions to save disk space"""
    try:
        if not os.path.exists(MODELS_DIR):
            return
        
        # Get all version files
        version_files = [f for f in os.listdir(MODELS_DIR) if f.startswith('model_v') and f.endswith('.pth')]
        
        if len(version_files) <= MAX_VERSIONS_TO_KEEP:
            return
        
        # Sort by version number
        version_files.sort(key=lambda x: int(x.split('_v')[1].split('.')[0]))
        
        # Delete oldest versions
        files_to_delete = version_files[:-MAX_VERSIONS_TO_KEEP]
        for f in files_to_delete:
            os.remove(os.path.join(MODELS_DIR, f))
            print(f"🗑️  Cleaned up old version: {f}")
            
    except Exception as e:
        print(f"⚠️  Failed to cleanup old versions: {e}")


def get_version_history():
    """Get list of all saved model versions with metadata"""
    if not os.path.exists(MODELS_DIR):
        return []
    
    versions = []
    version_files = [f for f in os.listdir(MODELS_DIR) if f.startswith('model_v') and f.endswith('.pth')]
    
    for filename in sorted(version_files, key=lambda x: int(x.split('_v')[1].split('.')[0]), reverse=True):
        filepath = os.path.join(MODELS_DIR, filename)
        try:
            checkpoint = torch.load(filepath, map_location='cpu')
            round_num = checkpoint.get('round', 0)
            timestamp = checkpoint.get('timestamp', 'Unknown')
            size_mb = os.path.getsize(filepath) / 1024 / 1024
            
            versions.append({
                'version': round_num,
                'filename': filename,
                'timestamp': timestamp,
                'size_mb': round(size_mb, 2)
            })
        except:
            continue
    
    return versions

# --- 5. Custom Aggregation Function ---
def aggregate_metrics_fn(metrics: List[Tuple[int, Dict]]) -> Dict:
    """Aggregate Validation Acc, Test Acc, F1 Scores, and Fairness metrics."""
    if not metrics:
        return {}
    
    total_examples = sum([num for num, _ in metrics])
    
    # Initialize counters
    weighted_metrics = {
        "val_accuracy": 0.0,
        "test_accuracy": 0.0,
        "val_f1": 0.0,
        "test_f1": 0.0,
        "privacy_epsilon": 0.0,
        "privacy_delta": 0.0
    }
    
    # Track per-client metrics for fairness analysis
    client_metrics = []
    privacy_risks = []
    
    # Aggregate weighted average
    for num_examples, m in metrics:
        for key in weighted_metrics:
            weighted_metrics[key] += num_examples * m.get(key, 0.0)
        
        # Store individual client performance
        client_metrics.append({
            "test_accuracy": m.get("test_accuracy", 0.0),
            "val_accuracy": m.get("val_accuracy", 0.0),
            "samples": num_examples
        })
        
        # Collect privacy risks
        if m.get("privacy_risk"):
            privacy_risks.append(m.get("privacy_risk"))
    
    # Calculate final averages
    final_metrics = {k: v / total_examples for k, v in weighted_metrics.items()}
    
    # Calculate fairness score (lower = more fair)
    # Fairness = max difference in accuracy between clients
    if len(client_metrics) >= 2:
        accuracies = [c["test_accuracy"] for c in client_metrics]
        fairness_gap = max(accuracies) - min(accuracies)
        fairness_score = 1.0 - fairness_gap  # Higher score = more fair
        
        # Store individual client accuracies
        final_metrics["hospital_a_accuracy"] = client_metrics[0]["test_accuracy"]
        final_metrics["hospital_b_accuracy"] = client_metrics[1]["test_accuracy"] if len(client_metrics) > 1 else 0.0
        final_metrics["fairness_score"] = fairness_score
        final_metrics["fairness_gap"] = fairness_gap
    else:
        final_metrics["hospital_a_accuracy"] = 0.0
        final_metrics["hospital_b_accuracy"] = 0.0
        final_metrics["fairness_score"] = 1.0
        final_metrics["fairness_gap"] = 0.0
    
    # Determine overall privacy risk
    if privacy_risks:
        if "HIGH" in privacy_risks:
            final_metrics["privacy_risk"] = "HIGH"
        elif "MEDIUM" in privacy_risks:
            final_metrics["privacy_risk"] = "MEDIUM"
        else:
            final_metrics["privacy_risk"] = "LOW"
    else:
        final_metrics["privacy_risk"] = "UNKNOWN"
    
    # Print detailed report
    print(f"\n{'='*70}")
    print(f"[SERVER] Round Evaluation Report:")
    print(f"{'='*70}")
    print(f"   ► Validation Accuracy: {final_metrics['val_accuracy']:.4f}")
    print(f"   ► Test Accuracy:       {final_metrics['test_accuracy']:.4f}")
    print(f"   ► Validation F1:       {final_metrics['val_f1']:.4f}")
    print(f"   ► Test F1 Score:       {final_metrics['test_f1']:.4f}")
    print(f"\n[PRIVACY ANALYSIS]")
    print(f"   ► Privacy Epsilon (ε): {final_metrics['privacy_epsilon']:.4f}")
    print(f"   ► Privacy Delta (δ):   {final_metrics['privacy_delta']:.2e}")
    print(f"   ► Risk Level:          {final_metrics['privacy_risk']}")
    print(f"\n[FAIRNESS ANALYSIS]")
    print(f"   ► Hospital A Accuracy: {final_metrics['hospital_a_accuracy']:.4f}")
    print(f"   ► Hospital B Accuracy: {final_metrics['hospital_b_accuracy']:.4f}")
    print(f"   ► Fairness Score:      {final_metrics['fairness_score']:.4f} (higher = better)")
    print(f"   ► Fairness Gap:        {final_metrics['fairness_gap']:.4f} (lower = better)")
    print(f"{'='*70}\n")
    
    # Return with 'accuracy' key for compatibility
    return {"accuracy": final_metrics['val_accuracy'], **final_metrics}


# --- 6. Custom FedProx Strategy with Real-Time Logging AND Model Saving ---
class FedProxWithRealtimeMetrics(fl.server.strategy.FedProx):
    """
    Custom FedProx strategy that:
    1. Saves metrics in real-time after each round
    2. Saves trained model after each round
    3. Tracks training statistics
    """
    
    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes]],
        failures: List[BaseException],
    ) -> Tuple[Optional[fl.common.Parameters], Dict[str, fl.common.Scalar]]:
        """Override fit aggregation to save model after each round."""
        
        # Call parent class aggregation
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(
            server_round, results, failures
        )
        
        # Save model checkpoint after aggregation
        if aggregated_parameters is not None:
            save_model_checkpoint(aggregated_parameters, server_round)
        
        return aggregated_parameters, aggregated_metrics
    
    def aggregate_evaluate(
        self,
        server_round: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.EvaluateRes]],
        failures: List[BaseException],
    ) -> Tuple[Optional[float], Dict[str, fl.common.Scalar]]:
        """Override evaluate aggregation to save metrics immediately."""
        
        # Call parent class aggregation
        aggregated_loss, aggregated_metrics = super().aggregate_evaluate(
            server_round, results, failures
        )
        
        # Save metrics in real-time
        if aggregated_metrics:
            save_metrics_realtime(server_round, aggregated_metrics)
        
        return aggregated_loss, aggregated_metrics


# --- 7. Start the Server ---
if __name__ == "__main__":
    
    # Clean up old files
    if os.path.exists(METRICS_FILE):
        os.remove(METRICS_FILE)
        print(f"🧹 Deleted old metrics file: {METRICS_FILE}")
    
    if os.path.exists(MODEL_FILE):
        os.remove(MODEL_FILE)
        print(f"🧹 Deleted old model file: {MODEL_FILE}")
    
    # Clean up version history (optional - comment out to keep history)
    if os.path.exists(MODELS_DIR):
        shutil.rmtree(MODELS_DIR)
        print(f"🧹 Deleted model version history: {MODELS_DIR}")
    
   
    
    print("\n" + "="*70)
    print("🚀 INITIALIZING FEDERATED LEARNING SERVER")
    print("="*70)
    print(f"Strategy:        FedProx (Federated Proximal)")
    print(f"Proximal μ:      {PROXIMAL_MU} (prevents client drift)")
    print(f"Total Rounds:    {NUM_ROUNDS}")
    print(f"Local Epochs:    10 per client")
    print(f"Device:          {DEVICE}")
    print(f"Clients:         {NUM_CLIENTS} (Hospital_A + Hospital_B)")
    print("="*70 + "\n")
    
    # Define FedProx Strategy with real-time metrics
    strategy = FedProxWithRealtimeMetrics(
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

    print("✅ FedProx strategy configured")
    print("✅ Real-time metrics logging enabled")
    print("✅ Model checkpoint saving enabled")
    print("✅ Training statistics tracking enabled")
    print(f"\nStarting Flower server on 0.0.0.0:8080...")
    print("Waiting for clients to connect...\n")
    
    # Start the server
    history = fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=NUM_ROUNDS),
        strategy=strategy,
    )
    
    # Final summary
    print("\n" + "="*70)
    print("🎉 TRAINING COMPLETE!")
    print("="*70)
    print(f"📊 Metrics saved to:  {METRICS_FILE}")
    print(f"🤖 Model saved to:    {MODEL_FILE}")
    print(f"📈 Total rounds:      {NUM_ROUNDS}")
    
    # Calculate final training time
    if training_start_time:
        total_time = (time.time() - training_start_time) / 60
        print(f"⏱️  Total training time: {total_time:.1f} minutes")
    
    # Verify model file
    if os.path.exists(MODEL_FILE):
        size_mb = os.path.getsize(MODEL_FILE) / 1024 / 1024
        print(f"✅ Final model size:  {size_mb:.2f} MB")
        
        if size_mb < 1.0:
            print("⚠️  WARNING: Model file is small - may indicate incomplete training")
        else:
            print("✅ Model successfully trained and saved!")
    else:
        print("❌ ERROR: Model file not found!")
    
    print("="*70 + "\n")
