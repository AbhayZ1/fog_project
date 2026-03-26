"""
Grad-CAM Heatmap Generator for Explainable AI
Visualizes which parts of the X-ray the model focuses on
"""

import torch
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget


def generate_gradcam_heatmap(model, image_tensor, target_class=None):
    """
    Generate Grad-CAM heatmap for the given image.
    
    Args:
        model: Trained PyTorch model
        image_tensor: Preprocessed image tensor (1, 1, 28, 28)
        target_class: Target class index (0=Normal, 1=Pneumonia), None for predicted class
    
    Returns:
        dict with overlay, heatmap, prediction, confidence
    """
    
    model.eval()
    
    # Get prediction
    with torch.no_grad():
        output = model(image_tensor)
        probabilities = F.softmax(output, dim=1)
        confidence, predicted = torch.max(probabilities, 1)
        predicted_class = predicted.item()
        confidence_score = confidence.item()
    
    # Use predicted class if target not specified
    if target_class is None:
        target_class = predicted_class
    
    # Target the last convolutional layer (conv3)
    # This is where the model has learned high-level features
    target_layers = [model.conv3]
    
    # Initialize Grad-CAM
    cam = GradCAM(model=model, target_layers=target_layers)
    
    # Specify target class
    targets = [ClassifierOutputTarget(target_class)]
    
    # Generate CAM
    grayscale_cam = cam(input_tensor=image_tensor, targets=targets)
    
    # Extract the heatmap for the first image in batch
    grayscale_cam = grayscale_cam[0, :]  # Shape: (28, 28)
    
    # Convert input image to numpy for visualization
    # Remove batch and channel dimensions: (1, 1, 28, 28) -> (28, 28)
    img_np = image_tensor.squeeze().cpu().numpy()
    
    # Normalize to [0, 1] for visualization
    img_np = (img_np - img_np.min()) / (img_np.max() - img_np.min() + 1e-8)
    
    # Resize to higher resolution for better visualization
    target_size = (224, 224)
    img_resized = cv2.resize(img_np, target_size)
    heatmap_resized = cv2.resize(grayscale_cam, target_size)
    
    # Convert grayscale image to RGB
    img_rgb = np.stack([img_resized] * 3, axis=-1)
    
    # Overlay heatmap on image
    cam_image = show_cam_on_image(img_rgb, heatmap_resized, use_rgb=True)
    
    # Create heatmap-only image (colorized)
    heatmap_colored = cv2.applyColorMap(
        np.uint8(255 * heatmap_resized), 
        cv2.COLORMAP_JET
    )
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
    
    # Convert to PIL Images
    overlay_pil = Image.fromarray(cam_image)
    heatmap_pil = Image.fromarray(heatmap_colored)
    
    return {
        "overlay": overlay_pil,
        "heatmap": heatmap_pil,
        "prediction": predicted_class,
        "confidence": confidence_score,
        "target_class": target_class
    }


def save_heatmap(heatmap_data, output_path="static/heatmap_latest.png"):
    """Save the heatmap overlay to disk."""
    heatmap_data["overlay"].save(output_path)
    return output_path
