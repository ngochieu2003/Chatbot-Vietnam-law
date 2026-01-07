#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tạo FAISS index từ embeddings
Sử dụng: python scripts/build_index.py
"""

import json
import argparse
from pathlib import Path
from typing import Optional
import sys

# Thêm parent directory vào path để import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import faiss
from utils.index_utils import save_index_info, validate_index


def build_faiss_index(
    embeddings_path: Path,
    output_path: Path,
    index_type: str = 'flat',
    nlist: Optional[int] = None
) -> None:
    """
    Tạo FAISS index từ embeddings
    
    Args:
        embeddings_path: Đường dẫn file embeddings.npy
        output_path: Đường dẫn file output index
        index_type: Loại index ('flat', 'ivf', 'hnsw')
        nlist: Số clusters cho IndexIVFFlat (mặc định: sqrt(num_vectors))
    """
    print("="*70)
    print("TẠO FAISS INDEX")
    print("="*70)
    
    # Load embeddings
    print(f"\n[1/4] Đang load embeddings từ: {embeddings_path}")
    if not embeddings_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {embeddings_path}")
    
    embeddings = np.load(str(embeddings_path)).astype('float32')
    num_vectors, dimension = embeddings.shape
    
    print(f"✓ Đã load embeddings")
    print(f"  - Số vectors: {num_vectors:,}")
    print(f"  - Dimension: {dimension}")
    print(f"  - Size: {embeddings.nbytes / 1024 / 1024:.2f} MB")
    
    # Validate embeddings
    if not validate_index(embeddings):
        raise ValueError("Embeddings không hợp lệ!")
    
    # Tạo index
    print(f"\n[2/4] Đang tạo FAISS index (type: {index_type})...")
    
    if index_type == 'flat':
        # IndexFlatL2 - Chính xác nhất, phù hợp cho dataset < 1M
        index = faiss.IndexFlatL2(dimension)
        print("  - Sử dụng IndexFlatL2 (chính xác 100%)")
        
    elif index_type == 'ivf':
        # IndexIVFFlat - Nhanh hơn cho dataset lớn
        if nlist is None:
            nlist = int(np.sqrt(num_vectors))
            nlist = min(max(nlist, 10), 1000)  # Giới hạn 10-1000
        
        print(f"  - Sử dụng IndexIVFFlat với {nlist} clusters")
        quantizer = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
        
        # Training
        print(f"  - Đang training index...")
        index.train(embeddings)
        
    elif index_type == 'hnsw':
        # IndexHNSW - Nhanh nhất nhưng tốn memory
        M = 32  # Số connections mỗi node
        print(f"  - Sử dụng IndexHNSW với M={M}")
        index = faiss.IndexHNSWFlat(dimension, M)
        
    else:
        raise ValueError(f"Index type không hợp lệ: {index_type}. Chọn 'flat', 'ivf', hoặc 'hnsw'")
    
    # Add vectors vào index
    print(f"\n[3/4] Đang add {num_vectors:,} vectors vào index...")
    index.add(embeddings)
    
    print(f"✓ Đã tạo index")
    print(f"  - Total vectors trong index: {index.ntotal:,}")
    print(f"  - Index type: {type(index).__name__}")
    
    # Lưu index
    print(f"\n[4/4] Đang lưu index...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(output_path))
    
    # Lưu metadata
    index_info = {
        'index_type': index_type,
        'num_vectors': num_vectors,
        'dimension': dimension,
        'index_class': type(index).__name__,
        'embeddings_path': str(embeddings_path),
        'index_size_mb': output_path.stat().st_size / 1024 / 1024 if output_path.exists() else 0
    }
    
    if index_type == 'ivf' and nlist:
        index_info['nlist'] = nlist
    
    info_path = output_path.parent / f"{output_path.stem}_info.json"
    save_index_info(index_info, info_path)
    
    print(f"✓ Đã lưu index: {output_path}")
    print(f"✓ Đã lưu metadata: {info_path}")
    
    print("\n" + "="*70)
    print("HOÀN THÀNH!")
    print("="*70)
    print(f"\nOutput files:")
    print(f"  - Index: {output_path}")
    print(f"  - Info: {info_path}")
    print(f"\nIndex stats:")
    print(f"  - Vectors: {num_vectors:,}")
    print(f"  - Dimension: {dimension}")
    print(f"  - Type: {type(index).__name__}")
    print(f"  - Size: {index_info['index_size_mb']:.2f} MB")


def main():
    """Hàm main"""
    # Lấy đường dẫn gốc của project
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # Default paths
    default_embeddings = project_root / "Embeddings" / "data" / "embeddings" / "embeddings.npy"
    default_output = script_dir.parent / "data" / "index" / "faiss_index.bin"
    
    parser = argparse.ArgumentParser(description='Tạo FAISS index từ embeddings')
    
    parser.add_argument(
        '--embeddings',
        type=str,
        default=str(default_embeddings),
        help=f'Đường dẫn file embeddings.npy (default: {default_embeddings})'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=str(default_output),
        help=f'Đường dẫn file output index (default: {default_output})'
    )
    
    parser.add_argument(
        '--index-type',
        type=str,
        default='flat',
        choices=['flat', 'ivf', 'hnsw'],
        help='Loại index: flat (chính xác), ivf (nhanh), hnsw (rất nhanh) (default: flat)'
    )
    
    parser.add_argument(
        '--nlist',
        type=int,
        default=None,
        help='Số clusters cho IndexIVFFlat (mặc định: sqrt(num_vectors))'
    )
    
    args = parser.parse_args()
    
    # Convert to Path
    embeddings_path = Path(args.embeddings).resolve()
    output_path = Path(args.output).resolve()
    
    # Kiểm tra file input
    if not embeddings_path.exists():
        print(f"❌ Lỗi: Không tìm thấy file {embeddings_path}")
        return 1
    
    # Tạo index
    try:
        build_faiss_index(
            embeddings_path=embeddings_path,
            output_path=output_path,
            index_type=args.index_type,
            nlist=args.nlist
        )
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

