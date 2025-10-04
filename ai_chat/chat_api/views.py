import secrets
from django.db import transaction
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, Chat, AuthToken
from .serial import (
    RegisterSerializer,
    LoginSerializer,
    ChatRequestSerializer,
    ChatSerializer,
    TokenBalanceSerializer,
)
from .model import generate_ai_response

TOKEN_COST_PER_QUESTION = 100


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        return Response(
            {"message": "Registration successful", "username": user.username, "tokens": user.tokens},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # create a new token each login (or reuse; here we issue new)
        key = secrets.token_hex(32)
        AuthToken.objects.create(key=key, user=user)
        return Response({"token": key, "username": user.username}, status=status.HTTP_200_OK)


class ChatView(APIView):
    """
    Requires authentication via our TokenHeaderAuthentication.
    Deducts 100 tokens per question, prevents negative balances,
    saves chat, returns response.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        req_ser = ChatRequestSerializer(data=request.data)
        if not req_ser.is_valid():
            return Response({"errors": req_ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        if user.tokens < TOKEN_COST_PER_QUESTION:
            return Response(
                {"message": "Insufficient tokens", "tokens": user.tokens},
                status=status.HTTP_402_PAYMENT_REQUIRED,  # or 400 if you prefer
            )

        message = req_ser.validated_data["message"]

        # Deduct first (atomic), then call model
        user.tokens -= TOKEN_COST_PER_QUESTION
        user.save(update_fields=["tokens"])

        try:
            ai_response = generate_ai_response(message)
        except Exception as e:
            # Rollback tokens on failure
            transaction.set_rollback(True)
            return Response(
                {"message": "AI service error", "detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        chat = Chat.objects.create(user=user, message=message, response=ai_response)
        return Response(
            {
                "message": message,
                "response": ai_response,
                "tokens_remaining": user.tokens,
                "chat": ChatSerializer(chat).data,
            },
            status=status.HTTP_200_OK,
        )


class TokenBalanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        ser = TokenBalanceSerializer({"tokens": user.tokens})
        return Response(ser.data, status=status.HTTP_200_OK)
