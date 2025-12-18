# Dockerfile

# Python 3.11 slim imajını kullan
FROM python:3.11-slim

# Gerekli sistem paketlerini kur (örn. MarkItDown için libmagic-dev gerekebilir)
RUN apt-get update && apt-get install -y \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python bağımlılıklarını kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY document_utils.py .
COPY fastapi_worker.py .

# Çalışma zamanı için yetkisiz kullanıcıyı ayarla
USER nobody

# Varsayılan CMD uvicorn sunucusunu başlatır (8080 portunda)
CMD ["uvicorn", "fastapi_worker:app", "--host", "0.0.0.0", "--port", "8080"]