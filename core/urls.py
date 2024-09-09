from django.urls import path
from .apis.views import registerview, loginview
urlpatterns = [
    path("register/", registerview.RegisterView.as_view(), name="register"),
    path("login/", loginview.LoginView.as_view(), name="login")
]
