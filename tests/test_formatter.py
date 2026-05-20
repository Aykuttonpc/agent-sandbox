import unittest
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

if __name__ == '__main__':
    unittest.main()
