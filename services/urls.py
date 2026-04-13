from django.urls import path
from . import views

urlpatterns = [
    path('api/signup/', views.signup_farmer),
    path('api/login/', views.login_api),
    path('api/weather/', views.weather_view),
    path('api/market/', views.market_view),
    path('api/plans/', views.get_plans), # Handles both all and specific via ?id=
    path('api/plans/add/', views.add_plan),
    path('api/recommend/', views.crop_recommendation),
    path('api/diagnosis/', views.plant_diagnosis),
    path('api/lands/', views.get_lands),
    path('api/lands/add/', views.add_land),
]