import sys
import argparse
from .formatter import JSONFormatter

def main():
    parser = argparse.ArgumentParser(description="Format JSON from file or stdin")
    parser.add_argument("file", nargs="?", help="JSON file to format (optional, read from stdin if not provided)")
    parser.add_argument("--indent", type=int, default=2, help="Indentation level (default: 2)")
    parser.add_argument("--sort-keys", action="store_true", help="Sort object keys alphabetically")
    
    args = parser.parse_args()
    
    # Read input
    if args.file:
        try:
            with open(args.file, 'r') as f:
                data = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found", file=sys.stderr)
            sys.exit(1)
    else:
        data = sys.stdin.read()
    
    # Format JSON
    formatter = JSONFormatter(indent=args.indent, sort_keys=args.sort_keys)
    try:
        result = formatter.format(data)
        print(result)
    except ValueError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
