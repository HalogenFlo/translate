import pytest
from src.translator.service import TranslatorService

def test_translate_empty_text():
    service = TranslatorService()
    assert service.translate("") == ""
    assert service.translate("   ") == ""

def test_translate_english_to_vietnamese():
    service = TranslatorService()
    result = service.translate("Hello, good morning!", source_lang="en", target_lang="vi")
    assert isinstance(result, str)
    assert len(result.strip()) > 0
    # Kết quả dịch phải chứa chữ tiếng Việt phù hợp (ví dụ "chào")
    assert "chào" in result.lower() or "buổi sáng" in result.lower()

def test_translation_caching():
    service = TranslatorService()
    text = "Thank you very much"
    res1 = service.translate(text, source_lang="en", target_lang="vi")
    # Kiểm tra xem có trong cache không
    assert text in service.cache
    res2 = service.translate(text, source_lang="en", target_lang="vi")
    assert res1 == res2

def test_local_ai_translation():
    service = TranslatorService(use_local_ai=True)
    assert service.use_local_ai is True
    result = service.translate("Good morning", source_lang="en", target_lang="vi")
    assert isinstance(result, str)
    assert len(result.strip()) > 0
    assert "chào" in result.lower() or "buổi sáng" in result.lower()

