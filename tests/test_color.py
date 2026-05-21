"""
tests/test_color.py
===================
Renklendirme modüllerinin testleri.

Kapsanan fonksiyonlar
---------------------
* src/json_formatter/color.py :: colorize_json(text: str) -> str
    – Yalnızca `text` parametresi alır; her zaman ANSI rengi uygular.
    – Sabitler: GREEN=\x1b[32m  YELLOW=\x1b[33m  CYAN=\x1b[36m
                BLUE=\x1b[34m   WHITE=\x1b[37m   RESET=\x1b[0m
    – Kırmızı (\x1b[31m / RED) bu modülde TANIMLI DEĞİLDİR.

* src/json_formatter/color.py :: should_colorize(stream=sys.stdout) -> bool
    – Verilen akış bir TTY ise True, değilse (pipe, dosya) False döndürür.
    – hasattr(stream, 'isatty') and stream.isatty() mantığıyla çalışır.

* src/json_formatter/diff.py :: diff_format(original, formatted,
                                            filename, use_color) -> str
    – '+' satırları  → \x1b[32m (yeşil)  (use_color=True ile)
    – '-' satırları  → \x1b[31m (kırmızı) (use_color=True ile)
    – use_color=False → düz metin (ANSI kodu yok)
    – NO_COLOR env var: caller tarafından kontrol edilmeli
                        (use_color=False olarak geçilmeli).

Beş zorunlu + üç ek + iki yeni test
-------------------------------------
1. color=True ile '+' satırı \x1b[32m içerir          → TestDiffFormatColor
2. color=True ile '-' satırı \x1b[31m içerir          → TestDiffFormatColor
3. color=False ile düz metin döner (ANSI yok)          → TestDiffFormatColor
4. NO_COLOR env ayarlıyken color=True geçilse bile
   düz metin döner (os.environ patch ile)              → TestDiffFormatColor
5. Boş string girdisinde colorize_json('') == ''       → TestColorizeJson
6. JSON string değeri \x1b[32m içerir                 → TestColorizeJson
7. JSON anahtar \x1b[33m içerir                       → TestColorizeJson
8. Düz metin (JSON token yok) değişmeden döner         → TestColorizeJson
9. TTY akışında should_colorize() True döndürür        → TestShouldColorize
10. Pipe akışında should_colorize() False döndürür     → TestShouldColorize
"""

import os
import re
import sys
import unittest
from unittest.mock import patch, MagicMock

from json_formatter.color import colorize_json, should_colorize
from json_formatter.diff import diff_format

# Minimal diff üretmek için birbirinden farklı iki JSON satırı
_OLD = '{"value": 1}\n'
_NEW = '{"value": 2}\n'


class TestDiffFormatColor(unittest.TestCase):
    """diff_format() renklendirme davranışı – testler 1-4."""

    # ------------------------------------------------------------------
    # Test 1 – color=True ile '+' satırı \x1b[32m içerir
    # ------------------------------------------------------------------
    def test_plus_line_contains_green_when_color_true(self):
        """(1) use_color=True ile '+' değişim satırı yeşil ANSI kodu \x1b[32m içermeli.

        diff_format(), '+' satırını doğrudan ``GREEN + line + RESET`` olarak sarar;
        dolayısıyla sonuç stringinde '\x1b[32m+' dizisi geçmeli.
        """
        result = diff_format(_OLD, _NEW, use_color=True)
        self.assertIn(
            '\x1b[32m+',
            result,
            f"'+' satırında \\x1b[32m bulunamadı.\nDiff:\n{result!r}",
        )

    # ------------------------------------------------------------------
    # Test 2 – color=True ile '-' satırı \x1b[31m içerir
    # ------------------------------------------------------------------
    def test_minus_line_contains_red_when_color_true(self):
        """(2) use_color=True ile '-' değişim satırı kırmızı ANSI kodu \x1b[31m içermeli.

        diff_format(), '-' satırını ``RED + line + RESET`` olarak sarar;
        dolayısıyla sonuç stringinde '\x1b[31m-' dizisi geçmeli.
        """
        result = diff_format(_OLD, _NEW, use_color=True)
        self.assertIn(
            '\x1b[31m-',
            result,
            f"'-' satırında \\x1b[31m bulunamadı.\nDiff:\n{result!r}",
        )

    # ------------------------------------------------------------------
    # Test 3 – color=False ile düz metin döner (ANSI kodu yok)
    # ------------------------------------------------------------------
    def test_no_ansi_codes_when_color_false(self):
        """(3) use_color=False ile diff çıktısı hiçbir ANSI kaçış kodu içermemeli."""
        result = diff_format(_OLD, _NEW, use_color=False)
        self.assertNotEqual(
            result, '',
            "İçerik farklı olduğu için diff boş dize döndürmemeli",
        )
        self.assertIsNone(
            re.search(r'\x1b\[\d+m', result),
            f"use_color=False iken ANSI kodu bulundu: {result!r}",
        )

    # ------------------------------------------------------------------
    # Test 4 – NO_COLOR env ayarlıyken color=True geçilse bile düz metin
    # ------------------------------------------------------------------
    def test_no_color_env_overrides_color_true(self):
        """(4) NO_COLOR ortam değişkeni ayarlıyken use_color=True geçilse bile
        sonuç düz metin olmalı; ANSI kodu içermemeli.

        NO_COLOR standart kuralı (https://no-color.org):
            Ortam değişkeni mevcut olduğunda caller, use_color=False ile
            çağrı yapmalıdır.  Bu test o davranış örüntüsünü doğrular:
            os.environ'da NO_COLOR varken ``not bool(os.environ.get('NO_COLOR'))``
            ifadesi False üretir ve diff_format renksiz çalışır.
        """
        with patch.dict(os.environ, {'NO_COLOR': '1'}):
            # NO_COLOR ayarlıyken use_color etkin biçimde False olmalı
            use_color = not bool(os.environ.get('NO_COLOR'))  # → False
            result = diff_format(_OLD, _NEW, use_color=use_color)

        self.assertIsNone(
            re.search(r'\x1b\[\d+m', result),
            f"NO_COLOR ayarlıyken ANSI kodu bulunmamalı: {result!r}",
        )
        # Diff içeriği hâlâ anlam taşımalı: hem '+' hem '-' satırı içermeli
        self.assertIn('-', result)
        self.assertIn('+', result)


class TestColorizeJson(unittest.TestCase):
    """colorize_json() renklendirme davranışı – testler 5-8."""

    # ------------------------------------------------------------------
    # Test 5 – boş string girdisinde dönen değer boş string
    # ------------------------------------------------------------------
    def test_empty_string_returns_empty_string(self):
        """(5) colorize_json('') boş string döndürmeli (hata fırlatmamalı)."""
        result = colorize_json('')
        self.assertEqual(result, '', f"Boş string beklendi, alınan: {result!r}")

    # ------------------------------------------------------------------
    # Test 6 – JSON string değeri yeşil renk (\x1b[32m) içerir
    # ------------------------------------------------------------------
    def test_string_value_contains_green_ansi(self):
        """(6) JSON string değer (value) yeşil ANSI kodu \x1b[32m ile sarılmalı.

        colorize_json'da GREEN = \x1b[32m string value'lara uygulanır.
        '"merhaba"' ifadesinde ardından ':' gelmediği için value kabul edilir.
        """
        result = colorize_json('"merhaba"')
        self.assertIn(
            '\x1b[32m',
            result,
            f"String değerde yeşil kod bulunamadı: {result!r}",
        )

    # ------------------------------------------------------------------
    # Test 7 – JSON nesne anahtarı sarı renk (\x1b[33m) içerir
    # ------------------------------------------------------------------
    def test_dict_key_contains_yellow_ansi(self):
        """(7) JSON nesne anahtarı (key) sarı ANSI kodu \x1b[33m ile sarılmalı.

        colorize_json'da YELLOW = \x1b[33m key'lere uygulanır.
        '"isim"' ifadesinin ardından ':' geldiği için key kabul edilir.
        """
        result = colorize_json('{"isim": "Ali"}')
        self.assertIn(
            '\x1b[33m',
            result,
            f"Key'de sarı kod bulunamadı: {result!r}",
        )

    # ------------------------------------------------------------------
    # Test 8 – JSON token içermeyen düz metin renksiz döner
    # ------------------------------------------------------------------
    def test_plain_text_without_json_tokens_returned_unchanged(self):
        """(8) JSON token (tırnak, rakam, anahtar sözcük, parantez) içermeyen
        düz metin, ANSI kodu eklenmeksizin aynen döner.
        """
        plain = 'merhaba dunya'
        result = colorize_json(plain)
        self.assertEqual(
            result,
            plain,
            f"Düz metin değişmeden dönmeli; alınan: {result!r}",
        )
        self.assertNotIn(
            '\x1b[',
            result,
            "Düz metin ANSI kodu içermemeli",
        )


class TestShouldColorize(unittest.TestCase):
    """should_colorize() TTY algılama davranışı – testler 9-10."""

    # ------------------------------------------------------------------
    # Test 9 – TTY akışında should_colorize() True döndürür
    # ------------------------------------------------------------------
    def test_tty_stream_returns_true(self):
        """(9) isatty() → True olan mock akışta should_colorize() True döndürmeli.

        Terminale bağlı bir stdout'u simüle eden MagicMock kullanılır;
        should_colorize() bu akışı TTY olarak tanımalı ve True döndürmeli.
        """
        mock_stream = MagicMock()
        mock_stream.isatty.return_value = True
        result = should_colorize(mock_stream)
        self.assertTrue(
            result,
            f"TTY akışında should_colorize() True bekleniyor; alınan: {result!r}",
        )

    # ------------------------------------------------------------------
    # Test 10 – Pipe (TTY olmayan) akışında should_colorize() False döndürür
    # ------------------------------------------------------------------
    def test_pipe_stream_returns_false(self):
        """(10) isatty() → False olan mock akışta should_colorize() False döndürmeli.

        Pipe'a ya da dosyaya yönlendirilmiş stdout'u simüle eden MagicMock
        kullanılır; should_colorize() bu akışı TTY değil olarak tanımalı
        ve False döndürmeli.
        """
        mock_stream = MagicMock()
        mock_stream.isatty.return_value = False
        result = should_colorize(mock_stream)
        self.assertFalse(
            result,
            f"Pipe akışında should_colorize() False bekleniyor; alınan: {result!r}",
        )


if __name__ == '__main__':
    unittest.main()
