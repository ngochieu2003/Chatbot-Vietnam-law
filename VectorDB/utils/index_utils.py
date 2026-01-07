#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Index Utilities
Helper functions cho việc quản lý FAISS index
"""

import json
from pathlib import Path
from typing import Dict, Optional
import numpy as np
from datetime import datetime


def save_index_info(
    index_info: Dict,
    output_path: Path
) -> None:
    """
    Lưu metadata về index
    
    Args:
        index_info: Dictionary chứa thông tin index
        output_path: Đường dẫn file output
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    index_info['created_at'] = datetime.now().isoformat()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index_info, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Đã lưu index info: {output_path}")


def load_index_info(info_path: Path) -> Dict:
    """
    Load metadata về index
    
    Args:
        info_path: Đường dẫn file info
        
    Returns:
        Dictionary chứa thông tin index
    """
    info_path = Path(info_path)
    
    if not info_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {info_path}")
    
    with open(info_path, 'r', encoding='utf-8') as f:
        info = json.load(f)
    
    print(f"✓ Đã load index info: {info_path}")
    return info


def validate_index(
    embeddings: np.ndarray,
    expected_dimension: Optional[int] = None
) -> bool:
    """
    Validate embeddings trước khi tạo index
    
    Args:
        embeddings: Numpy array chứa embeddings
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
    
    num_vectors, dimension = embeddings.shape
    
    if num_vectors == 0:
        print("❌ Không có vectors nào")
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
    
    # Kiểm tra dtype
    if embeddings.dtype != np.float32:
        print(f"⚠️  Embeddings dtype là {embeddings.dtype}, nên là float32")
        print("   Đang convert sang float32...")
        embeddings = embeddings.astype('float32')
    
    print(f"✓ Embeddings hợp lệ: {num_vectors:,} vectors, dimension {dimension}")
    return True

