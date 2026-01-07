#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tạo embeddings từ chunks
Sử dụng: python scripts/create_embeddings.py
"""

import json
import argparse
from pathlib import Path
from typing import Optional
import sys

# Thêm parent directory vào path để import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.embedding_model import EmbeddingModel
from utils.embedding_utils import (
    save_embeddings,
    save_mapping,
    validate_embeddings
)


def create_embeddings(
    chunks_file: Path,
    output_dir: Path,
    model_name: str = 'multilingual-minilm',
    batch_size: int = 32,
    version: Optional[str] = None
) -> None:
    """
    Tạo embeddings từ chunks
    
    Args:
        chunks_file: Đường dẫn file chunks.json
        output_dir: Thư mục lưu output
        model_name: Tên model (key trong SUPPORTED_MODELS)
        batch_size: Kích thước batch
        version: Version của embeddings (ví dụ: 'v1', 'v2')
    """
    print("="*70)
    print("TẠO EMBEDDINGS TỪ CHUNKS")
    print("="*70)
    
    # Load chunks
    print(f"\n[1/5] Đang load chunks từ: {chunks_file}")
    if not chunks_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {chunks_file}")
    
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks_raw = json.load(f)
    
    print(f"✓ Đã load {len(chunks_raw)} items từ file")
    
    # Flatten cấu trúc: một số items có thể là list chứa nhiều chunks
    print(f"  Đang flatten cấu trúc dữ liệu...")
    chunks = []
    for item in chunks_raw:
        if isinstance(item, list):
            # Nếu là list, thêm tất cả các dicts trong list
            chunks.extend([chunk for chunk in item if isinstance(chunk, dict)])
        elif isinstance(item, dict):
            # Nếu là dict, thêm trực tiếp
            chunks.append(item)
        else:
            print(f"  ⚠️  Bỏ qua item không hợp lệ: {type(item)}")
    
    print(f"✓ Đã flatten thành {len(chunks)} chunks")
    
    # Khởi tạo model
    print(f"\n[2/5] Đang khởi tạo embedding model: {model_name}")
    embedding_model = EmbeddingModel(model_name=model_name)
    model_info = embedding_model.get_model_info()
    
    # Tạo mapping
    print(f"\n[3/5] Đang tạo mapping...")
    mapping = {chunk['id']: i for i, chunk in enumerate(chunks) if isinstance(chunk, dict) and 'id' in chunk}
    reverse_mapping = {i: chunk['id'] for i, chunk in enumerate(chunks) if isinstance(chunk, dict) and 'id' in chunk}
    print(f"✓ Đã tạo mapping cho {len(mapping)} chunks")
    
    # Tạo embeddings
    print(f"\n[4/5] Đang tạo embeddings...")
    print(f"  - Batch size: {batch_size}")
    print(f"  - Tổng số chunks: {len(chunks)}")
    
    texts = [chunk['content'] for chunk in chunks if isinstance(chunk, dict) and 'content' in chunk]
    embeddings = embedding_model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True
    )
    
    print(f"✓ Đã tạo embeddings")
    print(f"  - Shape: {embeddings.shape}")
    print(f"  - Dimension: {embeddings.shape[1]}")
    
    # Validate embeddings
    print(f"\n[5/5] Đang validate embeddings...")
    if not validate_embeddings(embeddings, expected_count=len(chunks)):
        raise ValueError("Embeddings không hợp lệ!")
    
    # Tạo tên file
    version_suffix = f"_{version}" if version else ""
    embeddings_file = output_dir / "data" / "embeddings" / f"embeddings{version_suffix}.npy"
    mapping_file = output_dir / "data" / "mappings" / f"chunk_mapping{version_suffix}.json"
    
    # Lưu embeddings
    metadata = {
        'model_name': model_name,
        'model_info': model_info,
        'total_chunks': len(chunks),
        'batch_size': batch_size
    }
    save_embeddings(embeddings, embeddings_file, metadata)
    
    # Lưu mapping
    save_mapping(mapping, mapping_file, reverse_mapping)
    
    # Lưu model info
    model_info_file = output_dir / "data" / "metadata" / f"model_info{version_suffix}.json"
    model_info_file.parent.mkdir(parents=True, exist_ok=True)
    with open(model_info_file, 'w', encoding='utf-8') as f:
        json.dump(model_info, f, ensure_ascii=False, indent=2)
    print(f"✓ Đã lưu model info: {model_info_file}")
    
    print("\n" + "="*70)
    print("HOÀN THÀNH!")
    print("="*70)
    print(f"\nOutput files:")
    print(f"  - Embeddings: {embeddings_file}")
    print(f"  - Mapping: {mapping_file}")
    print(f"  - Model info: {model_info_file}")


def main():
    """Hàm main"""
    # Lấy đường dẫn gốc của project (2 level lên từ scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    default_chunks_path = project_root / "data_processing" / "chunks.json"
    
    parser = argparse.ArgumentParser(description='Tạo embeddings từ chunks')
    
    parser.add_argument(
        '--input',
        type=str,
        default=str(default_chunks_path),
        help=f'Đường dẫn file chunks.json (default: {default_chunks_path})'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='.',
        help='Thư mục output (default: current directory)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='multilingual-minilm',
        choices=list(EmbeddingModel.SUPPORTED_MODELS.keys()),
        help='Tên model (default: multilingual-minilm)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Kích thước batch (default: 32)'
    )
    
    parser.add_argument(
        '--version',
        type=str,
        default=None,
        help='Version của embeddings (ví dụ: v1, v2)'
    )
    
    args = parser.parse_args()
    
    # Convert to Path và resolve
    input_path = Path(args.input)
    # Nếu là relative path, resolve từ project root
    if not input_path.is_absolute():
        input_path = project_root / input_path
    chunks_file = input_path.resolve()
    
    output_path = Path(args.output)
    # Nếu output là relative path và là '.', dùng thư mục Embeddings
    if output_path == Path('.'):
        output_dir = script_dir.parent  # Thư mục Embeddings
    elif not output_path.is_absolute():
        output_dir = (script_dir.parent / output_path).resolve()
    else:
        output_dir = output_path.resolve()
    
    # Kiểm tra file input
    if not chunks_file.exists():
        print(f"❌ Lỗi: Không tìm thấy file {chunks_file}")
        print(f"  Đường dẫn đã thử: {chunks_file}")
        print(f"  Thư mục project root: {project_root}")
        print(f"\nCác models được hỗ trợ:")
        for key, value in EmbeddingModel.SUPPORTED_MODELS.items():
            print(f"  - {key}: {value}")
        return 1
    
    # Tạo embeddings
    try:
        create_embeddings(
            chunks_file=chunks_file,
            output_dir=output_dir,
            model_name=args.model,
            batch_size=args.batch_size,
            version=args.version
        )
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

