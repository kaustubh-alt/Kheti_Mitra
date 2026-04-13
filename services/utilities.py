
import pandas as pd
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry



def get_weather_json(lat, lon):
    # 1. Setup API Client
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "weather_code", "temperature_2m_max", "temperature_2m_min", 
            "rain_sum", "precipitation_probability_max", "uv_index_max"
        ],
        "current": [
            "temperature_2m", "relative_humidity_2m", "precipitation", 
            "is_day", "apparent_temperature"
        ],
        "timezone": "auto", # 'auto' is safer for general coordinates
        "forecast_days": 16,
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        res = responses[0]

        # 2. Extract Current Data
        current = res.Current()
        current_data = {
            "time": current.Time(),
            "temp": round(current.Variables(0).Value(), 1),
            "humidity": current.Variables(1).Value(),
            "precipitation": current.Variables(2).Value(),
            "is_day": bool(current.Variables(3).Value()),
            "feels_like": round(current.Variables(4).Value(), 1)
        }

        # 3. Extract Daily Data
        daily = res.Daily()
        # Create a date range for the forecast
        dates = pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        )

        daily_forecast = []
        # Index-based extraction to match your requested order
        codes = daily.Variables(0).ValuesAsNumpy()
        t_max = daily.Variables(1).ValuesAsNumpy()
        t_min = daily.Variables(2).ValuesAsNumpy()
        rain = daily.Variables(3).ValuesAsNumpy()
        prob = daily.Variables(4).ValuesAsNumpy()

        for i in range(len(dates)):
            daily_forecast.append({
                "date": dates[i].strftime('%Y-%m-%d'),
                "weather_code": int(codes[i]),
                "temp_max": float(t_max[i]),
                "temp_min": float(t_min[i]),
                "rain_sum_mm": float(rain[i]),
                "precip_prob": float(prob[i])
            })

        # 4. Final JSON Structure
        return {
            "metadata": {
                "lat": res.Latitude(),
                "lon": res.Longitude(),
                "elevation": res.Elevation(),
                "timezone": res.Timezone()
            },
            "current": current_data,
            "daily": daily_forecast
        }

    except Exception as e:
        return {"error": str(e)}

    
import google.generativeai as genai
import os

# 1. Setup Configuration
API_KEY = "YOUR_GEMINI_API_KEY"
genai.configure(api_key=API_KEY)

# 2. Parameter Tuning
# Temperature: High (1.0+) for creativity, Low (0.1) for precision/coding
# top_p: Nucleus sampling; 0.95 is standard
# max_output_tokens: Limits response length
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# 3. Initialize Model with System Prompt
# The system_instruction defines the 'Role' of the AI
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="You are an expert report generator." \
    " Provide detailed and accurate information." \
    " you are given a details about plant issue and you have to generate a report on it."
)

def get_ai_response(user_input):
    try:
        # 4. Generate Content (Non-streaming)
        # By default, this waits for the full response before returning
        response = model.generate_content(user_input)
        
        # Access the text from the response object
        return response.text
    
    except Exception as e:
        return f"An error occurred: {str(e)}"

