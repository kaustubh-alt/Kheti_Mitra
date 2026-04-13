from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import google.generativeai as genai
from diseases import predict_disease
from soil import model_predict
from crop_recommendation import predict
app = FastAPI(title="Kheti Mitra API")

# Enable CORS - allow all origins (development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Load data with error handling

disease_info = pd.read_csv('disease_info.csv', encoding='cp1252')




@app.post("/plant")
async def get_prediction(request: Request):
    """
    Accepts JSON body: { "image_url": "<url_or_path>" }
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    image_url = "C:\\Users\\kaust\\Downloads\\" + data.get("image_url")
    if not image_url:
        raise HTTPException(status_code=400, detail="Missing 'image_url' in request body")

    try:
        prediction_idx, score = predict_disease(image_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # 2. Extract info from CSV
    row = disease_info.iloc[prediction_idx]
    title = row['disease_name']
    description = row['description']
    prevent = row['Possible Steps']

    # Generate actual content
    response = "genai_model.generate_content(prompt)"
        
    return {
            "status": "success",
            "prediction": {
                "title": title,
                "confidence": f"{score*100:.2f}%"
            },
            "ai_analysis": response,
            "raw_details": {
                "description": description, 
                "prevention": prevent
            }
        }


@app.post("/soil/")
async def getsoil(request: Request):
    """
    Accepts JSON body: { "image_url": "<url_or_path>" }
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    image_url = "C:\\Users\\kaust\\Downloads\\" + data.get("image_url")
    if not image_url:
        raise HTTPException(status_code=400, detail="Missing 'image_url' in request body")

    return model_predict(image_url)


@app.post("/crop")
async def getcrop(request: Request):
    data = await request.json()
    n,p,k = data.get("N"),data.get("P"),data.get("K")
    temperature = data.get("temperature")
    humidity = data.get("humidity")
    ph = data.get("ph")
    rainfall = data.get("rainfall")
    return predict(n,p,k,temperature,humidity,ph,rainfall)

    