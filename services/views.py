from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import logging
import requests
from django.conf import settings
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
import uuid
import os
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.models import User
from .models import Farmer, Land
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Land,Plan,Farmer
from .utilities import get_weather_json, get_ai_response,get_plan
from django.db import transaction
from django.contrib.auth.models import User
from datetime import datetime,date
from .price_api import fetch_avg_prices

API_URL = "http://localhost:8100/"



@csrf_exempt
def login_api(request):
    # 1. Get credentials from the app
    phone = "FAR"+str(request.POST.get('phone_number'))
    password = request.POST.get('password')

    print(phone,password)

    # 2. Authenticate using your custom user model
    user = authenticate(username=phone, password=password)

    if user:
        # 3. Create the JWT token "on the fly"
        refresh = RefreshToken.for_user(user)
        
        return JsonResponse({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user_details": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": phone[3::]
            }
        })
    else:
        return JsonResponse({"error": "Invalid phone or password"}, status=401)





@csrf_exempt
def signup_farmer(request):
    if request.method == 'POST':
        data = request.POST
        raw_phone = data.get('phone_number') # e.g., 9876543210    
        
        if not raw_phone:
            return JsonResponse({"error": "Phone number is required"}, status=400)

        # Create the username with the FAR prefix
        custom_username = f"FAR{raw_phone}"
        print(custom_username)

        try:
            with transaction.atomic():
                # 1. Create the inbuilt User
                # We save the phone number as the username
                user = User.objects.create_user(
                    username=custom_username,
                    password=data.get('password'),
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', ''),
                    email=data.get('email', '')
                )

                # 2. Create the Farmer personal info and link to the user
                Farmer.objects.create(
                    user=user,
                    region=data.get('region'),
                    govt_farmer_id=data.get('govt_farmer_id',""),
                    dob=datetime.strptime(data.get("dob"), '%Y-%m-%d').date(),
                    literacy_level=data.get('literacy_level',"BASIC"),
                    income_range=data.get('income_range')
                )

            

            return JsonResponse({
                "status": "success", 
                "username": custom_username,
                "message": "User and Profile created successfully"
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e) ,"type":"inbound"}, status=400,)

    return JsonResponse({"error": "Method not allowed"}, status=405)

# --- PLAN ENDPOINTS ---
@api_view(['GET'])
def get_plans(request):
    farmer = request.user
    # If a specific plan_id is provided in URL params (?id=1)
    plan_id = request.GET.get('id')
    if plan_id:
        plan = Plan.objects.filter(id=plan_id).values().first()
        return JsonResponse(plan or {"error": "Not found"}, safe=False)
    
    plans = list(Plan.objects.filter(user=farmer).values())
    return JsonResponse(plans, safe=False)

@csrf_exempt
@api_view(['POST'])
def add_plan(request):

    data = request.json()

    crop = data.get('crop')
    land = Land.objects.get(id=data.get('land_id'))


    response = get_plan(crop,land)

        # request.user comes from your JWT Middleware
    new_plan = Plan.objects.create(
            user=request.user,
            details=response,
            land=land,
        )
    return JsonResponse({"message": "Plan added", "id": new_plan.id, "plan":response})

# --- EXTERNAL API ENDPOINTS ---
@api_view(['GET'])
def weather_view(request):
    print(request.GET.get('lat'))
    lat = request.GET.get('lat', 20)
    lon = request.GET.get('lon', 10)
    # Replace with your real OpenWeatherMap key
    data  = get_weather_json(lat,lon)
    if 'metadata' in data and isinstance(data['metadata'].get('timezone'), bytes):
        data['metadata']['timezone'] = data['metadata']['timezone'].decode('utf-8')

    return JsonResponse(data)

@api_view(['GET'])
def market_view(request):
    # Simulated market data
    state = request.GET.get('state','Mumbai')
    mandi = request.GET.get('mandi','ok')
    crop = request.GET.get('crop','wheat')
    data = fetch_avg_prices(state,mandi,crop)
    print(data)
    return JsonResponse(data,safe=False)

# --- AI / PROCESSING ENDPOINTS ---

@csrf_exempt
def crop_recommendation(request):
    # Here you would typically send data to your ML model/local API
    # Taking inputs like N, P, K, humidity from POST
    landid = request.GET.get('land_id',80)
    n,p,k,lat,lon,ph = Land.objects.filter(id = landid).values_list('n','p','k','lat','lon','ph')[0]

    weatherapi = get_weather_json(lat,lon)
    humidity = weatherapi['main']['humidity']
    rainfall = weatherapi['rain'].get('1h',0) if 'rain' in weatherapi else 0
    temperature = weatherapi['main']['temp']
    

    Response = requests.post(API_URL + 'recommend/', json={
        'N': n,
        'P': p,
        'K': k,
        'humidity': humidity,
        "ph": ph,
        'rainfall': rainfall,
        'temperature': temperature
    }, timeout=30)

    return JsonResponse(Response.json())

@csrf_exempt
def plant_diagnosis(request):
    image_fs_path = None
    if 'image' in request.FILES:
            image = request.FILES['image']
            fs = FileSystemStorage()
            filename = fs.save(f"lands/{uuid.uuid4().hex}_{image.name}", image)
            image_url = fs.url(filename)
            image_fs_path = os.path.join(settings.MEDIA_ROOT, filename)

    reponse = requests.post(API_URL + 'plant/' + image_fs_path, timeout=60)

    response = get_ai_response(reponse)
    if response:
        return JsonResponse({"diagnosis": response})

    return JsonResponse({"error": "No image"}, status=400)

def get_lands(request):
    farmer = request.user
    lands = list(Land.objects.filter(farmer__user=farmer).values())
    return JsonResponse(lands, safe=False)

def add_land(request):

    if request.method == 'POST':
        farmer = Farmer.objects.get(user=request.user)

        # 1) Save uploaded image to MEDIA (if provided)
        image_url = None
        image_fs_path = None
        if 'image' in request.FILES:
            image = request.FILES['image']
            fs = FileSystemStorage()
            filename = fs.save(f"lands/{uuid.uuid4().hex}_{image.name}", image)
            image_url = fs.url(filename)
            image_fs_path = os.path.join(settings.MEDIA_ROOT, filename)

        # 2) Ensure an image was uploaded and saved; require image for analysis
        if not image_fs_path:
            return JsonResponse({"error": "Image is required"}, status=400)

        # 3) Call external image-processing API with the saved file path (must succeed)
        analysis = {}
        try:
            resp = requests.post(API_URL + 'soil/' + image_fs_path, timeout=30)
            resp.raise_for_status()
            analysis = resp.json()
        except Exception as e:
            logging.exception("Image analysis request failed")
            return JsonResponse({"error": "Image analysis failed", "details": str(e)}, status=500)


        # 4) Save Land record with analysis results
        try:
            with transaction.atomic():
                new_land = Land.objects.create(
                    farmer=farmer,
                    lat=request.POST.get('lat'),
                    lon=request.POST.get('lon'),
                    ownership=request.POST.get('ownership', 'OWNER'),
                    soil_type = analysis.get('soil_type'),
                    nitrogen = analysis.get('nitrogen') or 0.1,
                    phosphorus = analysis.get('phosphorus') or 0.0,
                    potassium = analysis.get('potassium') or 0.0,
                    ph = analysis.get('ph'),
                    organic_matter = analysis.get('organic_matter'),
                    crops = analysis.get('eligible_crops')
                )
        except Exception as e:
            logging.exception("Failed to create Land")
            return JsonResponse({"error": "Failed to save land", "details": str(e)}, status=500)

        # 5) Respond with success, include saved image path and analysis
        return JsonResponse({"message": "Land added", "id": new_land.landid,"analysis": analysis})

    return JsonResponse({"error": "Method not allowed"}, status=405)