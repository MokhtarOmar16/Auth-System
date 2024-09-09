from django.urls import path
from .apis.views import registerview, loginview, refreshview
urlpatterns = [
    path("register/", registerview.RegisterView.as_view(), name="register"),
    path("login/", loginview.LoginView.as_view(), name="login"),
    path("refresh/", refreshview.RefreshView.as_view(), name="refresh")
]
