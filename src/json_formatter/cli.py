import sys
import os
import json
import tempfile
import argparse
import glob as _glob
from .formatter import JSONFormatter, format_json, is_already_formatted, is_formatted
from .color import colorize_json


def _non_negative_int(value):
    """--indent için negatif olmayan tam sayı doğrulayıcı.

    Değer geçerli bir tam sayı değilse ya da negatifse
    argparse.ArgumentTypeError fırlatır; argparse bunu exit code 2 ile sonlandırır.
    """
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Geçersiz tam sayı değeri: '{value}'")
    if ivalue < 0:
        raise argparse.ArgumentTypeError(
            f"--indent negatif olamaz: {ivalue}"
        )
    return ivalue


def build_parser():
    """Argüman ayrıştırıcıyı oluşturup döndürür."""
    from json_formatter import __version__
    parser = argparse.ArgumentParser(description="Format JSON from file or stdin")
    parser.add_argument("file", nargs="*", help="JSON file(s) to format (optional, read from stdin if not provided)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # --compact, --indent ve --tab üçü birbirini dışlayan format grubu.
    fmt_group = parser.add_mutually_exclusive_group()
    fmt_group.add_argument("--compact", action="store_true", help="Compact JSON çıktısı üret (boşluk yok)")
    fmt_group.add_argument("--indent", type=_non_negative_int, default=2, help="Girinti seviyesi (varsayılan: 2); negatif değer kabul edilmez")
    fmt_group.add_argument("--tab", action="store_true", help="Tab karakteri (\\t) ile girintile")

    parser.add_argument("--sort-keys", action="store_true", default=False, help="Nesne anahtarlarını alfabetik sırala")

    # --in-place ve --check argparse mutually_exclusive_group dışında tutulur;
    # çakışma main() içinde özel Türkçe mesajla ele alınır (exit 2).
    parser.add_argument("--in-place", "-i", action="store_true", help="Dosyayı yerinde atomik olarak formatla")
    parser.add_argument("--check", action="store_true", help="Dosyanın formatlanmış olup olmadığını kontrol et (yazmaz)")

    parser.add_argument("--unicode", action="store_true", help="Non-ASCII karakterleri escape etme")

    color_group = parser.add_mutually_exclusive_group()
    color_group.add_argument("--color", action="store_true", default=False, help="Renkli çıktıyı zorla aç")
    color_group.add_argument("--no-color", dest="no_color", action="store_true", default=False, help="Renkli çıktıyı zorla kapat")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    files = args.file  # nargs='*' → her zaman liste; boş liste stdin anlamına gelir

    # Glob genişlemesi
    expanded = []
    for pattern in files:
        matches = sorted(_glob.glob(pattern, recursive=True))
        expanded.extend(matches if matches else [pattern])
    files = expanded

    # --check + --in-place birlikte kullanılamaz; özel Türkçe mesajla exit 2
    if args.check and args.in_place:
        print("Bu iki flag birlikte kullanılamaz", file=sys.stderr)
        sys.exit(2)

    # Renk kararı:
    #   --in-place / --check  → renk yok (dosyaya yazılıyor)
    #   --color               → TTY kontrolü olmaksızın her zaman renkli
    #   --no-color            → her zaman renksiz
    #   (ikisi de yok)        → sys.stdout.isatty() kontrolü
    if args.in_place or args.check:
        use_color = False
    elif args.color:
        use_color = True
    elif args.no_color:
        use_color = False
    else:
        use_color = sys.stdout.isatty()

    fmt_kwargs = dict(sort_keys=args.sort_keys, compact=args.compact, unicode=args.unicode, tab=args.tab)
    if not args.compact and not args.tab:
        fmt_kwargs["indent"] = args.indent

    # --check stdin ile kullanılamaz
    if args.check and not files:
        print("Error: --check requires a file argument, not stdin", file=sys.stderr)
        sys.exit(2)

    # --in-place yalnızca dosya moduyla kullanılabilir
    if args.in_place and not files:
        parser.error("--in-place requires a file argument")

    # Stdout modu: 2+ dosya verilirse hata
    if not args.in_place and not args.check and len(files) >= 2:
        print("Error: stdout mode supports only a single file; use --in-place or --check for multiple files", file=sys.stderr)
        sys.exit(1)

    # Stdin modu (dosya verilmemişse)
    if not files:
        data = sys.stdin.read()
        try:
            result = format_json(data, **fmt_kwargs)
        except json.JSONDecodeError as e:
            print(e.msg, file=sys.stderr)
            sys.exit(1)
        if use_color:
            result = colorize_json(result)
        print(result)
        return

    # --check modu
    if args.check:
        any_fail = False
        for filepath in files:
            if not os.path.isfile(filepath):
                print(f"Error: File '{filepath}' not found", file=sys.stderr)
                any_fail = True
                continue

            try:
                with open(filepath, 'r') as f:
                    data = f.read()
            except PermissionError:
                print(f"Error: Permission denied for '{filepath}'", file=sys.stderr)
                any_fail = True
                continue
            except OSError as e:
                print(f"Error: Cannot read '{filepath}' - {e}", file=sys.stderr)
                any_fail = True
                continue

            # Geçersiz JSON: is_formatted() ile karıştırmadan önce ayrıca kontrol et
            try:
                json.loads(data)
            except json.JSONDecodeError as e:
                print(
                    f"Geçersiz JSON: satır {e.lineno}, sütun {e.colno}: {e.msg}",
                    file=sys.stderr
                )
                any_fail = True
                continue

            # Formatlı mı kontrolü
            indent_val = args.indent if (not args.compact and not args.tab) else 2
            if is_formatted(data, indent=indent_val, sort_keys=args.sort_keys,
                            compact=args.compact, tab=args.tab, unicode_=args.unicode):
                print("Already formatted")
            else:
                print("File is not formatted")
                any_fail = True

        if any_fail:
            sys.exit(1)
        sys.exit(0)

    # --in-place çoklu dosya modu: NamedTemporaryFile ile atomik yazma
    if args.in_place:
        any_fail = False
        for filepath in files:
            try:
                with open(filepath, 'r') as f:
                    data = f.read()
            except PermissionError:
                print(f"Error: Permission denied for '{filepath}'", file=sys.stderr)
                any_fail = True
                continue
            except OSError as e:
                print(f"Error: Cannot read '{filepath}' - {e}", file=sys.stderr)
                any_fail = True
                continue

            try:
                result = format_json(data, **fmt_kwargs)
            except json.JSONDecodeError as e:
                print(e.msg, file=sys.stderr)
                any_fail = True
                continue

            dir_name = os.path.dirname(os.path.abspath(filepath))
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile('w', dir=dir_name, suffix='.tmp', delete=False) as tmp:
                    tmp_path = tmp.name
                    tmp.write(result)
                os.replace(tmp_path, filepath)
            except OSError as e:
                if tmp_path is not None:
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
    except PermissionError:
        print(f"Error: Permission denied for '{filepath}'", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: Cannot read '{filepath}' - {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = format_json(data, **fmt_kwargs)
    except json.JSONDecodeError as e:
        print(e.msg, file=sys.stderr)
        sys.exit(1)

    if use_color:
        result = colorize_json(result)
    print(result)


if __name__ == "__main__":
    main()
