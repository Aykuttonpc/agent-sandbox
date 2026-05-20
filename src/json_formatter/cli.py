import sys
import os
import tempfile
import argparse
from .formatter import JSONFormatter, format_json

def main():
    parser = argparse.ArgumentParser(description="Format JSON from file or stdin")
    parser.add_argument("file", nargs="?", help="JSON file to format (optional, read from stdin if not provided)")

    fmt_group = parser.add_mutually_exclusive_group()
    fmt_group.add_argument("--compact", action="store_true", help="Compact JSON çıktısı üret (boşluk yok)")
    fmt_group.add_argument("--indent", type=int, default=2, help="Girinti seviyesi (varsayılan: 2)")

    parser.add_argument("--sort-keys", action="store_true", default=False, help="Nesne anahtarlarını alfabetik sırala")
    parser.add_argument("--in-place", "-i", action="store_true", help="Dosyayı yerinde atomik olarak formatla")
    parser.add_argument("--check", action="store_true", help="Dosyanın formatlanmış olup olmadığını kontrol et (yazmaz)")

    args = parser.parse_args()

    # --check stdin ile kullanılamaz
    if args.check and not args.file:
        print("Error: --check requires a file argument, not stdin", file=sys.stderr)
        sys.exit(2)

    # --check ve --in-place birlikte verilirse uyarı ver, yine de yalnızca check yap
    if args.check and args.in_place:
        print("Warning: --in-place ignored when --check is active", file=sys.stderr)

    # --in-place yalnızca dosya moduyla kullanılabilir
    if args.in_place and not args.file:
        print("Error: --in-place requires a file argument", file=sys.stderr)
        sys.exit(1)

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
    try:
        result = format_json(data, indent=args.indent, sort_keys=args.sort_keys, compact=args.compact)
    except ValueError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)

    # --check modu: karşılaştır, asla dosyaya yazma
    if args.check:
        if result.strip() == data.strip():
            sys.exit(0)
        else:
            print(f"File is not formatted: {args.file}", file=sys.stderr)
            sys.exit(1)

    # Çıktı yaz
    if args.in_place:
        # Atomik yazma: önce hedef dizinde geçici dosyaya yaz, sonra os.replace() ile değiştir
        dir_name = os.path.dirname(os.path.abspath(args.file))
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
        try:
            with os.fdopen(tmp_fd, 'w') as tmp:
                tmp.write(result)
            os.replace(tmp_path, args.file)
        except Exception:
            os.unlink(tmp_path)
            raise
    else:
        print(result)

if __name__ == "__main__":
    main()
