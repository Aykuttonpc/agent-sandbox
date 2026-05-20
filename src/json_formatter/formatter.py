import json

class JSONFormatter:
    def __init__(self, indent: int = 2, sort_keys: bool = False, compact: bool = False):
        self.indent = indent
        self.sort_keys = sort_keys
        self.compact = compact

    def format(self, data: str) -> str:
        try:
            obj = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(str(e))
        if self.compact:
            return json.dumps(obj, separators=(',', ':'), indent=None, sort_keys=self.sort_keys)
        return json.dumps(obj, indent=self.indent, sort_keys=self.sort_keys)
