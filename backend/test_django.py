import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, 'd:\\heatmap\\ai-study-tutor\\backend')
django.setup()

from backend.apps.core.services.ai_service import ask_ai
from django.conf import settings

print(f"GROQ_API_KEY loaded: {settings.GROQ_API_KEY[:20]}...")
print(f"GROQ_MODEL: {settings.GROQ_MODEL}")
print()

try:
    result = ask_ai("What is photosynthesis?", "Biology")
    print("✓ SUCCESS!")
    print(f"Answer: {result.answer[:150]}...")
    print(f"Examples: {result.examples[:2]}")
    print(f"Related Topics: {result.related_topics[:2]}")
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {e}")
