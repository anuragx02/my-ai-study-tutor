from django.core.management.base import BaseCommand
from backend.apps.core.models import UserPerformance


class Command(BaseCommand):
    help = "Remove quiz attempts with score=0 (legacy failed quizzes from before answer normalization fix)"

    def handle(self, *args, **options):
        deleted_count, _ = UserPerformance.objects.filter(score=0).delete()
        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted {deleted_count} zero-score attempts")
        )
