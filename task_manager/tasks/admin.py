from django.contrib import admin
from .models import Task


class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'due_date', 'is_completed', 'owner', 'created_at']
    list_filter = ['title', 'due_date', 'is_completed', 'owner', 'created_at']
    search_fields = ['title', 'owner']


admin.site.register(Task, TaskAdmin)
