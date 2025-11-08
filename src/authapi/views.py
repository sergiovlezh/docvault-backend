from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from authapi.serializers import LoginSerializer, UserSerializer


@api_view(["POST"])
@permission_classes([])
def login_view(request):
    """Log in a user using Django session authentication."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data: dict = serializer.validated_data  # type: ignore
    username = data.get("username")
    password = data.get("password")

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return Response({"message": "Login successful", "username": user.username})
    return Response({"error": "Invalid credentials"}, status=400)


@api_view(["POST"])
@permission_classes([])
def logout_view(request):
    """Log out the currently authenticated user."""
    logout(request)
    return Response({"message": "Logged out"})


@api_view(["GET"])
@permission_classes([])
def whoami_view(request):
    """
    Returns info about the current authenticated user.
    """
    if not request.user.is_authenticated:
        return Response({"error": "Not authenticated"}, status=401)
    return Response(UserSerializer(request.user).data)
