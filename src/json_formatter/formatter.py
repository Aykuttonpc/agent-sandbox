import json
import re


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


def format_json(data: str, indent: int = 2, sort_keys: bool = False, compact: bool = False, ensure_ascii: bool = True) -> str:
    """JSON verisini formatlar ve string olarak döndürür."""
    formatter = JSONFormatter(indent=indent, sort_keys=sort_keys, compact=compact, ensure_ascii=ensure_ascii)
    return formatter.format(data)


def colorize_json(text: str) -> str:
    """Biçimlendirilmiş JSON metnine ANSI renk kodları uygular.

    Giriş olarak json.dumps tarafından üretilmiş (sözdizimsel olarak geçerli,
    biçimlendirilmiş) JSON metni alır; dört regex kalıbını sırayla uygulayarak
    terminalde renkli görüntülenmesini sağlar.

    Renk haritası:
        dict anahtarları  → cyan   (\033[36m)
        string değerleri  → yeşil  (\033[32m)
        sayı değerleri    → sarı   (\033[33m)
        true/false/null   → mavi   (\033[34m)
    """
    # (1) Dict anahtarları: "key": → cyan; ":" reset dışında bırakılır,
    #     böylece (2) ve (3) kalıpları ":" çıpasını hâlâ bulabilir.
    text = re.sub(r'"([^"]+)":', r'\033[36m"\1"\033[0m:', text)

    # (2) String değerleri: : "val" → yeşil (":"+boşluk kısmı renksiz kalır)
    text = re.sub(r'(:\s*)"([^"]*)"', r'\1\033[32m"\2"\033[0m', text)

    # (3) Sayı değerleri: : 42 veya : -3.14 → sarı
    text = re.sub(r'(:\s*)(-?\d+(?:\.\d+)?)', r'\1\033[33m\2\033[0m', text)

    # (4) true / false / null → mavi
    text = re.sub(r'\b(true|false|null)\b', r'\033[34m\1\033[0m', text)

    return text
