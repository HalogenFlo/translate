import pytest
from unittest.mock import MagicMock
from src.ui.app import SubtitleCard

def test_subtitle_card_creation():
    import customtkinter as ctk
    # Khởi tạo root ẩn cho test
    root = ctk.CTk()
    root.withdraw() # Ẩn cửa sổ khi test

    card = SubtitleCard(
        root,
        original_text="Hello world",
        translated_text="Xin chào thế giới",
        timestamp_str="12:00:00"
    )

    assert card.original_text == "Hello world"
    assert card.translated_text == "Xin chào thế giới"
    assert "Hello world" in card.lbl_original.cget("text")
    root.destroy()

def test_format_all_history():
    from src.ui.app import ToolListenApp
    history = [
        {"time": "12:00:00", "original": "Hello", "translated": "Xin chào"},
        {"time": "12:00:05", "original": "Goodbye", "translated": "Tạm biệt"}
    ]
    formatted_bilingual = ToolListenApp.format_history_text(history, mode="both")
    assert "Hello" in formatted_bilingual
    assert "Xin chào" in formatted_bilingual
    assert "Goodbye" in formatted_bilingual
    assert "Tạm biệt" in formatted_bilingual

    formatted_vi_only = ToolListenApp.format_history_text(history, mode="vi_only")
    assert "Xin chào" in formatted_vi_only
    assert "Tạm biệt" in formatted_vi_only
    assert "Hello" not in formatted_vi_only

def test_app_tts_integration():
    from src.ui.app import ToolListenApp
    import customtkinter as ctk
    app = ToolListenApp()
    app.withdraw()

    # Kiểm tra service tts đã được gắn vào app
    assert hasattr(app, "tts")
    assert app.tts is not None
    assert app.tts.enabled is False

    # Kiểm tra toggle tts
    app._toggle_tts()
    assert app.tts.enabled is True
    app._toggle_tts()
    assert app.tts.enabled is False

    app.destroy()


