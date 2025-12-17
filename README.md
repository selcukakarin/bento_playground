## Bento HTTP örneği (Windows + Docker)

Bu repo, Bento'yu Docker ile çalıştırıp HTTP üzerinden JSON istekleri işlemek için basit bir örnek içerir.

### Ön koşullar

- **Docker Desktop** yüklü ve çalışıyor olmalı.
- `config.yaml` bu klasörde bulunmalı (örnek HTTP config'i zaten burada).

### 1. Bento konteynerini başlat

PowerShell'de bu klasöre gelin:

```powershell
cd C:\Users\Selcuk.Akarin\Desktop\bento_test1
```

Ardından Bento'yu HTTP server olarak çalıştırın:

```powershell
docker run --rm -i -p 4196:4196 -v "C:\Users\Selcuk.Akarin\Desktop\bento_test1\config.yaml:/bento.yaml" ghcr.io/warpstreamlabs/bento
```

Bu komut:

- `config.yaml` dosyasını konteyner içindeki `/bento.yaml` olarak mount eder,
- Host makinede `4196` portunu açar ve konteynerdeki `4196` portuna yönlendirir,
- Bento'yu HTTP input (`/echo` path'i) ve stdout output ile çalıştırır.

Bu pencere **açık kalmalı**; logları burada göreceksiniz.

### 2. HTTP isteği gönder

Yeni bir PowerShell penceresi açın ve aşağıdaki komutu çalıştırın:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:4196/echo `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"id":"1","names":["celine","dion"]}'
```

Bu istek:

- `http://localhost:4196/echo` adresine,
- JSON gövdesi ile (`id` ve `names` alanları),
- POST isteği gönderir.

Yanıt, Bento pipeline'ında tanımlanan `mapping` kurallarına göre dönüştürülmüş JSON olacaktır (orijinal belge `doc` altında, `first_name` upper-case, `last_name` ise sha256 + base64 olarak gelir).

### Referans

- Bento Getting Started dokümantasyonu: `https://warpstreamlabs.github.io/bento/docs/guides/getting_started/`


