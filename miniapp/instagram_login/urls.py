"""URL configuration for Instagram login app."""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('save_cookies/', views.save_cookies, name='save_cookies'),
]

