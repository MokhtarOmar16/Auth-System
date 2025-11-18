from django.urls import path
from .apis.views import registerview, loginview, refreshview, changepassword
from .test_middleware_view import test_anonymous_middleware

urlpatterns = [
    path("register/", registerview.RegisterView.as_view(), name="register"),
    path("login/", loginview.LoginView.as_view(), name="login"),
    path("refresh/", refreshview.RefreshView.as_view(), name="refresh"),
    path("changepassword/", changepassword.ChangePasswordView.as_view(), name="change_password"),
    path("test-anonymous/", test_anonymous_middleware, name="test_anonymous"),
]
