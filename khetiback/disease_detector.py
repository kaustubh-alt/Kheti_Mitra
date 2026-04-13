import os
import tempfile
import urllib.request
from urllib.parse import urlparse

import pandas as pd
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image

# --- 1. Model architecture ---
def ConvBlock(in_channels, out_channels, pool=False):
    layers = [
        nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True),
    ]
    if pool:
        layers.append(nn.MaxPool2d(4))
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
        self.classifier = nn.Sequential(nn.MaxPool2d(4), nn.Flatten(), nn.Linear(512, num_diseases))

    def forward(self, xb):
        out = self.conv1(xb)
        out = self.conv2(out)
        out = self.res1(out) + out
        out = self.conv3(out)
        out = self.conv4(out)
        out = self.res2(out) + out
        return self.classifier(out)


# --- 2. Paths and models ---
BASE_DIR = os.path.dirname(__file__)
DISEASE_INFO_PATH = os.path.join(BASE_DIR, 'disease_info.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'plant-disease-model-complete.pth')

if not os.path.exists(DISEASE_INFO_PATH):
    raise FileNotFoundError(f"{DISEASE_INFO_PATH} not found")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"{MODEL_PATH} not found")

# this CSV must have `disease_name`, `description`, `Possible Steps` columns

disease_info = pd.read_csv(DISEASE_INFO_PATH, encoding='cp1252')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Ensure ResNet9 is allowed when loading a full pickled model in torch 2.6+
if hasattr(torch.serialization, 'add_safe_globals'):
    torch.serialization.add_safe_globals([ResNet9])

# --- 3. Load model ---
# It is assumed the model object was saved with full state (can be loaded directly)
model = torch.load(MODEL_PATH, map_location=device, weights_only=False)
model.eval()


def _download_image_if_url(image_path: str) -> str:
    parsed = urlparse(image_path)
    if parsed.scheme not in ('http', 'https'):
        return image_path

    suffix = os.path.splitext(parsed.path)[1] or '.jpg'
    temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    temp_path = temp_file.name
    temp_file.close()

    urllib.request.urlretrieve(image_path, temp_path)
    return temp_path


def predict_disease(image_path: str):
    img = Image.open(image_path).convert('RGB')
    transform = transforms.Compose([transforms.Resize((256, 256)), transforms.ToTensor()])
    img_tensor = transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(img_tensor)
        prob = torch.nn.functional.softmax(outputs, dim=1)
        conf, idx = torch.max(prob, dim=1)

    return idx.item(), conf.item()


def get_prediction(image_path: str) -> dict:
    """Run disease detection pipeline end-to-end and return structured output.

    Args:
        image_path: Local path or HTTP/HTTPS URL to leaf image file.

    Returns:
        dict with prediction details from disease_info.csv and model output.
    """

    if not image_path or not isinstance(image_path, str):
        raise ValueError('image_path must be a non-empty string')

    path = _download_image_if_url(image_path)

    try:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Image file not found: {path}")

        prediction_idx, confidence = predict_disease(path)

        if prediction_idx < 0 or prediction_idx >= len(disease_info):
            raise IndexError(f"Predicted idx {prediction_idx} out of range")

        row = disease_info.iloc[prediction_idx]
        return {
            'prediction_idx': int(prediction_idx),
            'confidence': float(confidence),
            'disease_name': row.get('disease_name', ''),
            'description': row.get('description', ''),
            'prevention': row.get('Possible Steps', ''),
        }
    finally:
        # cleanup downloaded temp file
        parsed = urlparse(image_path)
        if parsed.scheme in ('http', 'https') and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


if __name__ == '__main__':
    # import argparse

    # parser = argparse.ArgumentParser(description='Disease detector complete inference wrapper')
    # parser.add_argument('image_path', help='Local image path or HTTPS URL')
    # args = parser.parse_args()

    result = get_prediction(r"C:\Users\kaust\Downloads\istockphoto-1286441510-612x612.jpg")
    print(result)
