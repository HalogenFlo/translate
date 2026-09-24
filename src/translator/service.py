import urllib.parse
import urllib.request
import json
import logging
import requests
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class TranslatorService:
    def __init__(self):
        self.cache: Dict[str, str] = {}
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })

    def translate(self, text: str, source_lang: str = "en", target_lang: str = "vi") -> str:
        """
        Dịch chuỗi văn bản text sang target_lang (mặc định là 'vi' - Tiếng Việt).
        """
        clean_text = text.strip()
        if not clean_text:
            return ""

        cache_key = f"{source_lang}_{target_lang}_{clean_text}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        translated_text = self._translate_mymemory(clean_text, source_lang, target_lang)
        if not translated_text:
            translated_text = self._translate_google(clean_text, source_lang, target_lang)

        if not translated_text:
            # Fallback nếu mạng gặp vấn đề thì trả lại text gốc
            translated_text = clean_text

        self.cache[cache_key] = translated_text
        # Đồng thời lưu cache với key là raw text nếu là default lang
        self.cache[clean_text] = translated_text
        return translated_text

    def _translate_mymemory(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Dịch qua MyMemory API miễn phí"""
        try:
            # MyMemory dùng format 'en|vi' hoặc 'autodetect|vi'
            src = "autodetect" if source_lang in ["auto", "autodetect"] else source_lang
            langpair = f"{src}|{target_lang}"
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": text,
                "langpair": langpair
            }
            resp = self.session.get(url, params=params, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                if "responseData" in data and "translatedText" in data["responseData"]:
                    result = data["responseData"]["translatedText"]
                    if result and not result.startswith("MYMEMORY WARNING"):
                        return result
        except Exception as e:
            logger.debug(f"MyMemory translation error: {e}")
        return None

    def _translate_google(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Dịch fallback qua Google Translate endpoint"""
        try:
            sl = "auto" if source_lang in ["auto", "autodetect"] else source_lang
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as response:
                res_bytes = response.read()
                data = json.loads(res_bytes.decode('utf-8'))
                if data and isinstance(data, list) and len(data) > 0:
                    sentences = [item[0] for item in data[0] if item and len(item) > 0 and item[0]]
                    return "".join(sentences)
        except Exception as e:
            logger.debug(f"Google translate error: {e}")
        return None
