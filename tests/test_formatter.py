import unittest
import os
import tempfile
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
            # Formatlanmış çıktı girintili olmalı
            self.assertIn('"b": 2', content)
            self.assertIn('"a": 1', content)
            self.assertIn('\n', content)
        finally:
            os.unlink(tmp_path)

    def test_in_place_with_stdin_exits_code_1(self):
        """stdin modunda --in-place kullanılınca exit code 1 alınmalı"""
        from json_formatter.cli import main
        with patch('sys.argv', ['json-formatter', '--in-place']):
            with self.assertRaises(SystemExit) as cm:
                main()
        self.assertEqual(cm.exception.code, 1)

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
            # Orijinal içerik değişmemiş olmalı
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
        """Formatlanmamış dosya --check ile exit 1 ve stderr mesajı döndürmeli"""
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
                    self.assertIn('File is not formatted', mock_err.getvalue())
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

    def test_check_with_in_place_file_unchanged_and_warning(self):
        """--check --in-place birlikte verilince dosya değişmemeli ve stderr'de uyarı olmalı"""
        from json_formatter.cli import main
        original = '{"b":2,"a":1}'
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            f.write(original)
            tmp_path = f.name
        try:
            with patch('sys.argv', ['json-formatter', '--check', '--in-place', tmp_path]):
                with patch('sys.stderr', new_callable=StringIO) as mock_err:
                    with self.assertRaises(SystemExit):
                        main()
                    stderr_output = mock_err.getvalue()
            self.assertIn('Warning: --in-place ignored when --check is active', stderr_output)
            with open(tmp_path, 'r') as f:
                content = f.read()
            self.assertEqual(content, original)
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
        # "a" anahtarı çıktıda "b"den önce gelmelidir
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
            # Anahtarlar alfabetik sırada olmalı: "a" önce, "b" sonra
            self.assertLess(content.index('"a"'), content.index('"b"'))
            self.assertIn('\n', content)
            self.assertIn('"a": 2', content)
            self.assertIn('"b": 1', content)
        finally:
            os.unlink(tmp_path)

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

    # --- çoklu dosya testleri (5 yeni test) ---

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
                main()  # başarılı → SystemExit yok
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
            # İlk dosya geçersiz JSON, ikinci dosya geçerli
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
            # Geçersiz dosya değişmemiş olmalı
            with open(files[0]) as f:
                self.assertEqual(f.read(), '{bad json}')
            # Geçerli dosya formatlanmış olmalı
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
            # İlk dosya zaten formatlanmış → OK bekleniyor
            f1 = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
            f1.write(formatted)
            f1.close()
            files.append(f1.name)
            # İkinci dosya formatlanmamış → FAIL bekleniyor
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

if __name__ == '__main__':
    unittest.main()
