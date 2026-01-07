#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding Utilities
Helper functions cho việc lưu/load embeddings và mappings
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from datetime import datetime


def save_embeddings(
    embeddings: np.ndarray,
    output_path: Path,
    metadata: Optional[Dict] = None
) -> None:
    """
    Lưu embeddings vào file .npy
    
    Args:
        embeddings: Numpy array chứa embeddings
        output_path: Đường dẫn file output
        metadata: Metadata về embeddings (optional)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Lưu embeddings
    np.save(str(output_path), embeddings)
    print(f"✓ Đã lưu embeddings: {output_path}")
    print(f"  - Shape: {embeddings.shape}")
    print(f"  - Size: {embeddings.nbytes / 1024 / 1024:.2f} MB")
    
    # Lưu metadata nếu có
    if metadata:
        metadata_path = output_path.parent / f"{output_path.stem}_info.json"
        metadata['saved_at'] = datetime.now().isoformat()
        metadata['shape'] = list(embeddings.shape)
        metadata['dtype'] = str(embeddings.dtype)
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"✓ Đã lưu metadata: {metadata_path}")


def load_embeddings(embeddings_path: Path) -> np.ndarray:
    """
    Load embeddings từ file .npy
    
    Args:
        embeddings_path: Đường dẫn file embeddings
        
    Returns:
        Numpy array chứa embeddings
    """
    embeddings_path = Path(embeddings_path)
    
    if not embeddings_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {embeddings_path}")
    
    embeddings = np.load(str(embeddings_path))
    print(f"✓ Đã load embeddings: {embeddings_path}")
    print(f"  - Shape: {embeddings.shape}")
    
    return embeddings


def save_mapping(
    mapping: Dict[str, int],
    output_path: Path,
    reverse_mapping: Optional[Dict[int, str]] = None
) -> None:
    """
    Lưu mapping (chunk_id -> index) vào file JSON
    
    Args:
        mapping: Dictionary mapping chunk_id -> index
        output_path: Đường dẫn file output
        reverse_mapping: Reverse mapping (index -> chunk_id) - optional
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    mapping_data = {
        'mapping': mapping,
        'total_chunks': len(mapping),
        'created_at': datetime.now().isoformat()
    }
    
    if reverse_mapping:
        mapping_data['reverse_mapping'] = reverse_mapping
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Đã lưu mapping: {output_path}")
    print(f"  - Tổng số chunks: {len(mapping)}")


def load_mapping(mapping_path: Path) -> Dict[str, int]:
    """
    Load mapping từ file JSON
    
    Args:
        mapping_path: Đường dẫn file mapping
        
    Returns:
        Dictionary mapping chunk_id -> index
    """
    mapping_path = Path(mapping_path)
    
    if not mapping_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {mapping_path}")
    
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)
    
    mapping = mapping_data.get('mapping', mapping_data)
    print(f"✓ Đã load mapping: {mapping_path}")
    print(f"  - Tổng số chunks: {len(mapping)}")
    
    return mapping


def validate_embeddings(
    embeddings: np.ndarray,
    expected_count: Optional[int] = None,
    expected_dimension: Optional[int] = None
) -> bool:
    """
    Validate embeddings
    
    Args:
        embeddings: Numpy array chứa embeddings
        expected_count: Số lượng embeddings mong đợi
        expected_dimension: Dimension mong đợi
        
    Returns:
        True nếu hợp lệ, False nếu không
    """
    if embeddings is None or embeddings.size == 0:
        print("❌ Embeddings rỗng")
        return False
    
    if len(embeddings.shape) != 2:
        print(f"❌ Embeddings phải là 2D array, nhận được: {embeddings.shape}")
        return False
    
    count, dimension = embeddings.shape
    
    if expected_count and count != expected_count:
        print(f"❌ Số lượng embeddings không khớp: {count} != {expected_count}")
        return False
    
    if expected_dimension and dimension != expected_dimension:
        print(f"❌ Dimension không khớp: {dimension} != {expected_dimension}")
        return False
    
    # Kiểm tra NaN hoặc Inf
    if np.isnan(embeddings).any():
        print("❌ Embeddings chứa NaN")
        return False
    
    if np.isinf(embeddings).any():
        print("❌ Embeddings chứa Inf")
        return False
    
    print(f"✓ Embeddings hợp lệ: {count} vectors, dimension {dimension}")
    return True

