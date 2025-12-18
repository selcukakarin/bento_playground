# document_utils.py

import os
import datetime
import io
from typing import Dict, List, Callable, Any, Optional

# Gerekli kütüphane bağımlılıkları (requirements.txt'den)
from langchain_core.documents import Document 
from langchain_text_splitters import RecursiveCharacterTextSplitter
# MarkItDown kütüphanesinin doğru kurulduğu varsayılmıştır
from markitdown import MarkItDown 


class DocumentLoader:
    """Bu sınıf, çeşitli belge türlerini yüklemek ve içeriklerini çıkarmak için tasarlanmıştır."""

    def __init__(self) -> None:
        """DocumentLoader'ı desteklenen dosya uzantılarıyla başlatır."""
        self.extension_map: Dict[str, Callable[[str], List[Document]]] = {
            # Kaynaklarda belirtilen uzantılar [1]
            ".pdf": self._load_markitdown,
            ".docx": self._load_markitdown,
            ".doc": self._load_markitdown,
            ".pptx": self._load_markitdown,
            ".ppt": self._load_markitdown,
        }

    def load_document(self, file_path: str) -> List[Document]:
        """Bir dosya yolundan belgeyi yükler ve içeriğini çıkarır. [1]"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}") [1]

            # Dosya uzantısını al
            file_extension = os.path.splitext(file_path)[2].lower() [3]
            loader_func = self.extension_map.get(file_extension) [3]

            if not loader_func:
                raise ValueError(f"Unsupported file extension: {file_extension}") [3]

            # Belge için temel meta veriyi oluştur
            base_metadata: Dict[str, Any] = {
                "source": file_path,
                "file_name": os.path.basename(file_path),
                "file_type": file_extension,
                "date_processed": datetime.datetime.now().isoformat(),
            } [3]

            documents = loader_func(file_path)

            # Çıkarılan belgelere temel meta veriyi ekle
            for doc in documents:
                doc.metadata.update(base_metadata) [3]

            return documents

        except Exception as e:
            raise RuntimeError(f"Failed to load document {file_path}: {str(e)}") [4]

    def _load_markitdown(self, file_path: str) -> List[Document]:
        """MarkItDown kullanarak desteklenen dosyaları Markdown'a dönüştürür. [4]"""
        md = MarkItDown(enable_plugins=False)
        result = md.convert(file_path)
        markdown_text = result.text_content
        return [Document(page_content=markdown_text, metadata={})] [4]

class DocumentSplitter:
    """Belgeleri parçalara (chunk) ayırır ve dosya yolunu her parçanın başına ekler. [5]"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """Chunk büyüklüğü ve çakışmasını ayarlar. [5]"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Belgeleri chunk'lara böler ve ön ek ekler. [6]"""
        final_chunks = []
        for doc in documents:
            chunks = self._split_and_prepend(doc.page_content, doc.metadata)
            final_chunks.extend(chunks)
        return final_chunks

    def _split_and_prepend(self, text: str, metadata: dict) -> List[Document]:
        """RecursiveCharacterTextSplitter kullanarak metni böler ve dosya adını içeriğin başına ekler. [6]"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        ) [6]

        splits = splitter.split_text(text) [7]
        docs = []
        file_path = metadata.get("file_name", "") [7]

        for chunk in splits:
            # Chunk içeriğine dosya adını ön ek olarak ekle: "file_name\n\nchunk_content" [7]
            content = f"{file_path}\n\n{chunk.lstrip()}"
            docs.append(Document(page_content=content, metadata=metadata)) [7]

        return docs