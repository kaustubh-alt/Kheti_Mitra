# middleware.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import JsonResponse

class JWTManualValidator:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Define public paths that DON'T need a token
        # 1. Define public paths that DON'T need a token
        public_paths = ['/api/signup/', '/api/login/']

        # 2. If the current request is for a public path, just let it pass
        if request.path in public_paths:
            return self.get_response(request)

        # 3. For all other API paths, check for the token
        if request.path.startswith('/api/'):
            
            # 4. Get the "Bearer <token>" string
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({"error": "Unauthorized: Missing Token"}, status=401)

            try:
                # 3. Extract and Validate
                token = auth_header.split(' ')[1]
                authenticator = JWTAuthentication()
                
                # This check ensures the token hasn't been tampered with and isn't expired
                validated_token = authenticator.get_validated_token(token)
                
                # 4. Attach User to request (Django uses phone_number PK here)
                request.user = authenticator.get_user(validated_token)
                
            except Exception as e:
                return JsonResponse({"error": f"Invalid Token: {str(e)}"}, status=401)

        return self.get_response(request)