## Bento HTTP örneği (Windows + Docker)

Bu repo, Bento'yu Docker ile çalıştırıp HTTP üzerinden JSON istekleri işlemek için basit bir örnek içerir.

### Ön koşullar

- **Docker Desktop** yüklü ve çalışıyor olmalı.
- `config.yaml` bu klasörde bulunmalı (örnek HTTP config'i zaten burada).

### 1. Bento konteynerini başlat

PowerShell'de bu klasöre gelin:

```powershell
cd C:\Users\Selcuk.Akarin\Desktop\bento_playground
```

Ardından Bento'yu HTTP server olarak çalıştırın:

```powershell
docker run --rm -i -p 4196:4196 -v "C:\Users\Selcuk.Akarin\Desktop\bento_playground\config.yaml:/bento.yaml" ghcr.io/warpstreamlabs/bento
```

Bu komut:

- `config.yaml` dosyasını konteyner içindeki `/bento.yaml` olarak mount eder,
- Host makinede `4196` portunu açar ve konteynerdeki `4196` portuna yönlendirir,
- Bento'yu HTTP input (`/echo` path'i) ve stdout output ile çalıştırır.

Bu pencere **açık kalmalı**; logları burada göreceksiniz.

### 2. HTTP isteği gönder

#### 2.1 PowerShell ile istek gönder

Yeni bir PowerShell penceresi açın ve aşağıdaki komutu çalıştırın:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:4196/echo `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"name": "bento", "type": "stream_processor", "features": ["fast", "fancy"], "stars": 1500}'
```

Bu istek:

- `http://localhost:4196/echo` adresine,
- JSON gövdesi ile (`name`, `type`, `features`, `stars` alanları),
- POST isteği gönderir.

Yanıt, `config.yaml` içindeki `mapping` bloğunda tanımlanan Bloblang kurallarına göre dönüştürülmüş JSON olacaktır; örneğin:

- **about**: `"%s 🍱 is a %s %s".format(this.name.capitalize(), this.features.join(" & "), this.type.split("_").join(" "))`
- **stars**: `"★".repeat((this.stars / 300))`

#### 2.2 curl (ve Postman) ile istek gönder

Aynı isteği `curl` ile de gönderebilirsiniz:

```bash
curl -X POST "http://localhost:4196/echo" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"bento\",\"type\":\"stream_processor\",\"features\":[\"fast\",\"fancy\"],\"stars\":1500}"
```

- Windows PowerShell'de `^` karakteri satır devamı içindir; isterseniz tek satırda da yazabilirsiniz.
- **Postman**'de kullanmak için: Postman → **Import** → **Raw text** → bu `curl` komutunu yapıştır → **Continue** → **Import**.
- Alternatif olarak Postman'de:
  - Method: **POST**
  - URL: `http://localhost:4196/echo`
  - Body: **raw** + **JSON**
  - İçerik:

    ```json
    {
      "name": "bento",
      "type": "stream_processor",
      "features": ["fast", "fancy"],
      "stars": 1500
    }
    ```

### Referans

- Bento Getting Started dokümantasyonu: `https://warpstreamlabs.github.io/bento/docs/guides/getting_started/`


