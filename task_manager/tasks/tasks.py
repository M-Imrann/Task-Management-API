from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Prefetch
from .models import Task


@shared_task
def send_due_soon_notifications():
    """
    Notify owners and shared users about the tasks due
    tomorrow and not completed.
    """
    tomorrow = timezone.localdate() + timedelta(days=1)

    # Prefetch shared users but only emails (non-empty)
    tasks = (
        Task.objects
        .filter(due_date=tomorrow, is_completed=False)
        .select_related("owner")
        .prefetch_related(
            Prefetch("shared_with")
        )
    )

    for task in tasks:
        recipients = []

        # Owner email
        owner_email = (task.owner.email or "").strip()
        if owner_email:
            recipients.append(owner_email)

        # Shared users emails
        shared_emails = [
            (u.email or "").strip()
            for u in task.shared_with.all()
            if (u.email or "").strip()
        ]
        recipients.extend(shared_emails)

        # Deduplicate
        recipients = list(dict.fromkeys(recipients))

        if not recipients:
            continue

        subject = f"Task due tomorrow: {task.title}"
        lines = [
            "Hello,",
            f"Reminder: The task **{task.title}** is due on {task.due_date}.",
            "Description:",
            f"{task.description or 'No description'}",
            f"Status: {'Completed' if task.is_completed else 'Pending'}",
            "— Task Manager",
        ]
        message = "\n".join(lines)

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=recipients,
            fail_silently=True,   # avoid crashing the task on email glitches
        )
