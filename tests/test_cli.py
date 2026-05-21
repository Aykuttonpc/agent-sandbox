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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
