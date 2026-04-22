#!/usr/bin/env python
"""
Simple test script to verify OCR functionality.
Usage: python test_ocr.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.apps.core.services.ai_service import extract_text_from_image

# Test with a public image URL
test_image_url = "https://upload.wikimedia.org/wikipedia/commons/f/f2/LPU-v1-die.jpg"
test_instruction = "What's in this image?"

print("Testing OCR with Groq Vision API...")
print(f"Image URL: {test_image_url}")
print(f"Instruction: {test_instruction}")
print("-" * 80)

try:
    result = extract_text_from_image(test_image_url, test_instruction)
    print("✅ OCR SUCCESS")
    print("Extracted text:")
    print(result)
except Exception as e:
    print("❌ OCR FAILED")
    print(f"Error: {e}")
