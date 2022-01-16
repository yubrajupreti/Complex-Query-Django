from django.urls import path, include

from rest_framework import routers

from . import views
from .views import UserView

router = routers.DefaultRouter()
router.register('users', UserView, basename='users')


urlpatterns = [
    path('', include(router.urls)),

]