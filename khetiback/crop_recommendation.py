from flask import Flask, render_template, request, send_file, jsonify
import joblib
import numpy as np
import re
from functools import wraps
from io import BytesIO
import datetime

model = joblib.load('model/rf_model.pkl')
label_encoder = joblib.load('model/label_encoder.pkl') 

def sanitize_numeric_input(value, min_val=None, max_val=None, field_name=""):
    """Sanitize and validate numeric input"""
    try:
        # Remove any non-numeric characters except decimal point and minus
        cleaned = re.sub(r'[^0-9.-]', '', str(value))
        num_value = float(cleaned)
        
        if min_val is not None and num_value < min_val:
            raise ValueError(f"{field_name} must be at least {min_val}")
        if max_val is not None and num_value > max_val:
            raise ValueError(f"{field_name} must be at most {max_val}")
            
        return num_value
    except ValueError as e:
        raise ValueError(f"Invalid {field_name}: {str(e)}")

def predict(n, p, k, temperature, humidity, ph, rainfall):
    try:
        # Sanitize and validate all numeric inputs
        data = [
            n,
            p,
            k,
            temperature,
            humidity,
            ph,     
            rainfall
        ]
        
        
        prediction_num = model.predict([data])
        print(prediction_num)
        prediction_label = [label_encoder.inverse_transform([num])[0] for num in prediction_num]

        return prediction_label

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Prediction failed'}), 500
    

prediction = predict(460,19,516,20.87,82.0,6.5,202.0)
print(prediction)