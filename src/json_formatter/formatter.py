import json
import os
import shutil
import tempfile
from typing import Any, Optional


class JSONFormatter:
    def __init__(self, indent: int = 2, sort_keys: bool = False, compact: bool = False, ensure_ascii: bool = True, separators=None):
        self.indent = indent
        self.sort_keys = sort_keys
        self.compact = compact
        self.ensure_ascii = ensure_ascii
        self.separators = separators

    def format(self, data: str) -> str:
        try:
            obj = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Geçersiz JSON: {e}") from e

        separators = self.separators if self.separators else ((',', ':') if self.compact else (', ', ': '))

        if self.compact:
            return json.dumps(obj, separators=separators, indent=None, sort_keys=self.sort_keys, ensure_ascii=self.ensure_ascii)
        return json.dumps(obj, separators=separators, indent=self.indent, sort_keys=self.sort_keys, ensure_ascii=self.ensure_ascii)


def format_json(data: str, indent: int = 2, sort_keys: bool = False, compact: bool = False, ensure_ascii: bool = True, unicode: bool = False, tab: bool = False) -> str:
    """JSON verisini formatlar ve string olarak döndürür.

    tab=True ve compact=False ise indent olarak '\\t' kullanılır.
    tab=True ve compact=True ise compact önceliklidir; tab sessizce yoksayılır.
    compact=True ise indent parametresi yok sayılır.
    
    Geçersiz JSON durumunda ValueError raise eder.
    """
    if compact:
        indent = None
    
    actual_indent = "\t" if (tab and not compact) else indent
    
    separators = (',', ':') if compact else (', ', ': ')
    
    formatter = JSONFormatter(indent=actual_indent, sort_keys=sort_keys, compact=compact, ensure_ascii=ensure_ascii and not unicode, separators=separators)
    return formatter.format(data)  # ValueError raise et


def is_already_formatted(content: str, **opts) -> bool:
    """Verilen içeriğin halıhazırda formatlanmış olup olmadığını kontrol eder.

    Karşılaştırma her iki taraf rstrip('\\r\\n') ile normalize edilerek yapılır.
    Geçersiz JSON durumunda False döner.
    """
    try:
        formatted = format_json(content, **opts)
        return formatted.rstrip("\r\n") == content.rstrip("\r\n")
    except json.JSONDecodeError:
        return False
    except (ValueError, TypeError):
        return False


def is_formatted(json_str: str, indent: int = 2, sort_keys: bool = False, compact: bool = False, tab: bool = False, unicode_: bool = False) -> bool:
    """Verilen JSON string'in verilen parametrelerle formatlanmış olup olmadığını kontrol eder.
    
    Args:
        json_str: JSON string
        indent: İndent seviyesi (default: 2)
        sort_keys: Anahtarı alfabetik sırala (default: False)
        compact: Kompakt format (default: False)
        tab: Tab karakteri kullan (default: False)
        unicode_: Non-ASCII karakterleri escape etme (default: False, yani escape et)
    
    Returns:
        True eğer json_str verilen parametrelerle formatlanmışsa, False aksi halde
    
    Örnek:
        >>> is_formatted('{"a": 1}')  # Default indent=2, formatlanmış
        True
        >>> is_formatted('{"a":1}')  # Kompakt, formatlanmamış
        False
        >>> is_formatted('{"b": 1, "a": 2}', sort_keys=True)  # sort-keys yok
        False
    """
    try:
        # unicode_: False → unicode=False (escape et)
        # unicode_: True  → unicode=True  (escape etme)
        formatted = format_json(
            json_str,
            indent=indent,
            sort_keys=sort_keys,
            unicode=unicode_,
            compact=compact,
            tab=tab
        )
        return formatted.rstrip("\r\n") == json_str.rstrip("\r\n")
    except json.JSONDecodeError:
        return False
    except (ValueError, TypeError):
        return False


def format_json_to_file(filepath: str, **opts) -> None:
    """Dosyadaki JSON'ı formatlar ve aynı dosyaya atomik biçimde yazar.
    
    - Dosyayı oku
    - format_json() ile formatla
    - Aynı dizinde temp dosya oluştur (delete=False)
    - shutil.copystat() ile izinleri kopyala
    - os.replace() ile atomik swap yap
    - try/finally ile error sırasında temp dosyasını sil
    
    Args:
        filepath: Formatlanacak JSON dosyasının yolu
        **opts: format_json() fonksiyonuna geçirilecek parametreler
        
    Raises:
        ValueError: Dosya içeriği geçersiz JSON ise (JSONDecodeError'ı sarar)
        IOError: Dosya okuma/yazma hatası ise
    """
    # Dosyayı oku
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Formatla (ValueError raise edebilir)
    formatted = format_json(content, **opts)
    
    # Temp dosya oluştur (aynı dizinde)
    file_dir = os.path.dirname(filepath) or '.'
    temp_fd, temp_path = tempfile.mkstemp(dir=file_dir, prefix='.tmp_')
    
    try:
        # Temp dosyaya yaz
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            f.write(formatted)
        
        # Orijinal dosyanın izinlerini kopyala
        shutil.copystat(filepath, temp_path)
        
        # Atomik swap
        os.replace(temp_path, filepath)
    finally:
        # Hata durumunda temp dosyasını sil
        if os.path.exists(temp_path):
            os.unlink(temp_path)


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
