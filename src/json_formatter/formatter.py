import json
import re
from typing import Any


class JSONFormatter:
    def __init__(self, indent: int = 2, sort_keys: bool = False, compact: bool = False, ensure_ascii: bool = True):
        self.indent = indent
        self.sort_keys = sort_keys
        self.compact = compact
        self.ensure_ascii = ensure_ascii

    def format(self, data: str) -> str:
        try:
            obj = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(str(e))
        if self.compact:
            return json.dumps(obj, separators=(',', ':'), indent=None, sort_keys=self.sort_keys, ensure_ascii=self.ensure_ascii)
        return json.dumps(obj, indent=self.indent, sort_keys=self.sort_keys, ensure_ascii=self.ensure_ascii)


def format_json(data: str, indent: int = 2, sort_keys: bool = False, compact: bool = False, ensure_ascii: bool = True, unicode: bool = False) -> str:
    """JSON verisini formatlar ve string olarak döndürür."""
    formatter = JSONFormatter(indent=indent, sort_keys=sort_keys, compact=compact, ensure_ascii=ensure_ascii and not unicode)
    return formatter.format(data)


def is_already_formatted(content: str, **opts) -> bool:
    """Verilen içeriğin halihazırda formatlanmış olup olmadığını kontrol eder.

    Karşılaştırma her iki taraf rstrip('\\r\\n') ile normalize edilerek yapılır.
    Geçersiz JSON durumunda (ValueError) False döner.
    """
    try:
        formatted = format_json(content, **opts)
        return formatted.rstrip("\r\n") == content.rstrip("\r\n")
    except ValueError:
        return False


def colorize_json(obj: Any, indent: int = 2, sort_keys: bool = False) -> str:
    """Parse edilmiş Python nesnesini renkli JSON string'e dönüştürür.

    Ham metin değil, json.loads() veya doğrudan oluşturulmuş Python nesnesi alır;
    recursive _walk() iç fonksiyonuyla nesnenin her düğümüne uygun ANSI rengi uygular.

    Renk haritası:
        dict anahtarları  -> sarı  (\033[33m)
        string değerleri  -> yeşil (\033[32m)
        sayı değerleri    -> cyan  (\033[36m)
        bool / null       -> mavi  (\033[34m)

    Her renk bloğunun ardından \033[0m reset kodu gelir.
    """
    YELLOW = "\033[33m"
    GREEN  = "\033[32m"
    CYAN   = "\033[36m"
    BLUE   = "\033[34m"
    RESET  = "\033[0m"

    def _walk(node: Any, level: int = 0) -> str:
        pad       = " " * indent * level
        child_pad = " " * indent * (level + 1)

        # bool, int'in alt sınıfı olduğundan int'ten önce kontrol edilmeli
        if isinstance(node, bool):
            val = "true" if node else "false"
            return f"{BLUE}{val}{RESET}"
        elif node is None:
            return f"{BLUE}null{RESET}"
        elif isinstance(node, str):
            # json.dumps ile tırnak ve kaçış karakterleri doğru üretilir
            return f"{GREEN}{json.dumps(node)}{RESET}"
        elif isinstance(node, (int, float)):
            return f"{CYAN}{json.dumps(node)}{RESET}"
        elif isinstance(node, list):
            if not node:
                return "[]"
            items = [f"{child_pad}{_walk(item, level + 1)}" for item in node]
            return "[\n" + ",\n".join(items) + f"\n{pad}]"
        elif isinstance(node, dict):
            if not node:
                return "{}"
            keys = sorted(node.keys()) if sort_keys else list(node.keys())
            items = []
            for k in keys:
                colored_key = f'{YELLOW}"{k}"{RESET}'
                colored_val = _walk(node[k], level + 1)
                items.append(f"{child_pad}{colored_key}: {colored_val}")
            return "{\n" + ",\n".join(items) + f"\n{pad}}}"
        else:
            # Bilinmeyen türler için str() fallback
            return str(node)

    return _walk(obj)
