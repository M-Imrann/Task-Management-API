from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status, viewsets, filters
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from .models import Task
from .serializers import RegisterSerializer, LoginSerializer, TaskSerializer
from django.contrib.auth.models import User


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    register API
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "User registered successfully"},
            status=status.HTTP_201_CREATED
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login API
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_completed', 'due_date']
    search_fields = ['title']

    def get_queryset(self):
        """
        Only return tasks owned by or shared with the authenticated user.
        """
        return Task.objects.filter(
            models.Q(owner=self.request.user) | models.Q(shared_with=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        """
        Automatically sets the logged in user as owner when creating new task
        """
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        """
        Complete task
        """
        task = self.get_object()
        if task.owner != request.user:
            return Response(
                {"error": "You can only complete your own tasks"},
                status=status.HTTP_403_FORBIDDEN
            )
        task.is_completed = True
        task.save()
        return Response(TaskSerializer(task).data)

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """
        Shared Task
        """
        task = self.get_object()
        user_id = request.data.get("user_id")
        email = request.data.get("email")

        try:
            if user_id:
                user = User.objects.get(id=user_id)
            elif email:
                user = User.objects.get(email=email)
            else:
                return Response({"error": "Provide user_id or email"}, status=status.HTTP_400_BAD_REQUEST)

            task.shared_with.add(user)
            return Response({"message": f"Task shared with {user.username}"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
