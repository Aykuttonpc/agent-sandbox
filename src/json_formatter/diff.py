"""JSON diff modülü: orijinal ile formatlanmış içerik arasındaki farkı üretir.

diff_format(original, formatted, filename, use_color) -> str

Unified diff formatında satırları döndürür.
use_color=True ise '+' satırları yeşil (\x1b[32m), '-' satırları kırmızı (\x1b[31m)
ANSI rengiyle renklendirilir; use_color=False ise düz metin döner.
İçerik özdeşse boş string ("") döner.
"""
import difflib

RED   = "\x1b[31m"
GREEN = "\x1b[32m"
RESET = "\x1b[0m"


def diff_format(
    original: str,
    formatted: str,
    filename: str = "file.json",
    use_color: bool = False,
) -> str:
    """Orijinal ve formatlanmış içerik arasındaki unified diff'i döndürür.

    Algoritma:
    - Her iki içerik ``splitlines(keepends=True)`` ile satırlara bölünür.
    - Son satır newline ile bitmiyorsa ``\\n`` eklenerek normalize edilir
      (diff çıktısının tutarlı olması için).
    - ``difflib.unified_diff`` ile fark hesaplanır.
    - use_color=True ise:
        * ``+`` ile başlayan (``+++`` hariç) satırlar yeşil renklendirilir.
        * ``-`` ile başlayan (``---`` hariç) satırlar kırmızı renklendirilir.
        * ``@@`` hunk başlıkları ve ``---``/``+++`` dosya satırları renksiz kalır.

    Args:
        original:   Orijinal dosya içeriği.
        formatted:  Formatlanmış içerik.
        filename:   Diff başlığında (``--- a/…`` / ``+++ b/…``) kullanılacak dosya adı.
        use_color:  True ise ANSI renk kodları eklenir; False ise düz metin döner.

    Returns:
        Unified diff string'i.  İçerik özdeşse boş string (``""``) döner.
    """
    original_lines  = original.splitlines(keepends=True)
    formatted_lines = formatted.splitlines(keepends=True)

    # Son satır newline ile bitmiyorsa ekle
    if original_lines and not original_lines[-1].endswith("\n"):
        original_lines[-1] += "\n"
    if formatted_lines and not formatted_lines[-1].endswith("\n"):
        formatted_lines[-1] += "\n"

    diff = list(difflib.unified_diff(
        original_lines,
        formatted_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    ))

    if not diff:
        return ""

    if not use_color:
        return "".join(diff)

    colored = []
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            colored.append(GREEN + line + RESET)
        elif line.startswith("-") and not line.startswith("---"):
            colored.append(RED + line + RESET)
        else:
            colored.append(line)
    return "".join(colored)
