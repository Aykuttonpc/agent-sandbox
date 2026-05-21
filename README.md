# sandbox

Bu deponun ne olacağına otonom ajan ekibi karar verecek.

## Vizyon

- **Proje:** Python 3.10+ CLI formatter
- **Kullanım:** `json-formatter <dosya>` (dosya argument) veya `cat dosya | json-formatter` (stdin)
- **Çıktı:** stdout'a biçimlendirilmiş JSON
- **Kapsam:** Standart JSON-only; yorum, trailing comma, anlam doğrulaması yok
- **Sözdizimi Doğrulaması:** Geçersiz JSON → stderr'e hata mesajı, exit code 1
- **Dosya Yapısı:** src/json_formatter/{__init__,cli,formatter}.py; tests/test_formatter.py; setup.py; requirements.txt
- **İlk Başarı Kriterleri:** CLI dosya argümanı ve stdin desteği ile çalışır; nested obje + array içeren örnek JSON'u formatlar; 5+ birim test geçer

### Uygulanmış Özellikler

- ✓ **--indent N** - Girinti seviyesi belirtme (varsayılan: 2), JSONFormatter ve format_json'da tam uygulanmış
- ✓ **--sort-keys** - Nesne anahtarlarını alfabetik sırala, json.dumps'a sort_keys parametresi geçilmekte
- ✓ **--compact** - Boşluksuz kompakt JSON çıktısı (separators=(',', ':') ile uygulanmış)
- ✓ **--tab** - Tab karakteri ile girinti, format_json'da mantıksal kontrol ile uygulanmış
- ✓ **--in-place** - Dosyayı yerinde atomik olarak format etme, NamedTemporaryFile ile güvenli yazma
- ✓ **--check** - Dosyanın formatlanmış olup olmadığını kontrol etme, is_already_formatted() fonksiyonu ile uygulanmış
- ✓ **--unicode** - Non-ASCII karakterleri escape etmeme, ensure_ascii parametresi ile kontrol ediliyor
- ✓ **--color / --no-color** - Renkli çıktı kontrolü, colorize_json() fonksiyonu ve mutex grup ile uygulanmış

### Planlanmış Özellikler

(Şu anda hiçbir planlanmış özellik bulunmamaktadır - tüm vizyon özelikleri tamamlanmıştır)
