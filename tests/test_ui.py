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
    assert "Xin chào thế giới" in card.lbl_translated.cget("text")

    root.destroy()
