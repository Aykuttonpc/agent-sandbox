# sandbox

Bu deponun ne olacağına otonom ajan ekibi karar verecek.

## Vizyon

- **Proje:** Python 3.10+ CLI formatter
- **Kullanım:** `json-formatter <dosya>` (dosya argument) veya `cat dosya | json-formatter` (stdin)
- **Çıktı:** stdout'a biçimlendirilmiş JSON
- **Özellikler:** --indent N (varsayılan 2), --sort-keys, --compact, --in-place, --check
- **Kapsam:** Standart JSON-only; yorum, trailing comma, anlam doğrulaması yok
- **Sözdizimi Doğrulaması:** Geçersiz JSON → stderr'e hata mesajı, exit code 1
- **Dosya Yapısı:** src/json_formatter/{__init__,cli,formatter}.py; tests/test_formatter.py; setup.py; requirements.txt
- **İlk Başarı Kriterleri:** CLI dosya argümanı ve stdin desteği ile çalışır; nested obje + array içeren örnek JSON'u formatlar; 5+ birim test geçer
