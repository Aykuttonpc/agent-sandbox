import unittest
import os
import tempfile
import pytest
from io import StringIO
from unittest.mock import patch
from json_formatter import JSONFormatter

class TestJSONFormatter(unittest.TestCase):

    def test_format_simple_object(self):
        """Test formatting a simple JSON object"""
        formatter = JSONFormatter()
        data = '{"name":"John","age":30}'
        result = formatter.format(data)
        expected = '{\n  "name": "John",\n  "age": 30\n}'
        self.assertEqual(result, expected)

    def test_format_with_custom_indent(self):
        """Test formatting with custom indentation"""
        formatter = JSONFormatter(indent=4)
        data = '{"key":"value"}'
        result = formatter.format(data)
        expected = '{\n    "key": "value"\n}'
        self.assertEqual(result, expected)

    def test_format_with_sort_keys(self):
        """Test formatting with sorted keys"""
        formatter = JSONFormatter(sort_keys=True)
        data = '{"z":"last","a":"first"}'
        result = formatter.format(data)
        expected = '{\n  "a": "first",\n  "z": "last"\n}'
        self.assertEqual(result, expected)

    def test_format_nested_object_and_array(self):
        """Test formatting nested object with array"""
        formatter = JSONFormatter()
        data = '{"user":{"name":"Alice","emails":["a@x.com","b@x.com"]},"count":2}'
        result = formatter.format(data)
        self.assertIn('"user"', result)
        self.assertIn('"emails"', result)
        self.assertIn('"a@x.com"', result)

    def test_format_array_of_objects(self):
        """Test formatting array of objects"""
        formatter = JSONFormatter()
        data = '[{"id":1,"name":"Item1"},{"id":2,"name":"Item2"}]'
        result = formatter.format(data)
        self.assertIn('"id": 1', result)
        self.assertIn('"name": "Item1"', result)

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises ValueError"""
        formatter = JSONFormatter()
        with self.assertRaises(ValueError):
            formatter.format('{invalid json}')

    def test_compact_mode_single_line_no_spaces(self):
        """compact=True ile çıktının tek satır ve boşluksuz olduğunu doğrula"""
        formatter = JSONFormatter(compact=True)
        data = '{"name": "John", "age": 30}'
        result = formatter.format(data)
        self.assertNotIn('\n', result)
        self.assertNotIn(' ', result)
        self.assertEqual(result, '{"name":"John","age":30}')

    def test_compact_mode_with_sort_keys(self):
        """compact=True ve sort_keys=True ile anahtarların sıralı tek satır üretildiğini doğrula"""
        formatter = JSONFormatter(compact=True, sort_keys=True)
        data = '{"z": "last", "a": "first"}'
        result = formatter.format(data)
        self.assertNotIn('\n', result)
        self.assertEqual(result, '{"a":"first","z":"last"}')

    def test_cli_compact_and_indent_mutually_exclusive(self):
        """CLI'da --compact ve --indent birlikte kullanılınca SystemExit fırlatılmalı"""
        from json_formatter.cli import main
        with patch('sys.argv', ['json-formatter', '--compact', '--indent', '2']):
            with self.assertRaises(SystemExit):
                main()

    # --- --in-place testleri ---

    def test_in_place_formats_valid_json_file(self):
        """Geçerli JSON içeren geçici dosya --in-place ile formatlanınca içerik güncellenmeli"""
        from json_formatter.cli import main
        raw = '{"b":2,"a":1}'
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            f.write(raw)
            tmp_path = f.name
        try:
            with patch('sys.argv', ['json-formatter', '--in-place', tmp_path]):
                main()
            with open(tmp_path, 'r') as f:
                content = f.read()
            self.assertIn('"b": 2', content)
            self.assertIn('"a": 1', content)
            self.assertIn('\n', content)
        finally:
            os.unlink(tmp_path)

    def test_in_place_with_stdin_exits_nonzero(self):
        """stdin modunda --in-place kullanılınca exit code != 0 alınmalı (parser.error → code 2)"""
        from json_formatter.cli import main
        with patch('sys.argv', ['json-formatter', '--in-place']):
            with self.assertRaises(SystemExit) as cm:
                main()
        self.assertNotEqual(cm.exception.code, 0)

    def test_in_place_invalid_json_preserves_original(self):
        """Geçersiz JSON + --in-place kombinasyonunda orijinal dosya içeriği bozulmamalı"""
        from json_formatter.cli import main
        original = '{invalid json}'
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            f.write(original)
            tmp_path = f.name
        try:
            with patch('sys.argv', ['json-formatter', '--in-place', tmp_path]):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 1)
            with open(tmp_path, 'r') as f:
                content = f.read()
            self.assertEqual(content, original)
        finally:
            os.unlink(tmp_path)

    # --- --check testleri ---

    def test_check_already_formatted_file_exits_0(self):
        """Zaten formatlanmış dosya --check ile exit 0 döndürmeli"""
        from json_formatter.cli import main
        formatter = JSONFormatter()
        raw = '{"name":"John","age":30}'
        formatted = formatter.format(raw)
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            f.write(formatted)
            tmp_path = f.name
        try:
            with patch('sys.argv', ['json-formatter', '--check', tmp_path]):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 0)
        finally:
            os.unlink(tmp_path)

    def test_check_unformatted_file_exits_1_with_stderr(self):
        """Formatlanmamış dosya --check ile exit 1 ve stderr 'not formatted' mesajı döndürmeli"""
        from json_formatter.cli import main
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            f.write('{"b":2,"a":1}')
            tmp_path = f.name
        try:
            with patch('sys.argv', ['json-formatter', '--check', tmp_path]):
                with patch('sys.stderr', new_callable=StringIO) as mock_err:
                    with self.assertRaises(SystemExit) as cm:
                        main()
                    self.assertEqual(cm.exception.code, 1)
                    self.assertIn('not formatted', mock_err.getvalue())
        finally:
            os.unlink(tmp_path)

    def test_check_invalid_json_exits_1(self):
        """Geçersiz JSON + --check kombinasyonunda exit 1 alınmalı"""
        from json_formatter.cli import main
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            f.write('{invalid json}')
            tmp_path = f.name
        try:
            with patch('sys.argv', ['json-formatter', '--check', tmp_path]):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 1)
        finally:
            os.unlink(tmp_path)

    def test_check_with_in_place_exits_2_argparse_error(self):
        """--check --in-place birlikte verilince argparse mutually exclusive hatası (exit 2) vermeli"""
        from json_formatter.cli import main
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            f.write('{"b":2,"a":1}')
            tmp_path = f.name
        try:
            with patch('sys.argv', ['json-formatter', '--check', '--in-place', tmp_path]):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        finally:
            os.unlink(tmp_path)

    def test_check_with_stdin_exits_2_with_error(self):
        """stdin + --check kombinasyonunda exit 2 ve stderr'de hata mesajı olmalı"""
        from json_formatter.cli import main
        with patch('sys.argv', ['json-formatter', '--check']):
            with patch('sys.stderr', new_callable=StringIO) as mock_err:
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 2)
                self.assertIn('--check requires a file argument, not stdin', mock_err.getvalue())

    # --- sort_keys yeni testleri ---

    def test_sort_keys_orders_keys_alphabetically(self):
        """sort_keys=True ile {"b": 1, "a": 2} girdisinde anahtarlar alfabetik sırada çıkmalı"""
        from json_formatter import format_json
        data = '{"b": 1, "a": 2}'
        result = format_json(data, sort_keys=True)
        self.assertLess(result.index('"a"'), result.index('"b"'))
        self.assertIn('"a": 2', result)
        self.assertIn('"b": 1', result)

    def test_compact_and_sort_keys_single_line_sorted(self):
        """compact=True, sort_keys=True birlikte tek satır ve sıralı anahtar üretmeli"""
        from json_formatter import format_json
        data = '{"b": 1, "a": 2}'
        result = format_json(data, compact=True, sort_keys=True)
        self.assertNotIn('\n', result)
        self.assertEqual(result, '{"a":2,"b":1}')

    def test_in_place_sort_keys_writes_sorted_json(self):
        """--in-place --sort-keys atomik yazma yolundan geçerek sıralı JSON yazdırmalı"""
        from json_formatter.cli import main
        raw = '{"b": 1, "a": 2}'
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            f.write(raw)
            tmp_path = f.name
        try:
            with patch('sys.argv', ['json-formatter', '--in-place', '--sort-keys', tmp_path]):
                main()
            with open(tmp_path, 'r') as f:
                content = f.read()
            self.assertLess(content.index('"a"'), content.index('"b"'))
            self.assertIn('\n', content)
            self.assertIn('"a": 2', content)
            self.assertIn('"b": 1', content)
        finally:
            os.unlink(tmp_path)

    def test_sort_keys_a_before_b_with_compact_input(self):
        """(1) format_json('{"b":2,"a":1}', sort_keys=True) çıktısında 'a' anahtarı 'b'den önce gelmeli"""
        from json_formatter import format_json
        result = format_json('{"b":2,"a":1}', sort_keys=True)
        self.assertLess(result.index('"a"'), result.index('"b"'))

    def test_sort_keys_compact_no_spaces_sorted_output(self):
        """(2) format_json('{"b":2,"a":1}', sort_keys=True, compact=True) → '{"a":1,"b":2}' (boşluksuz, sıralı)"""
        from json_formatter import format_json
        result = format_json('{"b":2,"a":1}', sort_keys=True, compact=True)
        self.assertEqual(result, '{"a":1,"b":2}')

    # --- --unicode / ensure_ascii testleri ---

    def test_ensure_ascii_default_escapes_non_ascii(self):
        """ensure_ascii=True (varsayılan) ile 'ü' karakteri \\u00fc olarak escape edilmeli"""
        from json_formatter import format_json
        data = '{"key": "ü"}'
        result = format_json(data)
        self.assertIn('\\u00fc', result)
        self.assertNotIn('ü', result)

    def test_ensure_ascii_false_preserves_unicode(self):
        """ensure_ascii=False ile 'ü' karakteri olduğu gibi korunmalı"""
        from json_formatter import format_json
        data = '{"key": "ü"}'
        result = format_json(data, ensure_ascii=False)
        self.assertIn('ü', result)
        self.assertNotIn('\\u00fc', result)

    # --- çoklu dosya testleri ---

    def test_no_args_reads_from_stdin(self):
        """Argümansız çağrıda stdin'den okuyup stdout'a yazmalı (regression)"""
        from json_formatter.cli import main
        input_data = '{"x":1}'
        with patch('sys.argv', ['json-formatter']):
            with patch('sys.stdin', StringIO(input_data)):
                with patch('sys.stdout', new_callable=StringIO) as mock_out:
                    main()
                    output = mock_out.getvalue()
        self.assertIn('"x": 1', output)

    def test_in_place_two_valid_files(self):
        """--in-place iki geçerli dosyada her ikisi de bağımsız formatlanmalı"""
        from json_formatter.cli import main
        files = []
        try:
            for raw in ['{"b":1,"a":2}', '{"z":9}']:
                f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
                f.write(raw)
                f.close()
                files.append(f.name)
            with patch('sys.argv', ['json-formatter', '--in-place'] + files):
                main()
            with open(files[0]) as f:
                c1 = f.read()
            with open(files[1]) as f:
                c2 = f.read()
            self.assertIn('\n', c1)
            self.assertIn('"b": 1', c1)
            self.assertIn('\n', c2)
            self.assertIn('"z": 9', c2)
        finally:
            for fp in files:
                if os.path.exists(fp):
                    os.unlink(fp)

    def test_in_place_one_invalid_skips_and_exits_1(self):
        """--in-place biri geçersiz JSON iken hatalı atlanır, geçerli yazılır, exit 1 döner"""
        from json_formatter.cli import main
        files = []
        try:
            for raw in ['{bad json}', '{"ok":true}']:
                f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
                f.write(raw)
                f.close()
                files.append(f.name)
            with patch('sys.argv', ['json-formatter', '--in-place'] + files):
                with patch('sys.stderr', new_callable=StringIO) as mock_err:
                    with self.assertRaises(SystemExit) as cm:
                        main()
                    self.assertEqual(cm.exception.code, 1)
                    self.assertIn('Invalid JSON', mock_err.getvalue())
            with open(files[0]) as f:
                self.assertEqual(f.read(), '{bad json}')
            with open(files[1]) as f:
                content = f.read()
            self.assertIn('\n', content)
            self.assertIn('"ok": true', content)
        finally:
            for fp in files:
                if os.path.exists(fp):
                    os.unlink(fp)

    def test_check_mixed_ok_fail_two_files(self):
        """--check karışık dosyalarda OK/FAIL stdout'a yazdırılmalı, exit 1 dönmeli"""
        from json_formatter.cli import main
        formatter = JSONFormatter()
        unformatted = '{"b":2,"a":1}'
        formatted = formatter.format(unformatted)
        files = []
        try:
            f1 = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
            f1.write(formatted)
            f1.close()
            files.append(f1.name)
            f2 = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
            f2.write(unformatted)
            f2.close()
            files.append(f2.name)
            with patch('sys.argv', ['json-formatter', '--check'] + files):
                with patch('sys.stdout', new_callable=StringIO) as mock_out:
                    with self.assertRaises(SystemExit) as cm:
                        main()
                    output = mock_out.getvalue()
            self.assertEqual(cm.exception.code, 1)
            self.assertIn('OK:', output)
            self.assertIn('FAIL:', output)
        finally:
            for fp in files:
                if os.path.exists(fp):
                    os.unlink(fp)

    def test_stdout_mode_two_files_exits_1(self):
        """Stdout modunda 2 dosya verilince stderr'e hata yazıp exit 1 dönmeli"""
        from json_formatter.cli import main
        files = []
        try:
            for raw in ['{"a":1}', '{"b":2}']:
                f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
                f.write(raw)
                f.close()
                files.append(f.name)
            with patch('sys.argv', ['json-formatter'] + files):
                with patch('sys.stderr', new_callable=StringIO) as mock_err:
                    with self.assertRaises(SystemExit) as cm:
                        main()
                    self.assertEqual(cm.exception.code, 1)
                    self.assertIn('stdout mode', mock_err.getvalue())
        finally:
            for fp in files:
                if os.path.exists(fp):
                    os.unlink(fp)

    # --- compact parametresi: format_json() üzerinden testler ---

    def test_format_json_compact_no_spaces(self):
        """format_json: compact=True ile {"a": 1} → {"a":1} (boşluk yok)"""
        from json_formatter import format_json
        result = format_json('{"a": 1}', compact=True)
        self.assertEqual(result, '{"a":1}')

    def test_format_json_compact_overrides_indent(self):
        """format_json: compact=True, indent=4 birlikte verildiğinde çıktı tek satır boşluksuz olmalı"""
        from json_formatter import format_json
        result = format_json('{"a": 1}', compact=True, indent=4)
        self.assertNotIn('\n', result)
        self.assertNotIn(' ', result)
        self.assertEqual(result, '{"a":1}')

    # --- colorize_json testleri (nesne tabanlı yeni API) ---

    def test_colorize_string_value_wrapped_with_green_ansi(self):
        """(a) String değer yeşil ANSI koduyla (\033[32m) sarılmalı"""
        from json_formatter.formatter import colorize_json
        obj = {"name": "John"}
        result = colorize_json(obj)
        self.assertIn('\033[32m"John"\033[0m', result)

    def test_colorize_number_value_wrapped_with_cyan_ansi(self):
        """(b) Sayı değer cyan ANSI koduyla (\033[36m) sarılmalı"""
        from json_formatter.formatter import colorize_json
        obj = {"age": 30}
        result = colorize_json(obj)
        self.assertIn('\033[36m30\033[0m', result)

    def test_colorize_key_wrapped_with_yellow_ansi(self):
        """(c) Dict anahtarı sarı ANSI koduyla (\033[33m) sarılmalı"""
        from json_formatter.formatter import colorize_json
        obj = {"name": "John"}
        result = colorize_json(obj)
        self.assertIn('\033[33m"name"\033[0m', result)


# --- Bağımsız pytest testleri ---

def test_invalid_json_error_message_contains_location():
    from json_formatter import format_json
    with pytest.raises(ValueError) as exc_info:
        format_json("{invalid")
    msg = str(exc_info.value)
    assert "line" in msg and "column" in msg


def test_version_flag(capsys):
    """--version bayrağı: exit kodu 0 olmalı ve __version__ stdout'ta görünmeli."""
    from json_formatter.cli import main
    from json_formatter import __version__
    with patch('sys.argv', ['json-formatter', '--version']):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out


# --- compact parametresi ve mutually exclusive grup testleri ---

def test_compact_true_no_space_no_newline():
    """format_json('{"a":1}', compact=True) çıktısı ' ' ve '\\n' içermemeli."""
    from json_formatter import format_json
    result = format_json('{"a":1}', compact=True)
    assert ' ' not in result
    assert '\n' not in result


def test_compact_false_preserves_default_behavior():
    """format_json('{"a":1}', compact=False) varsayılan davranışı bozmamalı."""
    from json_formatter import format_json
    result_explicit = format_json('{"a":1}', compact=False)
    result_default = format_json('{"a":1}')
    assert result_explicit == result_default
    assert '\n' in result_explicit


def test_compact_color_integration_no_newline():
    """compact=True çıktısına colorize_json uygulandığında sonuç '\\n' içermemeli."""
    from json_formatter import format_json
    from json_formatter.formatter import colorize_json
    import json
    compact_result = format_json('{"a":1}', compact=True)
    assert '\n' not in compact_result
    # Compact string'i parse ederek colorize_json'a nesne olarak geçir
    colored = colorize_json(json.loads(compact_result))
    assert '\n' not in colored


def test_build_parser_compact_and_indent_mutually_exclusive_exits_2():
    """build_parser().parse_args(['--compact', '--indent', '4']) → SystemExit(2) fırlatmalı."""
    from json_formatter.cli import build_parser
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(['--compact', '--indent', '4'])
    assert exc_info.value.code == 2


# --- is_already_formatted testleri (5 yeni test) ---

def test_is_already_formatted_formatted_json_returns_true():
    """(1) Formatlanmış JSON içeriği → is_already_formatted True döndürmeli."""
    from json_formatter.formatter import is_already_formatted
    from json_formatter import format_json
    raw = '{"name":"John","age":30}'
    formatted = format_json(raw)
    assert is_already_formatted(formatted) is True


def test_is_already_formatted_unformatted_json_returns_false():
    """(2) Formatlanmamış (kompakt) JSON içeriği → is_already_formatted False döndürmeli."""
    from json_formatter.formatter import is_already_formatted
    assert is_already_formatted('{"b":2,"a":1}') is False


def test_is_already_formatted_invalid_json_returns_false():
    """(3) Geçersiz JSON içeriği → is_already_formatted ValueError yakaladığından False döndürmeli."""
    from json_formatter.formatter import is_already_formatted
    assert is_already_formatted('{invalid json}') is False


def test_is_already_formatted_compact_mode_true_and_false():
    """(4) compact=True ile formatlanmış kompakt girdi → True; compact=False ile aynı girdi → False."""
    from json_formatter.formatter import is_already_formatted
    compact_input = '{"a":1,"b":2}'
    assert is_already_formatted(compact_input, compact=True) is True
    assert is_already_formatted(compact_input, compact=False) is False


def test_check_subprocess_unformatted_file_exits_1_stderr_not_formatted():
    """(5) subprocess --check ile formatlanmamış dosyada returncode==1, stderr 'not formatted' içermeli."""
    import sys
    import subprocess
    import tempfile
    import os
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        f.write('{"b":2,"a":1}')
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--check', tmp_path],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert 'not formatted' in result.stderr
    finally:
        os.unlink(tmp_path)


# --- unicode parametresi testleri ---

def test_unicode_false_default_escapes_non_ascii():
    """unicode=False (varsayılan) ile '{"key": "değer"}' girdisindeki non-ASCII karakterler \\u kaçışına dönüşmeli."""
    from json_formatter import format_json
    data = '{"key": "değer"}'
    result = format_json(data, unicode=False)
    assert '\\u' in result
    assert 'değer' not in result


def test_unicode_true_preserves_non_ascii():
    """unicode=True ile '{"key": "değer"}' girdisindeki 'değer' string'i olduğu gibi korunmalı."""
    from json_formatter import format_json
    data = '{"key": "değer"}'
    result = format_json(data, unicode=True)
    assert 'değer' in result


# --- colorize_json yeni testleri (nesne tabanlı API) ---

def test_colorize_json_key_contains_yellow():
    """(1) Dict anahtarı sarı renk kodunu (\033[33m) içermeli."""
    from json_formatter.formatter import colorize_json
    result = colorize_json({"yas": 25})
    assert "\033[33m" in result


def test_colorize_json_number_contains_cyan():
    """(2) Sayı değer cyan renk kodunu (\033[36m) içermeli."""
    from json_formatter.formatter import colorize_json
    result = colorize_json({"sayi": 42})
    assert "\033[36m" in result


def test_colorize_json_every_color_block_has_reset():
    """(3) Her renk bloğunun ardından \033[0m reset kodu gelmeli."""
    import re
    from json_formatter.formatter import colorize_json
    obj = {"isim": "Ali", "yas": 30, "aktif": True, "veri": None}
    result = colorize_json(obj)
    # Tüm ANSI kodlarını bul
    all_codes = re.findall(r'\033\[\d+m', result)
    open_codes = [c for c in all_codes if c != '\033[0m']
    resets     = [c for c in all_codes if c == '\033[0m']
    assert len(open_codes) == len(resets), (
        f"Açık renk kodu sayısı ({len(open_codes)}) reset sayısıyla ({len(resets)}) eşleşmiyor"
    )


# ============================================================
# YENİ TESTLER: --in-place iyileştirmeleri (tmp_path fixture)
# ============================================================

def test_in_place_formats_file_correctly_tmp_path(tmp_path):
    """
    (1) tmp_path fixture ile geçici dosyanın içeriği --in-place sonrası
    doğru biçimlendirilmeli: girintili, anahtarlar ve değerler korunmalı.
    """
    from json_formatter.cli import main
    json_file = tmp_path / "sample.json"
    json_file.write_text('{"b":2,"a":1}')
    with patch('sys.argv', ['json-formatter', '--in-place', str(json_file)]):
        main()
    content = json_file.read_text()
    assert '"b": 2' in content
    assert '"a": 1' in content
    assert '\n' in content


def test_in_place_without_file_exits_nonzero_pytest(tmp_path):
    """
    (2) --in-place stdin ile (dosyasız) kullanıldığında exit code != 0 olmalı.
    parser.error() kullanıldığından argparse exit code 2 verir.
    """
    from json_formatter.cli import main
    with patch('sys.argv', ['json-formatter', '--in-place']):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code != 0


def test_in_place_and_check_mutually_exclusive_exits_2(tmp_path):
    """
    (3) --in-place --check birlikte kullanıldığında argparse mutually exclusive
    grubu devreye girerek exit code 2 ile hata vermeli.
    """
    from json_formatter.cli import main
    json_file = tmp_path / "data.json"
    json_file.write_text('{"a":1}')
    with patch('sys.argv', ['json-formatter', '--in-place', '--check', str(json_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 2


if __name__ == '__main__':
    unittest.main()
