#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FAISS Manager
Class quản lý FAISS index và search operations
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Union
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


class FAISSManager:
    """Class quản lý FAISS index và search"""
    
    def __init__(
        self,
        embedding_model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'
    ):
        """
        Khởi tạo FAISS Manager
        
        Args:
            embedding_model_name: Tên embedding model (phải giống với model đã dùng tạo embeddings)
        """
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.index = None
        self.embeddings = None
        self.chunks = None
        self.mapping = None
        self.reverse_mapping = None
        self.dimension = None
    
    def load_index(
        self,
        index_path: Path,
        embeddings_path: Optional[Path] = None,
        mapping_path: Optional[Path] = None,
        chunks_path: Optional[Path] = None
    ) -> None:
        """
        Load FAISS index và các dữ liệu liên quan
        
        Args:
            index_path: Đường dẫn file FAISS index
            embeddings_path: Đường dẫn file embeddings.npy (optional, để lấy dimension)
            mapping_path: Đường dẫn file chunk_mapping.json (optional)
            chunks_path: Đường dẫn file chunks.json (optional, để lấy nội dung chunks)
        """
        # Load index
        if not index_path.exists():
            raise FileNotFoundError(f"Không tìm thấy index file: {index_path}")
        
        print(f"Đang load FAISS index từ: {index_path}")
        self.index = faiss.read_index(str(index_path))
        self.dimension = self.index.d
        print(f"✓ Đã load index: {self.index.ntotal:,} vectors, dimension {self.dimension}")
        
        # Load embeddings nếu có (để lấy dimension hoặc sử dụng sau)
        if embeddings_path and embeddings_path.exists():
            self.embeddings = np.load(str(embeddings_path)).astype('float32')
            print(f"✓ Đã load embeddings: {self.embeddings.shape}")
        
        # Load mapping nếu có
        if mapping_path and mapping_path.exists():
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
            
            if isinstance(mapping_data, dict) and 'mapping' in mapping_data:
                self.mapping = mapping_data['mapping']
                self.reverse_mapping = mapping_data.get('reverse_mapping', {})
            else:
                self.mapping = mapping_data
                self.reverse_mapping = {v: k for k, v in self.mapping.items()}
            
            print(f"✓ Đã load mapping: {len(self.mapping)} chunks")
        
        # Load chunks nếu có
        if chunks_path and chunks_path.exists():
            with open(chunks_path, 'r', encoding='utf-8') as f:
                chunks_raw = json.load(f)
            
            # Flatten cấu trúc: một số items có thể là list chứa nhiều chunks
            print(f"  Đang flatten cấu trúc dữ liệu...")
            self.chunks = []
            for item in chunks_raw:
                if isinstance(item, list):
                    # Nếu là list, thêm tất cả các dicts trong list
                    self.chunks.extend([c for c in item if isinstance(c, dict)])
                elif isinstance(item, dict):
                    # Nếu là dict, thêm trực tiếp
                    self.chunks.append(item)
            
            print(f"✓ Đã load chunks: {len(self.chunks)} chunks (từ {len(chunks_raw)} items)")
    
    def search(
        self,
        query_embeddings: np.ndarray,
        top_k: int = 5,
        return_distances: bool = True
    ) -> Dict:
        """
        Tìm kiếm trong index
        
        Args:
            query_embeddings: Embeddings của query (shape: [num_queries, dimension])
            top_k: Số kết quả trả về
            return_distances: Có trả về distances không
            
        Returns:
            Dictionary chứa indices và distances
        """
        if self.index is None:
            raise ValueError("Chưa load index! Gọi load_index() trước.")
        
        # Đảm bảo đúng format
        if len(query_embeddings.shape) == 1:
            query_embeddings = query_embeddings.reshape(1, -1)
        
        query_embeddings = query_embeddings.astype('float32')
        
        # Tìm kiếm
        distances, indices = self.index.search(query_embeddings, top_k)
        
        result = {
            'indices': indices[0].tolist(),
            'top_k': top_k
        }
        
        if return_distances:
            result['distances'] = distances[0].tolist()
        
        return result
    
    def search_by_text(
        self,
        query_text: Union[str, List[str]],
        top_k: int = 5,
        return_distances: bool = True
    ) -> Dict:
        """
        Tìm kiếm bằng text (tự động tạo embeddings)
        
        Args:
            query_text: Text query hoặc list texts
            top_k: Số kết quả trả về
            return_distances: Có trả về distances không
            
        Returns:
            Dictionary chứa indices, distances, và chunks (nếu có)
        """
        # Tạo embeddings
        if isinstance(query_text, str):
            query_text = [query_text]
        
        query_embeddings = self.embedding_model.encode(query_text)
        
        # Tìm kiếm
        search_result = self.search(query_embeddings, top_k, return_distances)
        
        # Lấy chunks nếu có
        if self.chunks:
            search_result['chunks'] = [
                self.chunks[idx] for idx in search_result['indices'] 
                if 0 <= idx < len(self.chunks)
            ]
        
        return search_result
    
    def get_chunks_by_indices(self, indices: List[int]) -> List[Dict]:
        """
        Lấy chunks theo indices
        
        Args:
            indices: List indices
            
        Returns:
            List chunks
        """
        if self.chunks is None:
            raise ValueError("Chưa load chunks! Truyền chunks_path vào load_index().")
        
        return [self.chunks[idx] for idx in indices if 0 <= idx < len(self.chunks)]
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        """
        Lấy chunk theo ID
        
        Args:
            chunk_id: ID của chunk
            
        Returns:
            Chunk hoặc None nếu không tìm thấy
        """
        if self.mapping is None or self.chunks is None:
            return None
        
        index = self.mapping.get(chunk_id)
        if index is not None and 0 <= index < len(self.chunks):
            return self.chunks[index]
        
        return None


def main():
    """Test function"""
    from pathlib import Path
    
    # Test paths
    project_root = Path(__file__).parent.parent.parent
    index_path = project_root / "VectorDB" / "data" / "index" / "faiss_index.bin"
    embeddings_path = project_root / "Embeddings" / "data" / "embeddings" / "embeddings.npy"
    mapping_path = project_root / "Embeddings" / "data" / "mappings" / "chunk_mapping.json"
    chunks_path = project_root / "data_processing" / "chunks.json"
    
    # Khởi tạo
    manager = FAISSManager()
    
    # Load
    if index_path.exists():
        manager.load_index(
            index_path=index_path,
            embeddings_path=embeddings_path,
            mapping_path=mapping_path,
            chunks_path=chunks_path
        )
        
        # Test search
        query = "Phạm vi điều chỉnh của luật"
        print(f"\nTìm kiếm: '{query}'")
        results = manager.search_by_text(query, top_k=3)
        
        print(f"\nKết quả:")
        for i, (idx, dist) in enumerate(zip(results['indices'], results['distances'])):
            chunk = results['chunks'][i]
            print(f"\n[{i+1}] Index: {idx}, Distance: {dist:.4f}")
            print(f"    ID: {chunk.get('id', 'N/A')}")
            print(f"    Content: {chunk.get('content', '')[:100]}...")
    else:
        print(f"Index chưa được tạo. Chạy scripts/build_index.py trước.")


if __name__ == "__main__":
    main()

