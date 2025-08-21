from django.test import TestCase
from datetime import date, timedelta
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Task
from .tasks import send_due_soon_notifications


class AuthTests(TestCase):
    """
    Test Class for testing the authentication.
    """
    def setUp(self):
        self.client = APIClient()

    def test_register_and_login(self):
        """
        Test case for testing the register and login process.
        """

        # For registration
        response = self.client.post("/api/auth/register/", {
            "username": "imran",
            "email": "imran@example.com",
            "password": "imran123"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # For logging
        response = self.client.post("/api/auth/login/", {
            "username": "imran",
            "password": "imran123"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())


class TaskTests(TestCase):
    """
    Test class for testing the tasks.
    """
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="test", password="test123", email="test@example.com"
        )
        self.other = User.objects.create_user(
            username="test1", password="test1123", email="test1@example.com"
        )

        response = self.client.post("/api/auth/login/", {
            "username": "test",
            "password": "test123"
        })
        self.token = response.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_create_and_list_tasks(self):
        """
        Test case for creating and listing task.
        """

        # Create Task
        response = self.client.post("/api/tasks/", {
            "title": "Finish Project",
            "description": "Complete the API",
            "due_date": date.today() + timedelta(days=2),
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # List Tasks
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_retrieve_update_delete_task(self):
        """
        Test case for retrieving, updating and deleting tasks.
        """
        task = Task.objects.create(
            title="Update me",
            description="Old desc",
            due_date=date.today() + timedelta(days=2),
            owner=self.user
        )
        url = f"/api/tasks/{task.id}/"

        # Retrieve
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update task
        response = self.client.put(url, {
            "title": "Updated",
            "description": "New desc",
            "due_date": date.today() + timedelta(days=3),
            "is_completed": False
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["title"], "Updated")

        # Delete Task
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_filter_and_search(self):
        """
        Test Case for filtering and searching tasks.
        """
        Task.objects.create(
            title="Read book",
            description="Study Django",
            due_date=date.today(),
            owner=self.user,
            is_completed=True
        )
        Task.objects.create(
            title="Write code",
            description="Practice DRF",
            due_date=date.today(),
            owner=self.user,
            is_completed=False
        )

        # Filtering
        response = self.client.get("/api/tasks/?is_completed=True")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)

        # Searching
        response = self.client.get("/api/tasks/?search=Write")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_complete_task(self):
        """
        Test case for complete task.
        """
        task = Task.objects.create(
            title="Do homework",
            due_date=date.today(),
            owner=self.user
        )
        url = f"/api/tasks/{task.id}/complete/"

        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["is_completed"])

    def test_share_task(self):
        """
        Testcase for shared task
        """
        task = Task.objects.create(
            title="Shared Task",
            due_date=date.today(),
            owner=self.user
        )
        url = f"/api/tasks/{task.id}/share/"

        response = self.client.post(url, {"user_id": self.other.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Task shared with", response.json()["message"])


class CeleryTaskTests(TestCase):
    """
    Testclass for Celery Task
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username="ali", password="password123", email="ali@example.com"
        )

    def test_send_due_soon_notifications(self):
        """
        Testcase for testing send due soon notification
        """
        task = Task.objects.create(
            title="Tomorrow's Task",
            description="Due soon",
            due_date=date.today() + timedelta(days=1),
            owner=self.user,
            is_completed=False
        )

        result = send_due_soon_notifications()

        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(Task.objects.first().title, "Tomorrow's Task")
