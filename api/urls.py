from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('upload/', upload_file_api, name='upload'),
    path('subtitle/', subtitle_list_api, name='subtitle'),
    path('subtitle/<int:pk>/', subtitle_detail_api, name='subtitle_detail_api'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]