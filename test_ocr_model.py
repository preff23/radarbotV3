#!/usr/bin/env python3
"""
Тест модели OCR
"""
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from bot.core.config import config
from bot.ai.vision import vision_processor

def test_ocr_model():
    """Тест модели OCR"""
    print("🧪 Тест модели OCR...")
    
    print(f"✅ Vision provider: {config.vision_provider}")
    print(f"✅ Vision model: {config.vision_model}")
    print(f"✅ Vision processor model: {vision_processor.model}")
    
    if config.vision_model == "gpt-4o":
        print("🎉 OCR настроен на GPT-4o для лучшего качества распознавания!")
        return True
    else:
        print(f"❌ OCR использует {config.vision_model} вместо gpt-4o")
        return False

if __name__ == "__main__":
    test_ocr_model()
