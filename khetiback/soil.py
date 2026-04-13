import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
import keras
import random # Added for the random range feature

# --- FIX FOR THE DEPTHWISECONV2D ERROR ---
def fix_depthwise_conv2d(**kwargs):
    if 'groups' in kwargs:
        kwargs.pop('groups')
    return keras.layers.DepthwiseConv2D(**kwargs)

model_path = "model/SoilNet_93_86.h5"
SoilNet = load_model(model_path, custom_objects={'DepthwiseConv2D': fix_depthwise_conv2d})

class_map = {0: "alluvial", 1: "black", 2: "clay", 3: "red"}

display_names = {
    "alluvial": ['Rice', 'Wheat', 'Sugarcane', 'Maize', 'Cotton', 'Soyabean', 'Jute'],
    "black": ['Virginia', 'Wheat', 'Jowar', 'Millets', 'Linseed', 'Castor', 'Sunflower'],
    "clay": ['Rice', 'Lettuce', 'Chard', 'Broccoli', 'Cabbage', 'Snap Beans'],
    "red": ['Cotton', 'Wheat', 'Pulses', 'Millets', 'OilSeeds', 'Potatoes']
}

# Data dictionary with ranges
data = {
    "alluvial": {
        "nitrogen_kg_ha": [220, 480],
        "phosphorus_kg_ha": [11, 25],
        "potassium_kg_ha": [280, 500],
        "ph_range": [6.5, 8.4],
        "organic_matter_percent": [0.4, 0.8]
    },
    "black": {
        "nitrogen_kg_ha": [180, 350],
        "phosphorus_kg_ha": [8, 18],
        "potassium_kg_ha": [300, 650],
        "ph_range": [7.2, 8.5],
        "organic_matter_percent": [0.5, 1.2]
    },
    "clay": {
        "nitrogen_kg_ha": [240, 420],
        "phosphorus_kg_ha": [20, 50],
        "potassium_kg_ha": [350, 750],
        "ph_range": [6.0, 7.8],
        "organic_matter_percent": [1.5, 3.5]
    },
    "red": {
        "nitrogen_kg_ha": [120, 250],
        "phosphorus_kg_ha": [5, 15],
        "potassium_kg_ha": [150, 300],
        "ph_range": [5.0, 7.3],
        "organic_matter_percent": [0.2, 0.6]
    }
}

def model_predict(image_path):
    # 1. Preprocessing
    image = load_img(image_path, target_size=(224, 224))
    image = img_to_array(image)
    image = image / 255.0
    image = np.expand_dims(image, axis=0)
    
    # 2. Prediction
    preds = SoilNet.predict(image)
    result_idx = np.argmax(preds)
    soil_key = class_map[result_idx]
    
    # 3. Randomize Properties within Range
    base_props = data[soil_key]
    
    # Generate random values based on the defined ranges
    randomized_report = {
        "soil_type": soil_key.capitalize(),
        "nitrogen": round(random.uniform(base_props["nitrogen_kg_ha"][0], base_props["nitrogen_kg_ha"][1]), 2),
        "phosphorus": round(random.uniform(base_props["phosphorus_kg_ha"][0], base_props["phosphorus_kg_ha"][1]), 2),
        "potassium": round(random.uniform(base_props["potassium_kg_ha"][0], base_props["potassium_kg_ha"][1]), 2),
        "ph": round(random.uniform(base_props["ph_range"][0], base_props["ph_range"][1]), 1),
        "organic_matter": round(random.uniform(base_props["organic_matter_percent"][0], base_props["organic_matter_percent"][1]), 2),
        "eligible_crops": display_names[soil_key]
    }
    
    return randomized_report

# # Test the function
# try:
#     report = model_predict("11.jpg")
#     print("--- Soil Analysis Report ---")
#     for key, value in report.items():
#         print(f"{key.replace('_', ' ').title()}: {value}")
# except Exception as e:
#     print(f"Error: {e}")