import os
import django
from django.core.asgi import get_asgi_application

# 1. Set environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'khetimitra.settings')

# 2. Manually trigger django setup
django.setup()

# 3. Initialize the HTTP application
django_asgi_app = get_asgi_application()

# 4. Imports (Must stay below django.setup())
from channels.routing import ProtocolTypeRouter, URLRouter
from services.routing import websocket_urlpatterns
from services.wsmiddleware import JWTAuthMiddleware # Your custom middleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    
    # Replace AuthMiddlewareStack with JWTAuthMiddleware
    "websocket": JWTAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})