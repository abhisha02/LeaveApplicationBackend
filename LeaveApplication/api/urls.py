from django.urls import include, path
from . import views
from .views import RegisterView, LoginView, UserDetailView
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
urlpatterns =[

 path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
 path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

 path('register/', RegisterView.as_view(), name='register'),
 path('login/', LoginView.as_view(), name='login'),
 path('user/', UserDetailView.as_view(), name='user_detail'),
]
