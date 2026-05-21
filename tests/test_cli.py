import subprocess
import json
import tempfile
import os
import sys
import unittest
import pytest


# ---------------------------------------------------------------------------
# subprocess tabanlı Click CliRunner uyumlu sarıcı
# CLI argparse kullandığı için Click bağımlılığı olmadan aynı arayüzü sunar.
# ---------------------------------------------------------------------------
class _CliRunner:
    class _Result:
        def __init__(self, returncode):
            self.exit_code = returncode

    def invoke(self, _cli, args):
        r = subprocess.run(
            [sys.executable, '-m', 'json_formatter'] + args,
            capture_output=True
        )
        return self._Result(r.returncode)


# cli parametresi _CliRunner.invoke içinde kullanılmaz; yalnızca arayüz uyumu için.
cli = None


class TestCLIVersion:
    """--version flag'ini test et."""

    def test_version_flag(self):
        """--version flag'ı sürüm numarasını stdout veya stderr'da göstermeli ve exit code 0 döndürmeli."""
        from json_formatter import __version__
        result = subprocess.run(
            ["json-formatter", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"--version için exit code 0 bekleniyor; alınan: {result.returncode}"
        )
        combined = result.stdout + result.stderr
        assert __version__ in combined, (
            f"Sürüm numarası '{__version__}' çıktıda bekleniyor; alınan: {repr(combined)}"
        )


class TestCLISortKeys:
    """--sort-keys flag'ini stdin ve dosya argumentında test et."""

    def test_sort_keys_stdin(self):
        """stdin üzerinden --sort-keys flag'ini test et."""
        input_json = '{"z":1,"a":2}'
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--sort-keys'],
            input=input_json,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        output = result.stdout.strip()
        output_json = json.loads(output)
        keys = list(output_json.keys())
        assert keys == ['a', 'z'], f"Expected ['a', 'z'], got {keys}"

    def test_sort_keys_file(self):
        """Dosya argumentı üzerinden --sort-keys flag'ini test et."""
        input_json = '{"z":1,"a":2}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(input_json)
            temp_path = f.name
        try:
            result = subprocess.run(
                ['python', '-m', 'json_formatter', '--sort-keys', temp_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            output = result.stdout.strip()
            output_json = json.loads(output)
            keys = list(output_json.keys())
            assert keys == ['a', 'z'], f"Expected ['a', 'z'], got {keys}"
        finally:
            os.unlink(temp_path)

    def test_sort_keys_nested_object_stdin(self):
        """Nested object'in anahtarlarını --sort-keys ile sırala (stdin)."""
        input_json = '{"outer":{"z":1,"a":2}}'
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--sort-keys'],
            input=input_json,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        output = result.stdout.strip()
        output_json = json.loads(output)
        outer_keys = list(output_json.keys())
        assert outer_keys == ['outer']
        inner_keys = list(output_json['outer'].keys())
        assert inner_keys == ['a', 'z'], f"Expected ['a', 'z'] for nested keys, got {inner_keys}"

    def test_sort_keys_nested_object_file(self):
        """Nested object'in anahtarlarını --sort-keys ile sırala (dosya)."""
        input_json = '{"outer":{"z":1,"a":2}}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(input_json)
            temp_path = f.name
        try:
            result = subprocess.run(
                ['python', '-m', 'json_formatter', '--sort-keys', temp_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            output = result.stdout.strip()
            output_json = json.loads(output)
            outer_keys = list(output_json.keys())
            assert outer_keys == ['outer']
            inner_keys = list(output_json['outer'].keys())
            assert inner_keys == ['a', 'z'], f"Expected ['a', 'z'] for nested keys, got {inner_keys}"
        finally:
            os.unlink(temp_path)

    def test_sort_keys_file_nested(self):
        """nested.json'ı --sort-keys ile formatla; tüm seviyelerde anahtarlar sıralı olmalı."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', 'tests/data/nested.json', '--sort-keys'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert list(output.keys()) == sorted(output.keys())
        assert list(output['app'].keys()) == sorted(output['app'].keys())
        assert list(output['app']['config'].keys()) == sorted(output['app']['config'].keys())
        for user in output['users']:
            assert list(user['settings'].keys()) == sorted(user['settings'].keys())

    def test_sort_keys_without_flag_preserves_order_stdin(self):
        """--sort-keys olmadan giriş sırası korunmalı (stdin)."""
        input_json = '{"z":1,"a":2}'
        result = subprocess.run(
            ['python', '-m', 'json_formatter'],
            input=input_json,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        output = result.stdout.strip()
        assert '"z"' in output and '"a"' in output


class TestCLICheckMode:
    """--check flag'i ile is_formatted() entegrasyonunu test et."""

    def test_check_formatted_file_returns_exit_0(self):
        """Formatlanmış dosya --check ile exit code 0 ve 'Already formatted' döndürmeli."""
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--check', 'tests/data/formatted.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Already formatted" in result.stdout

    def test_check_unformatted_file_returns_exit_1(self):
        """Formatlanmamış dosya --check ile exit code 1 döndürmeli."""
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--check', 'tests/data/unformatted.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "File is not formatted" in result.stdout

    def test_check_flag_file_not_formatted(self):
        """--check flag'ı biçimlendirilmemiş dosya için exit 1 ve stdout'a 'File is not formatted' döndürmeli."""
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--check', 'tests/data/unformatted.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "File is not formatted" in result.stdout

    def test_check_invalid_json_file_returns_exit_1(self):
        """Geçersiz JSON dosyası --check ile exit code 1 ve stderr'da 'satır'/'sütun' içeren mesaj döndürmeli."""
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--check', 'tests/data/invalid.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "satır" in result.stderr
        assert "sütun" in result.stderr


class TestCLICheck:
    """--check flag'i için 5 temel senaryo testi."""

    def test_check_stdin_exit_2(self):
        """(1) stdin + --check → exit 2, stderr'da hata mesajı."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--check'],
            input='{"a":1}',
            capture_output=True,
            text=True
        )
        assert result.returncode == 2
        assert result.stderr.strip() != ""

    def test_check_invalid_json_exit_1(self):
        """(2) Geçersiz JSON + --check → exit 1, stderr'da mesaj."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--check', 'tests/data/invalid.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert result.stderr.strip() != ""

    def test_check_formatted_json_exit_0_already_formatted(self):
        """(3) formatted.json + --check → exit 0 + stdout'a 'Already formatted'."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--check', 'tests/data/formatted.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Already formatted" in result.stdout

    def test_check_unformatted_json_exit_1_file_is_not_formatted(self):
        """(4) unformatted.json + --check → exit 1 + stdout'a 'File is not formatted'."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--check', 'tests/data/unformatted.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "File is not formatted" in result.stdout

    def test_check_and_in_place_exit_2(self):
        """(5) --check + --in-place → exit 2, stderr'da 'Bu iki flag birlikte kullanılamaz'."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"a": 1}')
            temp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'json_formatter', '--check', '--in-place', temp_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 2
            assert "Bu iki flag birlikte kullanılamaz" in result.stderr
        finally:
            os.unlink(temp_path)


class TestCLIInvalidJSON:
    """Invalid JSON dosyası ile test et."""

    def test_cli_invalid_json_exit_code(self):
        """Invalid JSON dosyası ile çalıştır, returncode==1 ve stderr'da 'satır'/'sütun' mesajı assert et."""
        result = subprocess.run(
            ['python', '-m', 'json_formatter', 'tests/data/invalid.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "satır" in result.stderr
        assert "sütun" in result.stderr


class TestCLIInPlace(unittest.TestCase):
    """--in-place flag'ini atomik yazma ile test et."""

    def setUp(self):
        self.runner = _CliRunner()

    def test_cli_in_place_successful_write(self):
        """--in-place ile başarılı yazma: dosya formatlanmış olmalı."""
        unformatted_json = '{"z":1,"a":2}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(unformatted_json)
            temp_path = f.name
        try:
            result = subprocess.run(
                ['python', '-m', 'json_formatter', '--in-place', temp_path],
                capture_output=True, text=True
            )
            assert result.returncode == 0
            with open(temp_path, 'r') as f:
                content = f.read()
            parsed = json.loads(content)
            assert parsed == {"z": 1, "a": 2}
            assert '  ' in content
        finally:
            os.unlink(temp_path)

    def test_cli_in_place_format_error_preserves_original(self):
        """Format hatası durumunda orijinal dosya korunmalı."""
        invalid_json = '{"z":1,"a":2'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(invalid_json)
            temp_path = f.name
        try:
            result = subprocess.run(
                ['python', '-m', 'json_formatter', '--in-place', temp_path],
                capture_output=True, text=True
            )
            assert result.returncode == 1
            assert "satır" in result.stderr
            assert "sütun" in result.stderr
            with open(temp_path, 'r') as f:
                content = f.read()
            assert content == invalid_json
        finally:
            os.unlink(temp_path)

    def test_cli_in_place_without_file_argument_error(self):
        """--in-place dosya argümanı olmadan kullanılamaz."""
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--in-place'],
            input='{"a":1}',
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "--in-place requires a file argument" in result.stderr

    def test_cli_in_place_with_sort_keys(self):
        """--in-place ile --sort-keys birlikte çalışmalı."""
        unformatted_json = '{"z":1,"a":2}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(unformatted_json)
            temp_path = f.name
        try:
            result = subprocess.run(
                ['python', '-m', 'json_formatter', '--in-place', '--sort-keys', temp_path],
                capture_output=True, text=True
            )
            assert result.returncode == 0
            with open(temp_path, 'r') as f:
                content = f.read()
            parsed = json.loads(content)
            assert list(parsed.keys()) == ['a', 'z']
        finally:
            os.unlink(temp_path)

    def test_cli_in_place_nonexistent_file_error(self):
        """Var olmayan dosya ile --in-place hata döndürmeli."""
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--in-place', '/nonexistent/path/file.json'],
            capture_output=True, text=True
        )
        assert result.returncode == 1
        assert "Error" in result.stderr

    def test_cli_in_place_multiple_files(self):
        """--in-place birden fazla dosyayı işleyebilmeli."""
        unformatted_json1 = '{"b":2,"a":1}'
        unformatted_json2 = '{"y":3,"x":4}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
            f1.write(unformatted_json1)
            temp_path1 = f1.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            f2.write(unformatted_json2)
            temp_path2 = f2.name
        try:
            result = subprocess.run(
                ['python', '-m', 'json_formatter', '--in-place', temp_path1, temp_path2],
                capture_output=True, text=True
            )
            assert result.returncode == 0
            with open(temp_path1, 'r') as f:
                content1 = f.read()
            with open(temp_path2, 'r') as f:
                content2 = f.read()
            assert json.loads(content1) == {"b": 2, "a": 1}
            assert json.loads(content2) == {"y": 3, "x": 4}
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)

    def test_in_place_invalid_json_leaves_file_unchanged(self):
        original_content = b'{"key": invalid}'
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(original_content)
            tmp_name = f.name
        try:
            result = self.runner.invoke(cli, ['--in-place', tmp_name])
            self.assertEqual(result.exit_code, 1)
            with open(tmp_name, 'rb') as f:
                self.assertEqual(f.read(), original_content)
        finally:
            os.unlink(tmp_name)


class TestCLICompactFlag:
    """--compact flag'i ile boşluksuz JSON çıktısını test et."""

    def test_compact_basic_functionality(self):
        """--compact flag'ı ile boşluksuz JSON üretmeyi test et."""
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--compact', 'tests/data/sample.json'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        output = result.stdout.strip()
        parsed = json.loads(output)
        assert parsed is not None
        assert '\n' not in output, f"Output contains newlines: {repr(output)}"
        assert not output.startswith(' '), "Output starts with space (has indentation)"
        assert not output.startswith('\t'), "Output starts with tab (has indentation)"

    def test_compact_with_sort_keys(self):
        """--compact --sort-keys kombinasyonu ile boşluksuz ve sıralanmış JSON üretmeyi test et."""
        def is_keys_sorted_recursive(obj):
            if isinstance(obj, dict):
                keys = list(obj.keys())
                if keys != sorted(keys):
                    return False
                for value in obj.values():
                    if not is_keys_sorted_recursive(value):
                        return False
                return True
            elif isinstance(obj, list):
                for item in obj:
                    if not is_keys_sorted_recursive(item):
                        return False
                return True
            return True

        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--compact', '--sort-keys', 'tests/data/sample.json'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        output = result.stdout.strip()
        parsed = json.loads(output)
        assert parsed is not None
        assert is_keys_sorted_recursive(parsed), f"Parsed object has unsorted keys: {parsed}"


class TestCLITabFlag:
    """--tab flag'i ile tab karakteri girinti içerikli JSON çıktısını test et."""

    def test_cli_tab_stdin(self):
        """stdin üzerinden --tab flag'ini test et."""
        input_json = '{"name":"John","age":30}'
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--tab'],
            input=input_json,
            capture_output=True, text=True
        )
        assert result.returncode == 0
        output = result.stdout.strip()
        parsed = json.loads(output)
        assert parsed is not None
        assert '\t' in output, f"Output does not contain tab character: {repr(output)}"
        lines = output.split('\n')
        for line in lines:
            if line and line[0] == ' ':
                assert False, f"Line indented with space instead of tab: {repr(line)}"

    def test_cli_tab_file(self):
        """Dosya argumentı üzerinden --tab flag'ini test et."""
        input_json = '{"name":"John","age":30}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(input_json)
            temp_path = f.name
        try:
            result = subprocess.run(
                ['python', '-m', 'json_formatter', '--tab', temp_path],
                capture_output=True, text=True
            )
            assert result.returncode == 0
            output = result.stdout.strip()
            parsed = json.loads(output)
            assert parsed is not None
            assert '\t' in output, f"Output does not contain tab character: {repr(output)}"
            lines = output.split('\n')
            for line in lines:
                if line and line[0] == ' ':
                    assert False, f"Line indented with space instead of tab: {repr(line)}"
        finally:
            os.unlink(temp_path)


class TestCLIColor:
    """--color / --no-color flag'lerini ve colorize_json davranışını test et."""

    def test_no_color_strips_ansi(self):
        """--no-color verildiğinde çıktıda hiç ANSI escape kodu bulunmamalı."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--no-color'],
            input='{"key": true}',
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert '\x1b[' not in result.stdout, (
            f"--no-color ile ANSI kodu beklenmiyor; stdout: {repr(result.stdout)}"
        )

    def test_color_force_produces_ansi(self):
        """--color verildiğinde TTY kontrolü olmaksızın çıktıda ANSI escape kodu bulunmalı."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--color'],
            input='{"key": true}',
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert '\x1b[' in result.stdout, (
            f"--color ile ANSI kodu bekleniyor; stdout: {repr(result.stdout)}"
        )

    def test_color_string_value_containing_true(self):
        """String value içindeki 'true' kelimesi string rengi (yeşil \x1b[32m) almalı,
        boolean rengi (mavi \x1b[34m) almamalı."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--color'],
            input='{"flag": "true"}',
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        stdout = result.stdout
        # "true" string value olarak yeşil (\x1b[32m) renkte, tırnaklarıyla birlikte görünmeli
        assert '\x1b[32m"true"\x1b[0m' in stdout, (
            f'Yeşil renkte "true" bekleniyor; stdout: {repr(stdout)}'
        )
        # Çıplak boolean token'ı olarak mavi (\x1b[34m) görünmemeli
        assert '\x1b[34mtrue\x1b[0m' not in stdout, (
            f'Mavi renkte çıplak true beklenmiyor; stdout: {repr(stdout)}'
        )

    def test_explicit_color_flag_overrides_non_tty_detection(self):
        """--color açıkça verilince TTY-olmayan (pipe) ortamda dahi ANSI kodları üretilmeli.

        capture_output=True, subprocess stdout'unu bir pipe'a bağlar; bu nedenle
        süreç içinde should_colorize() → False döndürür. Ancak --color açıkça
        verildiği için args.color is not None (True) koşulu sağlanır ve
        should_colorize() devre dışı kalır; çıktı ANSI kodları içermelidir.
        """
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--color'],
            input='{"a": 1, "b": true}',
            capture_output=True,   # stdout pipe → isatty() = False
            text=True
        )
        assert result.returncode == 0
        # --color açıkça verildi; pipe olmasına rağmen ANSI kodu görünmeli
        assert '\x1b[' in result.stdout, (
            f"TTY-olmayan pipe ortamında --color ile ANSI kodu bekleniyor; "
            f"stdout: {repr(result.stdout)}"
        )


class TestCLIErrors:
    """Hatalı giriş senaryolarını test et: var olmayan dosya ve negatif --indent."""

    def test_nonexistent_file_exit_1(self):
        """(1) Var olmayan dosya yolu → exit code 1 ve stderr'de hata mesajı."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '/nonexistent/path/no_such_file_xyz.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1, (
            f"Var olmayan dosya için exit code 1 bekleniyor, alınan: {result.returncode}"
        )
        assert result.stderr.strip() != "", (
            f"Var olmayan dosya için stderr'de hata mesajı bekleniyor; stderr boş"
        )

    def test_indent_negative_exit_2(self):
        """(2) --indent -1 → exit code 2 ve stderr'de hata mesajı."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--indent', '-1'],
            input='{"a": 1}',
            capture_output=True,
            text=True
        )
        assert result.returncode == 2, (
            f"--indent -1 için exit code 2 bekleniyor, alınan: {result.returncode}"
        )
        assert result.stderr.strip() != "", (
            f"--indent -1 için stderr'de hata mesajı bekleniyor; stderr boş"
        )


class TestCLIDiff:
    """--diff flag'i için temel senaryo testleri."""

    def test_diff_unformatted_file_exit_1_and_diff_lines(self):
        """(1) Biçimlendirilmemiş dosya + --diff → exit 1 ve diff satırları stdout'da."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"a":1,"b":2}')
            temp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'json_formatter', '--diff', temp_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 1, (
                f"Biçimlendirilmemiş dosya için exit code 1 bekleniyor; alınan: {result.returncode}"
            )
            # Unified diff çıktısında + ve/veya - satırları bulunmalı
            assert ('+' in result.stdout or '-' in result.stdout), (
                f"Diff satırları (+ veya -) bekleniyor; stdout: {repr(result.stdout)}"
            )
            # Unified diff başlığı bulunmalı
            assert '@@' in result.stdout, (
                f"Diff hunk başlığı ('@@') bekleniyor; stdout: {repr(result.stdout)}"
            )
        finally:
            os.unlink(temp_path)

    def test_diff_already_formatted_exit_0_already_formatted(self):
        """(2) Zaten formatlanmış dosya + --diff → exit 0 ve stdout'a 'Already formatted'."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--diff', 'tests/data/formatted.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Formatlanmış dosya için exit code 0 bekleniyor; alınan: {result.returncode}"
        )
        assert "Already formatted" in result.stdout, (
            f"'Already formatted' mesajı bekleniyor; stdout: {repr(result.stdout)}"
        )

    def test_diff_stdin_exit_2(self):
        """(3) stdin + --diff → exit 2 ve stderr'da hata mesajı."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--diff'],
            input='{"a":1}',
            capture_output=True,
            text=True
        )
        assert result.returncode == 2, (
            f"stdin + --diff için exit code 2 bekleniyor; alınan: {result.returncode}"
        )
        assert result.stderr.strip() != "", (
            f"stderr'de hata mesajı bekleniyor; stderr boş"
        )

    def test_diff_in_place_exit_2(self):
        """(4a) --diff + --in-place → exit 2 ve stderr'da hata mesajı."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"a":1}')
            temp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'json_formatter', '--diff', '--in-place', temp_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 2, (
                f"--diff + --in-place için exit code 2 bekleniyor; alınan: {result.returncode}"
            )
            assert result.stderr.strip() != "", (
                f"stderr'de hata mesajı bekleniyor; stderr boş"
            )
        finally:
            os.unlink(temp_path)

    def test_diff_check_exit_2(self):
        """(4b) --diff + --check → exit 2 ve stderr'da hata mesajı."""
        result = subprocess.run(
            [sys.executable, '-m', 'json_formatter', '--diff', '--check',
             'tests/data/formatted.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 2, (
            f"--diff + --check için exit code 2 bekleniyor; alınan: {result.returncode}"
        )
        assert result.stderr.strip() != "", (
            f"stderr'de hata mesajı bekleniyor; stderr boş"
        )

    def test_diff_color_plus_lines_green_minus_lines_red(self):
        """(5) --diff --color ile + satırları yeşil (\x1b[32m), - satırları kırmızı (\x1b[31m) olmalı."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"a":1,"b":2}')
            temp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'json_formatter', '--diff', '--color', temp_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 1
            assert '\x1b[32m+' in result.stdout, (
                f"Yeşil (+) satırı bekleniyor (\\x1b[32m+); stdout: {repr(result.stdout)}"
            )
            assert '\x1b[31m-' in result.stdout, (
                f"Kırmızı (-) satırı bekleniyor (\\x1b[31m-); stdout: {repr(result.stdout)}"
            )
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
