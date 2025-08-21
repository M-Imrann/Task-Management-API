from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet


router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename="task")

urlpatterns = [
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('', include(router.urls)),
]
