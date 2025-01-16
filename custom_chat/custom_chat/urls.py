"""
URL configuration for custom_chat project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from chat.views import chat_view, get_chat_history, delete_chat_history
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', chat_view, name='chat_view'),  # Route for home page
    path('chat/', chat_view, name='chat_view'),
    path('get_chat_history/<str:user_name>/',get_chat_history, name='get_chat_history'),
    path('delete_chat_history/<str:user_name>/',delete_chat_history, name='delete_chat_history')
]
