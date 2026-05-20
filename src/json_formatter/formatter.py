import json

class JSONFormatter:
    def __init__(self, indent: int = 2, sort_keys: bool = False, compact: bool = False, ensure_ascii: bool = True):
        self.indent = indent
        self.sort_keys = sort_keys
        self.compact = compact
        self.ensure_ascii = ensure_ascii

    def format(self, data: str) -> str:
        try:
            obj = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(str(e))
        if self.compact:
            return json.dumps(obj, separators=(',', ':'), indent=None, sort_keys=self.sort_keys, ensure_ascii=self.ensure_ascii)
        return json.dumps(obj, indent=self.indent, sort_keys=self.sort_keys, ensure_ascii=self.ensure_ascii)


def format_json(data: str, indent: int = 2, sort_keys: bool = False, compact: bool = False, ensure_ascii: bool = True) -> str:
    """JSON verisini formatlar ve string olarak döndürür."""
    formatter = JSONFormatter(indent=indent, sort_keys=sort_keys, compact=compact, ensure_ascii=ensure_ascii)
    return formatter.format(data)
