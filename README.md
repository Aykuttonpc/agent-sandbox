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

## Seçenek Referansı

| Seçenek | Açıklama | Varsayılan |
|---------|----------|----------|
| --indent N | Girinti seviyesi belirtme | 2 |
| --sort-keys | Nesne anahtarlarını alfabetik sırala (iç içe nesneler dahil) | Sıralamasız |
| --compact | Boşluksuz kompakt JSON çıktısı | Biçimlenmiş |
| --tab | Tab karakteri ile girinti | Boşluk |
| --in-place | Dosyayı yerinde atomik olarak format etme | Stdout'a yazdır |
| --check | Dosyanın formatlanmış olup olmadığını kontrol | Formatla |
| --unicode | Non-ASCII karakterleri escape etmeme | Escape et |
| --color / --no-color | Renkli çıktı kontrolü | Renkli (destekleniyorsa) |

## Kullanım Örnekleri

### Dosya Argument

```bash
json-formatter data.json
json-formatter --indent 4 --sort-keys config.json
```

### stdin

```bash
cat data.json | json-formatter
echo '{"b":2,"a":1}' | json-formatter --sort-keys
```

### Seçenek Örnekleri

```bash
json-formatter --sort-keys data.json
json-formatter --compact config.json
json-formatter --indent 4 data.json
json-formatter --in-place file.json
```
