"""URL configuration for miniapp project."""

from django.urls import path, include

urlpatterns = [
    path('', include('instagram_login.urls')),
]

