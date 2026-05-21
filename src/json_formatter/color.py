"""Token-aware JSON renklendirme modülü.

colorize_json(text: str) -> str

Formatlanmış bir JSON string'ini alır; karakter-karakter tarama yapılırken
durum makinesiyle string sınırları izlenir (string içinde / dışında).
String içindeyken true/null/{ gibi token'lara renk uygulanmaz; token'lar
yalnızca string dışındayken tanınır ve renklendirilir.

Renk haritası:
  dict key'leri        -> sarı   \x1b[33m
  string value'ları    -> yeşil  \x1b[32m
  sayılar              -> cyan   \x1b[36m
  boolean / null       -> mavi   \x1b[34m
  { } [ ] parantezleri -> beyaz  \x1b[37m
"""

import sys

YELLOW = "\x1b[33m"   # key
GREEN  = "\x1b[32m"   # string value
CYAN   = "\x1b[36m"   # number
BLUE   = "\x1b[34m"   # bool / null
WHITE  = "\x1b[37m"   # bracket
RESET  = "\x1b[0m"


def should_colorize(stream=sys.stdout) -> bool:
    """Verilen akışın renklendirmeye uygun olup olmadığını döndürür.

    Akış ``isatty`` metoduna sahipse ve bu metot ``True`` döndürüyorsa
    (yani bir terminale / TTY'ye bağlıysa) ``True``, aksi hâlde
    (pipe, dosyaya yönlendirilmiş, ``isatty`` metodu yoksa) ``False`` döndürür.

    Args:
        stream: Kontrol edilecek G/Ç akışı (varsayılan: sys.stdout).

    Returns:
        Akış bir terminale bağlıysa True, değilse False.
    """
    return hasattr(stream, 'isatty') and stream.isatty()


def colorize_json(text: str) -> str:
    """Formatlanmış JSON string'ini token-aware durum makinesiyle renklendirir.

    Algoritma:
    - String token'ları (``"..."``), açılış tırnağından kapanış tırnağına
      kadar bütünüyle okunur; içindeki karakterler ayrı token olarak
      işlenmez. Kaçış dizileri (``\\\\"``) iki karakter birden atlanarak
      doğru şekilde atlanır.
    - Okunan string token'ının key mi value mı olduğu, token'dan sonraki
      ilk boşluk-dışı karakterin ``:`` olup olmadığına bakılarak belirlenir.
    - Sayılar (negatif ve bilimsel notasyon dahil), ``true``, ``false`` ve
      ``null`` yalnızca string dışındayken eşleştirilir.
    - ``{``, ``}``, ``[``, ``]`` beyaz renkle gösterilir.
    - ``:``, ``,``, boşluk ve satır sonu karakterleri renksiz aktarılır.

    Args:
        text: Renklendirilecek formatlanmış JSON string'i.

    Returns:
        ANSI renk kodları eklenmiş string.
    """
    result = []
    i = 0
    n = len(text)

    while i < n:
        c = text[i]

        # ── String token ────────────────────────────────────────────────────
        if c == '"':
            # Kapanış tırnağına kadar oku; kaçış karakterlerini (\x) atla
            j = i + 1
            while j < n:
                if text[j] == '\\':
                    j += 2          # \x → iki karakteri birden atla
                elif text[j] == '"':
                    j += 1          # kapanış tırnağını dahil et, dur
                    break
                else:
                    j += 1
            string_token = text[i:j]

            # İleriye bak: boşlukları atla → ':' var mı? (key mi, value mı?)
            k = j
            while k < n and text[k] in ' \t\n\r':
                k += 1
            is_key = (k < n and text[k] == ':')

            if is_key:
                result.append(YELLOW + string_token + RESET)
            else:
                result.append(GREEN + string_token + RESET)
            i = j

        # ── Boolean: true ───────────────────────────────────────────────────
        elif text[i:i + 4] == 'true':
            result.append(BLUE + 'true' + RESET)
            i += 4

        # ── Boolean: false ──────────────────────────────────────────────────
        elif text[i:i + 5] == 'false':
            result.append(BLUE + 'false' + RESET)
            i += 5

        # ── Null ────────────────────────────────────────────────────────────
        elif text[i:i + 4] == 'null':
            result.append(BLUE + 'null' + RESET)
            i += 4

        # ── Sayı (negatif ve bilimsel notasyon dahil) ───────────────────────
        elif c in '-0123456789':
            j = i
            while j < n and text[j] in '-+0123456789.eE':
                j += 1
            result.append(CYAN + text[i:j] + RESET)
            i = j

        # ── Süslü ve köşeli parantezler ─────────────────────────────────────
        elif c in '{}[]':
            result.append(WHITE + c + RESET)
            i += 1

        # ── Diğer: ':' ',' boşluk, newline – renksiz aktar ─────────────────
        else:
            result.append(c)
            i += 1

    return ''.join(result)
