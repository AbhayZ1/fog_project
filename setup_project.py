import numpy as np
import medmnist
from medmnist import INFO
from PIL import Image
from tqdm import tqdm
import os
import torch
from torch.utils.data import Subset


# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(os.path.expanduser('~'), '.medmnist') 
DATA_FLAG = "pneumoniamnist"
HOSPITALS = ["Hospital_A", "Hospital_B"]
NUM_CLIENTS = len(HOSPITALS)

# NEW: Heterogeneous split configuration
# Hospital A will have SKEW_RATIO of label 0 (Normal), rest label 1 (Pneumonia)
# Hospital B will have SKEW_RATIO of label 1 (Pneumonia), rest label 0 (Normal)
SKEW_RATIO = 0.8  # 80% of one label, 20% of the other


def save_images(images: np.ndarray, labels: np.ndarray, client_id: str, base_path: str, split_type: str):
    """
    Saves numpy arrays as .png image files into a structured folder 
    for federated distribution.
    Structure: /dataset/{client_id}/{split_type}/{label}/image_id.png
    """
    save_dir = os.path.join(base_path, client_id, split_type)
    
    print(f"\nSaving {len(images)} samples for {client_id} ({split_type})...")
    
    for i in tqdm(range(len(images)), desc=f"Saving {client_id} {split_type}"):
        img_array = images[i].squeeze()
        label = labels[i].item()
        
        final_path = os.path.join(save_dir, str(label))
        os.makedirs(final_path, exist_ok=True)
        
        img = Image.fromarray(img_array.astype(np.uint8), mode='L') 
        img.save(os.path.join(final_path, f'{i:05d}.png'))


def split_data_heterogeneous(images: np.ndarray, labels: np.ndarray, num_clients: int, skew_ratio: float):
    """
    Creates HETEROGENEOUS (non-IID) data split with label skew.
    
    Hospital A: Gets ~80% of Normal (label 0) cases + ~20% of Pneumonia (label 1) cases
    Hospital B: Gets ~80% of Pneumonia (label 1) cases + ~20% of Normal (label 0) cases
    
    This simulates realistic federated scenario where different hospitals 
    have different patient populations and disease prevalence.
    
    Args:
        images: Full dataset images
        labels: Full dataset labels
        num_clients: Number of hospitals (2)
        skew_ratio: Proportion of majority class (0.8 = 80%)
    
    Returns:
        List of (images, labels) tuples for each client
    """
    # Flatten labels for easier indexing
    labels_flat = labels.flatten()
    
    # Separate indices by label
    label_0_indices = np.where(labels_flat == 0)[0]  # Normal cases
    label_1_indices = np.where(labels_flat == 1)[0]  # Pneumonia cases
    
    # Shuffle to randomize within each label
    np.random.shuffle(label_0_indices)
    np.random.shuffle(label_1_indices)
    
    # Calculate split points
    # Hospital A gets 80% of label 0, Hospital B gets 20% of label 0
    label_0_split = int(len(label_0_indices) * skew_ratio)
    # Hospital B gets 80% of label 1, Hospital A gets 20% of label 1
    label_1_split = int(len(label_1_indices) * (1 - skew_ratio))
    
    # Split label 0 (Normal): 80% to Hospital A, 20% to Hospital B
    hospital_a_label_0 = label_0_indices[:label_0_split]
    hospital_b_label_0 = label_0_indices[label_0_split:]
    
    # Split label 1 (Pneumonia): 20% to Hospital A, 80% to Hospital B
    hospital_a_label_1 = label_1_indices[:label_1_split]
    hospital_b_label_1 = label_1_indices[label_1_split:]
    
    # Combine indices for each hospital
    hospital_a_indices = np.concatenate([hospital_a_label_0, hospital_a_label_1])
    hospital_b_indices = np.concatenate([hospital_b_label_0, hospital_b_label_1])
    
    # Shuffle combined indices to mix labels
    np.random.shuffle(hospital_a_indices)
    np.random.shuffle(hospital_b_indices)
    
    # Print distribution statistics
    print(f"\n{'='*60}")
    print(f"HETEROGENEOUS DATA SPLIT - Label Distribution")
    print(f"{'='*60}")
    
    for i, (hospital_name, indices) in enumerate(zip(HOSPITALS, [hospital_a_indices, hospital_b_indices])):
        hospital_labels = labels_flat[indices]
        label_0_count = np.sum(hospital_labels == 0)
        label_1_count = np.sum(hospital_labels == 1)
        total = len(indices)
        
        print(f"\n{hospital_name}:")
        print(f"  Total samples: {total}")
        print(f"  Label 0 (Normal):    {label_0_count:4d} ({label_0_count/total*100:.1f}%)")
        print(f"  Label 1 (Pneumonia): {label_1_count:4d} ({label_1_count/total*100:.1f}%)")
    
    print(f"\n{'='*60}\n")
    
    # Extract images and labels for each hospital
    client_data = []
    for indices in [hospital_a_indices, hospital_b_indices]:
        client_images = images[indices]
        client_labels = labels[indices]
        client_data.append((client_images, client_labels))
    
    return client_data


def main():
    info = INFO[DATA_FLAG]
    DataClass = getattr(medmnist, info['python_class'])
    
    splits = ['train', 'val', 'test']
    
    # Prepare Base Directories
    dataset_base_dir = os.path.join(PROJECT_ROOT, 'dataset')
    os.makedirs(dataset_base_dir, exist_ok=True)
    
    # Set seeds for reproducibility
    np.random.seed(42)
    torch.manual_seed(42)

    for split_type in splits:
        print(f"\n{'='*60}")
        print(f"Processing {split_type.upper()} Split")
        print(f"{'='*60}")
        
        # Load the full dataset
        full_dataset = DataClass(
            root=DATA_ROOT, 
            split=split_type, 
            transform=None,
            download=True
        )
        
        total_samples = len(full_dataset)
        print(f"Total samples in {split_type} split: {total_samples}")
        
        # Get all images and labels
        all_images = full_dataset.imgs
        all_labels = full_dataset.labels
        
        # Create HETEROGENEOUS split (non-IID)
        client_data = split_data_heterogeneous(
            images=all_images,
            labels=all_labels,
            num_clients=NUM_CLIENTS,
            skew_ratio=SKEW_RATIO
        )
        
        # Save data for each hospital
        for i, client_id in enumerate(HOSPITALS):
            client_images, client_labels = client_data[i]
            
            save_images(
                images=client_images, 
                labels=client_labels, 
                client_id=client_id, 
                base_path=dataset_base_dir, 
                split_type=split_type
            )
    
    print("\n" + "="*60)
    print("✅ HETEROGENEOUS DATA SPLIT COMPLETE!")
    print("="*60)
    print("\n📊 Data Distribution Summary:")
    print("   Hospital A: ~80% Normal, ~20% Pneumonia")
    print("   Hospital B: ~20% Normal, ~80% Pneumonia")
    print("\n💡 This simulates realistic federated scenario with")
    print("   heterogeneous patient populations across hospitals.")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
