import sys
import os
import tempfile
import argparse
from .formatter import JSONFormatter, format_json

def main():
    parser = argparse.ArgumentParser(description="Format JSON from file or stdin")
    parser.add_argument("file", nargs="*", help="JSON file(s) to format (optional, read from stdin if not provided)")

    fmt_group = parser.add_mutually_exclusive_group()
    fmt_group.add_argument("--compact", action="store_true", help="Compact JSON çıktısı üret (boşluk yok)")
    fmt_group.add_argument("--indent", type=int, default=2, help="Girinti seviyesi (varsayılan: 2)")

    parser.add_argument("--sort-keys", action="store_true", default=False, help="Nesne anahtarlarını alfabetik sırala")
    parser.add_argument("--in-place", "-i", action="store_true", help="Dosyayı yerinde atomik olarak formatla")
    parser.add_argument("--check", action="store_true", help="Dosyanın formatlanmış olup olmadığını kontrol et (yazmaz)")
    parser.add_argument("--unicode", action="store_true", help="Non-ASCII karakterleri escape etmeden yaz (--check ile birlikte kullanıldığında etkisizdir)")

    args = parser.parse_args()
    files = args.file  # nargs='*' → her zaman liste; boş liste stdin anlamına gelir

    # --check stdin ile kullanılamaz
    if args.check and not files:
        print("Error: --check requires a file argument, not stdin", file=sys.stderr)
        sys.exit(2)

    # --check ve --in-place birlikte verilirse uyarı ver, yine de yalnızca check yap
    if args.check and args.in_place:
        print("Warning: --in-place ignored when --check is active", file=sys.stderr)

    # --in-place yalnızca dosya moduyla kullanılabilir
    if args.in_place and not files:
        print("Error: --in-place requires a file argument", file=sys.stderr)
        sys.exit(1)

    # Stdout modu: 2+ dosya verilirse hata
    if not args.in_place and not args.check and len(files) >= 2:
        print("Error: stdout mode supports only a single file; use --in-place or --check for multiple files", file=sys.stderr)
        sys.exit(1)

    # Stdin modu (dosya verilmemişse)
    if not files:
        data = sys.stdin.read()
        try:
            result = format_json(data, indent=args.indent, sort_keys=args.sort_keys, compact=args.compact, ensure_ascii=not args.unicode)
        except ValueError as e:
            print(f"Error: Invalid JSON - {e}", file=sys.stderr)
            sys.exit(1)
        print(result)
        return

    # --check çoklu dosya modu
    if args.check:
        any_fail = False
        for filepath in files:
            try:
                with open(filepath, 'r') as f:
                    data = f.read()
            except FileNotFoundError:
                print(f"FAIL: {filepath}")
                print(f"Error: File '{filepath}' not found", file=sys.stderr)
                any_fail = True
                continue
            try:
                result = format_json(data, indent=args.indent, sort_keys=args.sort_keys, compact=args.compact, ensure_ascii=not args.unicode)
            except ValueError as e:
                print(f"FAIL: {filepath}")
                print(f"Error: Invalid JSON in '{filepath}' - {e}", file=sys.stderr)
                any_fail = True
                continue
            if result.strip() == data.strip():
                print(f"OK: {filepath}")
            else:
                print(f"FAIL: {filepath}")
                # Geriye dönük uyumluluk: tek dosya testleri bu mesajı stderr'de arar
                print(f"File is not formatted: {filepath}", file=sys.stderr)
                any_fail = True
        if any_fail:
            sys.exit(1)
        sys.exit(0)

    # --in-place çoklu dosya modu
    if args.in_place:
        any_fail = False
        for filepath in files:
            try:
                with open(filepath, 'r') as f:
                    data = f.read()
            except FileNotFoundError:
                print(f"Error: File '{filepath}' not found", file=sys.stderr)
                any_fail = True
                continue
            try:
                result = format_json(data, indent=args.indent, sort_keys=args.sort_keys, compact=args.compact, ensure_ascii=not args.unicode)
            except ValueError as e:
                print(f"Error: Invalid JSON in '{filepath}' - {e}", file=sys.stderr)
                any_fail = True
                continue
            dir_name = os.path.dirname(os.path.abspath(filepath))
            tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
            try:
                with os.fdopen(tmp_fd, 'w') as tmp:
                    tmp.write(result)
                os.replace(tmp_path, filepath)
            except Exception as e:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                print(f"Error: Failed to write '{filepath}' - {e}", file=sys.stderr)
                any_fail = True
        if any_fail:
            sys.exit(1)
        return

    # Tek dosya stdout modu
    filepath = files[0]
    try:
        with open(filepath, 'r') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        sys.exit(1)
    try:
        result = format_json(data, indent=args.indent, sort_keys=args.sort_keys, compact=args.compact, ensure_ascii=not args.unicode)
    except ValueError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)
    print(result)

if __name__ == "__main__":
    main()
