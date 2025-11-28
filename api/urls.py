from django.urls import path
from .views import *

urlpatterns = [
    path('upload/', upload_file_api, name='upload'),
    path('subtitle/', subtitle_list_api, name='subtitle'),
    path('subtitle/<int:pk>/', subtitle_detail_api, name='subtitle_detail_api')
]