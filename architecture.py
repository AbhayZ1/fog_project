import torch
import torch.nn as nn
import torch.nn.functional as F

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        
        # --- BLOCK 1: Low-level Features (Edges) ---
        self.conv1 = nn.Conv2d(1, 32, 3, padding=1) 
        self.bn1 = nn.BatchNorm2d(32)
        
        # --- BLOCK 2: Mid-level Features (Shapes) ---
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        
        # --- BLOCK 3: High-level Features (Pathology) ---
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        
        self.pool = nn.MaxPool2d(2, 2)
        
        # Dropout: 0.5 is aggressive to kill overfitting
        self.dropout = nn.Dropout(0.5)
        
        # Output calculation: 
        # Input: 28x28
        # Pool 1 -> 14x14
        # Pool 2 -> 7x7
        # Pool 3 -> 3x3 (integer division)
        # Flattened size: 128 channels * 3 * 3 = 1152
        self.fc1 = nn.Linear(128 * 3 * 3, 256) 
        self.fc2 = nn.Linear(256, 2) 

    def forward(self, x):
        # Block 1
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.pool(x)
        
        
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.pool(x)
        
        
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)
        x = self.pool(x)
        
       
        x = x.view(-1, 128 * 3 * 3) 
        
        x = F.relu(self.fc1(x))
        x = self.dropout(x) 
        x = self.fc2(x)
        return x

def get_model():
    return Net()