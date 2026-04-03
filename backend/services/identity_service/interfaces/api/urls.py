from django.urls import path
from interfaces.api import auth_views

urlpatterns = [
    path("me", auth_views.MeView.as_view(), name="auth-me"),
    path("auth/signup", auth_views.SignupView.as_view(), name="auth-signup"),
    path("auth/login", auth_views.LoginView.as_view(), name="auth-login"),
    path("auth/logout", auth_views.LogoutView.as_view(), name="auth-logout"),
    path("auth/refresh", auth_views.RefreshView.as_view(), name="auth-refresh"),
    path("auth/forgot-password", auth_views.ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("auth/reset-password", auth_views.ResetPasswordView.as_view(), name="auth-reset-password"),
    path("users", auth_views.UserListCreateView.as_view(), name="user-list-create"),
    path("users/<int:user_id>", auth_views.UserDetailView.as_view(), name="user-detail"),
    path("users/<int:user_id>/invite", auth_views.UserInviteView.as_view(), name="user-invite"),
    path("users/<int:user_id>/suspend", auth_views.UserSuspendView.as_view(), name="user-suspend"),
    path("users/<int:user_id>/reactivate", auth_views.UserReactivateView.as_view(), name="user-reactivate"),
]
