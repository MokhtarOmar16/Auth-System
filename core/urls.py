from django.urls import path
from .apis.views import registerview
urlpatterns = [
    path("register/", registerview.RegisterView.as_view(), name="register")
]
