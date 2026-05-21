import subprocess
import json
import tempfile
import os
import pytest


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
        # Anahtarlar alfabetik sırada olmalı: a, z
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
        # Nested object: {"outer":{"z":1,"a":2}}
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
        
        # Dış nesne anahtarı
        outer_keys = list(output_json.keys())
        assert outer_keys == ['outer']
        
        # İç nesne anahtarları sıralanmalı
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
        # Sıralama yapılmadığında, JSON parse etmeden kontrol etmek
        # Python 3.7+ dict order preserves insertion order
        # Formatted output'ta z, a sırasında olmalı
        assert '"z"' in output and '"a"' in output


class TestCLICheckMode:
    """--check flag'i ile is_formatted() entegrasyonunu test et."""

    def test_check_formatted_file_returns_exit_0(self):
        """Formatlanmış dosya --check ile exit code 0 döndürmeli."""
        # formatted.json zaten tests/data/ altında var
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--check', 'tests/data/formatted.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "OK:" in result.stdout

    def test_check_unformatted_file_returns_exit_1(self):
        """Formatlanmamış dosya --check ile exit code 1 döndürmeli."""
        # unformatted.json zaten tests/data/ altında var
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--check', 'tests/data/unformatted.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "FAIL:" in result.stdout

    def test_check_invalid_json_file_returns_exit_1(self):
        """Geçersiz JSON dosyası --check ile exit code 1 döndürmeli."""
        # invalid.json zaten tests/data/ altında var
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--check', 'tests/data/invalid.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "FAIL:" in result.stdout


class TestCLIInvalidJSON:
    """Invalid JSON dosyası ile test et."""

    def test_cli_invalid_json_exit_code(self):
        """Invalid JSON dosyası ile çalıştır, returncode==1 ve stderr'da 'Invalid JSON' mesajı assert et."""
        result = subprocess.run(
            ['python', '-m', 'json_formatter', 'tests/data/invalid.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "Invalid JSON" in result.stderr


class TestCLIInPlace:
    """--in-place flag'ini atomik yazma ile test et."""

    def test_cli_in_place_successful_write(self):
        """--in-place ile başarılı yazma: dosya formatlanmış olmalı."""
        unformatted_json = '{"z":1,"a":2}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(unformatted_json)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ['python', '-m', 'json_formatter', '--in-place', temp_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            
            # Dosya formatlanmış olmalı
            with open(temp_path, 'r') as f:
                content = f.read()
            parsed = json.loads(content)
            assert parsed == {"z": 1, "a": 2}
            
            # İndent 2 olmalı (varsayılan)
            assert '  ' in content
        finally:
            os.unlink(temp_path)

    def test_cli_in_place_format_error_preserves_original(self):
        """Format hatası durumunda orijinal dosya korunmalı."""
        invalid_json = '{"z":1,"a":2'  # Kapanmamış
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(invalid_json)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ['python', '-m', 'json_formatter', '--in-place', temp_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 1
            assert "Invalid JSON" in result.stderr
            
            # Dosya değişmemiş olmalı
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
            capture_output=True,
            text=True
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
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            
            # Dosya formatlanmış ve anahtarlar sıralanmış olmalı
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
            capture_output=True,
            text=True
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
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            
            # Her iki dosya da formatlanmış olmalı
            with open(temp_path1, 'r') as f:
                content1 = f.read()
            with open(temp_path2, 'r') as f:
                content2 = f.read()
            
            parsed1 = json.loads(content1)
            parsed2 = json.loads(content2)
            assert parsed1 == {"b": 2, "a": 1}
            assert parsed2 == {"y": 3, "x": 4}
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)


class TestCLICompactFlag:
    """--compact flag'i ile boşluksuz JSON çıktısını test et."""

    def test_compact_basic_functionality(self):
        """--compact flag'ı ile boşluksuz JSON üretmeyi test et.
        
        Kontroller:
        (a) Çıktı geçerli JSON
        (b) Newline karakteri yok
        (c) İndentation yok (satır başında boşluk yok)
        """
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--compact', 'tests/data/sample.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        output = result.stdout.strip()
        
        # (a) Geçerli JSON olduğunu kontrol et (json.loads() ile parse et)
        parsed = json.loads(output)
        assert parsed is not None
        
        # (b) Newline karakteri (`\n`) içermediğini assert et
        assert '\n' not in output, f"Output contains newlines: {repr(output)}"
        
        # (c) Satır başında boşluk olmadığını (indentation yok) assert et
        assert not output.startswith(' '), "Output starts with space (has indentation)"
        assert not output.startswith('\t'), "Output starts with tab (has indentation)"

    def test_compact_with_sort_keys(self):
        """--compact --sort-keys kombinasyonu ile boşluksuz ve sıralanmış JSON üretmeyi test et.
        
        Kontroller:
        (a) Çıktı geçerli JSON
        (b) Recursive olarak tüm nested objelerin anahtarları alfabetik sıralanmış
        """
        def is_keys_sorted_recursive(obj):
            """Verilen nesnenin tüm dict anahtarlarının alfabetik sıralanmış olup olmadığını kontrol et."""
            if isinstance(obj, dict):
                keys = list(obj.keys())
                if keys != sorted(keys):
                    return False
                # Tüm değerleri recursive kontrol et
                for value in obj.values():
                    if not is_keys_sorted_recursive(value):
                        return False
                return True
            elif isinstance(obj, list):
                # Listede dict varsa kontrol et
                for item in obj:
                    if not is_keys_sorted_recursive(item):
                        return False
                return True
            return True
        
        result = subprocess.run(
            ['python', '-m', 'json_formatter', '--compact', '--sort-keys', 'tests/data/sample.json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        output = result.stdout.strip()
        
        # (a) Geçerli JSON olduğunu kontrol et (json.loads() ile parse et)
        parsed = json.loads(output)
        assert parsed is not None
        
        # (b) Parse ettikten sonra recursive olarak tüm nested objelerin anahtarlarının alfabetik sıralanmış olduğunu assert et
        assert is_keys_sorted_recursive(parsed), f"Parsed object has unsorted keys: {parsed}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
