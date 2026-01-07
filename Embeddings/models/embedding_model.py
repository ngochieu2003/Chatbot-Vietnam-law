#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding Model Manager
Quản lý và load embedding models
"""

from pathlib import Path
from typing import List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import torch


class EmbeddingModel:
    """Class quản lý embedding model"""
    
    # Danh sách models được hỗ trợ
    SUPPORTED_MODELS = {
        'multilingual-minilm': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        'multilingual-mpnet': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        'multilingual-e5': 'intfloat/multilingual-e5-base',
        'vietnamese-sbert': 'keepitreal/vietnamese-sbert',
        'vietnamese-phobert': 'VoVanPhuc/sup-SimCSE-VietNamese-phobert-base'
    }
    
    def __init__(
        self,
        model_name: str = 'multilingual-minilm',
        device: Optional[str] = None,
        cache_folder: Optional[Path] = None
    ):
        """
        Khởi tạo embedding model
        
        Args:
            model_name: Tên model (key trong SUPPORTED_MODELS) hoặc đường dẫn model
            device: Device để chạy model ('cpu', 'cuda', None = auto)
            cache_folder: Thư mục cache model
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.cache_folder = cache_folder
        
        # Lấy model path
        if model_name in self.SUPPORTED_MODELS:
            model_path = self.SUPPORTED_MODELS[model_name]
        else:
            model_path = model_name
        
        # Load model
        print(f"Đang load model: {model_path}")
        print(f"Device: {self.device}")
        
        self.model = SentenceTransformer(
            model_path,
            device=self.device,
            cache_folder=str(cache_folder) if cache_folder else None
        )
        
        # Lấy dimension của model
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        print(f"✓ Model đã được load. Dimension: {self.dimension}")
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress_bar: bool = True,
        normalize_embeddings: bool = False
    ) -> np.ndarray:
        """
        Tạo embeddings cho text(s)
        
        Args:
            texts: Text hoặc list texts
            batch_size: Kích thước batch
            show_progress_bar: Hiển thị progress bar
            normalize_embeddings: Chuẩn hóa embeddings về unit vector
            
        Returns:
            Numpy array chứa embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress_bar: bool = True
    ) -> np.ndarray:
        """
        Tạo embeddings cho batch texts (alias cho encode)
        
        Args:
            texts: List texts
            batch_size: Kích thước batch
            show_progress_bar: Hiển thị progress bar
            
        Returns:
            Numpy array chứa embeddings
        """
        return self.encode(texts, batch_size, show_progress_bar)
    
    def get_dimension(self) -> int:
        """Lấy dimension của embeddings"""
        return self.dimension
    
    def get_model_info(self) -> dict:
        """Lấy thông tin về model"""
        # Lấy model path từ SentenceTransformer
        try:
            if hasattr(self.model, '_modules') and len(self.model._modules) > 0:
                first_module = list(self.model._modules.values())[0]
                if hasattr(first_module, 'auto_model') and hasattr(first_module.auto_model, 'config'):
                    model_path = first_module.auto_model.config.name_or_path
                else:
                    model_path = self.SUPPORTED_MODELS.get(self.model_name, self.model_name)
            else:
                model_path = self.SUPPORTED_MODELS.get(self.model_name, self.model_name)
        except:
            model_path = self.SUPPORTED_MODELS.get(self.model_name, self.model_name)
        
        return {
            'model_name': self.model_name,
            'model_path': model_path,
            'dimension': self.dimension,
            'device': self.device,
            'max_seq_length': self.model.max_seq_length
        }
    
    @classmethod
    def list_supported_models(cls) -> dict:
        """Liệt kê các models được hỗ trợ"""
        return cls.SUPPORTED_MODELS.copy()

