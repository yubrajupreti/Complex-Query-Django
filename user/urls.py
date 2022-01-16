from django.urls import path, include

from rest_framework import routers
from rest_framework.documentation import include_docs_urls


from . import views
from .views import UserView

router = routers.DefaultRouter()
router.register('users', UserView, basename='users')


urlpatterns = [
    path('', include(router.urls)),
    path('user/docs/', include_docs_urls(title='UserAPI')),

]