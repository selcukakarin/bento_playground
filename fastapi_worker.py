# fastapi_worker.py
# Çalıştırma komutu: uvicorn fastapi_worker:app --host 0.0.0.0 --port 8080

import os
import tempfile
import json
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import requests

# Qdrant için
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, NamedVectors
import datetime

# Kendi yardımcı sınıflarımızı içe aktar
from document_utils import DocumentLoader, DocumentSplitter 

# --- Yapılandırma ---
# Ortam değişkenlerinden yapılandırma okuma
QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_COLLECTION_NAME = os.environ.get("QDRANT_COLLECTION_NAME")
VECTOR_API_URL = os.environ.get("VECTOR_API_URL")
NET_DOWNLOAD_ENDPOINT = os.environ.get("NET_DOWNLOAD_ENDPOINT")

# --- İstemciler ve Yardımcılar ---
app = FastAPI(title="File Processing Worker")
qdrant_client = QdrantClient(url=QDRANT_URL)
doc_loader = DocumentLoader()
doc_splitter = DocumentSplitter(chunk_size=1000, chunk_overlap=200)

# Pydantic Modelleri (Kafka'dan gelen mesaj yapısı)
class FileProcessingRequest(BaseModel):
    Id: str # PostgreSQL primary key
    Source: str # Server'daki dosya yolu
    FileName: str
    FileType: str

# Vektör servisine gönderilecek istek yapısı
class VectorizationInput(BaseModel):
    input: Dict[str, str]


@app.post("/process")
async def process_file_endpoint(file_data: FileProcessingRequest):
    """
    Bento tarafından çağrılır. Dosyayı indirir, böler, vektörleştirir ve Qdrant'a kaydeder.
    """
    
    file_id = file_data.Id
    server_path = file_data.Source
    file_name = file_data.FileName
    file_type = file_data.FileType
    
    temp_file_path = None
    
    try:
        # 1. Dosyayı .NET uygulamasından indirme
        download_payload = {"server_path": server_path}
        
        # HTTP isteği gönderimi [8]
        download_response = requests.post(
            NET_DOWNLOAD_ENDPOINT, 
            json=download_payload,
            timeout=300 
        )
        download_response.raise_for_status()
        
        file_content = download_response.content
        
        # 2. İndirilen dosyayı geçici bir dizine kaydet (DocumentLoader'ın dosya yolu ihtiyacı nedeniyle)
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_type) as tmp:
            tmp.write(file_content)
            temp_file_path = tmp.name
        
        # 3. DocumentLoader ile metni çıkar
        # DocumentLoader, dosya yolunu [1] ve uzantısını [3] kullanır.
        documents = doc_loader.load_document(temp_file_path)
        
        # 4. Chunk'lara Ayırma (RecursiveCharacterTextSplitter kullanılır) [6]
        chunks = doc_splitter.split_documents(documents)
        print(f"File {file_name} split into {len(chunks)} chunks.")

        points_to_upsert: List[PointStruct] = []
        
        for i, chunk in enumerate(chunks):
            chunk_content = chunk.page_content
            
            # 5. Harici Vektör API'yi çağırma
            vector_input = VectorizationInput(input={"text": chunk_content})
            
            vector_response = requests.post(
                VECTOR_API_URL, 
                json=vector_input.model_dump(),
                timeout=60
            )
            vector_response.raise_for_status()
            vectors_data = vector_response.json()
            
            # 6. Vektörleri Qdrant yapısına hazırlama (Dense: 1024, Sparse: 95, ColBERT: 204x1024)
            named_vectors = NamedVectors(
                vectors={
                    "dense": vectors_data["dense"],
                    "sparse": vectors_data["sparse"], 
                    "colbert": vectors_data["colbert"]
                }
            )
            
            # 7. Payload hazırlama (Qdrant şemasına uygun)
            payload = {
                "source": chunk.metadata.get("source"),
                "file_name": chunk.metadata.get("file_name"),
                "file_type": chunk.metadata.get("file_type"),
                "date_processed": chunk.metadata.get("date_processed"), 
                "page_content": chunk_content,
                "indexed_at": datetime.datetime.now().isoformat(),
                "file_id": file_id 
            }

            point_id = f"{file_id}-{i}" 

            points_to_upsert.append(
                PointStruct(
                    id=point_id,
                    vector=named_vectors,
                    payload=payload
                )
            )

        # 8. Qdrant'a toplu kaydetme (Upsert)
        if points_to_upsert:
            qdrant_client.upsert(
                collection_name=QDRANT_COLLECTION_NAME,
                points=points_to_upsert,
                wait=True
            )
        
        return {"status": "SUCCESS", "indexed_chunks": len(points_to_upsert), "file_id": file_id}

    except Exception as e:
        # Hata durumunda 500 dönerek Bento'nun tekrar denemesini veya hata işlemesini sağla [9], [10]
        error_message = f"Processing failed for ID {file_id}: {str(e)}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
        
    finally:
        # Geçici dosyayı temizle
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)