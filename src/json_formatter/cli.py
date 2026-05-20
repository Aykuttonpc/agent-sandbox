import sys
import argparse
from .formatter import JSONFormatter

def main():
    parser = argparse.ArgumentParser(description="Format JSON from file or stdin")
    parser.add_argument("file", nargs="?", help="JSON file to format (optional, read from stdin if not provided)")

    fmt_group = parser.add_mutually_exclusive_group()
    fmt_group.add_argument("--compact", action="store_true", help="Compact JSON çıktısı üret (boşluk yok)")
    fmt_group.add_argument("--indent", type=int, default=2, help="Girinti seviyesi (varsayılan: 2)")

    parser.add_argument("--sort-keys", action="store_true", help="Nesne anahtarlarını alfabetik sırala")

    args = parser.parse_args()

    # Girdi oku
    if args.file:
        try:
            with open(args.file, 'r') as f:
                data = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found", file=sys.stderr)
            sys.exit(1)
    else:
        data = sys.stdin.read()

    # JSON formatla
    formatter = JSONFormatter(indent=args.indent, sort_keys=args.sort_keys, compact=args.compact)
    try:
        result = formatter.format(data)
        print(result)
    except ValueError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
