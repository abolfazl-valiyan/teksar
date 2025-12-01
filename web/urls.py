from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', upload_file, name='upload_file'),

    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('sing_up',signup_view,name='signup'),
    path('list/', file_list, name='file_list'),
    path('files/<int:pk>/', file_detail, name='file_detail'),
    path('download_result/<int:pk>/<str:file_type>/', download_result, name='download'),
]