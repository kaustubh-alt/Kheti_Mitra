import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import os
import sys
import __main__  # Needed to fix the __main__ attribute error

# --- 1. Model Architecture ---
def ConvBlock(in_channels, out_channels, pool=False):
    layers = [
        nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
        nn.BatchNorm2d(out_channels), 
        nn.ReLU(inplace=True)
    ]
    if pool: layers.append(nn.MaxPool2d(4))
    return nn.Sequential(*layers)

class ResNet9(nn.Module):
    def __init__(self, in_channels, num_diseases):
        super().__init__()
        self.conv1 = ConvBlock(in_channels, 64)
        self.conv2 = ConvBlock(64, 128, pool=True)
        self.res1 = nn.Sequential(ConvBlock(128, 128), ConvBlock(128, 128))
        self.conv3 = ConvBlock(128, 256, pool=True)
        self.conv4 = ConvBlock(256, 512, pool=True)
        self.res2 = nn.Sequential(ConvBlock(512, 512), ConvBlock(512, 512))
        self.classifier = nn.Sequential(
            nn.MaxPool2d(4), 
            nn.Flatten(), 
            nn.Linear(512, num_diseases)
        )

    def forward(self, xb):
        out = self.conv1(xb)
        out = self.conv2(out)
        out = self.res1(out) + out
        out = self.conv3(out)
        out = self.conv4(out)
        out = self.res2(out) + out
        return self.classifier(out)

# --- 2. THE FIXES ---

# FIX A: Allowlist ResNet9 for PyTorch 2.6+ security
if hasattr(torch.serialization, 'add_safe_globals'):
    torch.serialization.add_safe_globals([ResNet9])

# FIX B: Force ResNet9 into the global namespace. 
# This stops the "Can't get attribute 'ResNet9' on <module '__main__'>" error.
setattr(__main__, "ResNet9", ResNet9)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = 'plant-disease-model-complete.pth'

# --- 3. Loading with Trust ---
def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    
    # FIX C: Explicitly set weights_only=False because your file contains the full model object.
    # Since you created this model, it is safe to trust.
    model = torch.load(MODEL_PATH, map_location=device, weights_only=False)
    model.eval()
    return model

# Global model instance
model = load_model()

# --- 4. Prediction Function ---
def predict_disease(image_path):
    img = Image.open(image_path).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((256, 256)), 
        transforms.ToTensor()
    ])
    img_tensor = transform(img).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(img_tensor)
        prob = torch.nn.functional.softmax(outputs, dim=1)
        conf, idx = torch.max(prob, dim=1)
        
    return idx.item(), conf.item()