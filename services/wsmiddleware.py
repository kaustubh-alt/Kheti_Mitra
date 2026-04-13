from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user(phone_number):
    try:
        return User.objects.get(phone_number=phone_number)
    except User.DoesNotExist:
        return AnonymousUser()

class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # 1. Get token from the query string (e.g., ws://localhost:8000/ws/chat/?token=xyz)
        query_string = scope.get("query_string", b"").decode()
        query_params = dict(qc.split("=") for qc in query_string.split("&") if "=" in qc)
        token_key = query_params.get("token")

        if token_key:
            try:
                # 2. Validate the JWT
                access_token = AccessToken(token_key)
                # SimpleJWT stores the PK in the 'user_id' claim
                user_phone = access_token["user_id"]
                
                # 3. Get user and attach to scope
                scope['user'] = await get_user(user_phone)
            except Exception:
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await self.app(scope, receive, send)