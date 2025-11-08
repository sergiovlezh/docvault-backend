from django.urls import path

from authapi.views import login_view, logout_view, whoami_view

urlpatterns = [
    path("login/", login_view, name="auth-login"),
    path("logout/", logout_view, name="auth-logout"),
    path("whoami/", whoami_view, name="auth-whoami"),
]
