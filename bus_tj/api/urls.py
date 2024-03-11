"""APIs of api app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register('bus', views.BusViewSet, basename='bus')
router.register('stop', views.StopViewSet, basename='stop')
router.register('location', views.LocationViewSet, basename='location')

urlpatterns = [
    path('', include(router.urls)),
]
