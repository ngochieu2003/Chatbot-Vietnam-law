# VectorDB Module - FAISS Vector Database

Module này chứa code để tạo và quản lý Vector Database sử dụng FAISS.

## 📁 Cấu Trúc

```
VectorDB/
├── scripts/              # Scripts tạo và quản lý index
│   ├── __init__.py
│   └── build_index.py    # Script tạo FAISS index
├── models/               # Models và utilities
│   ├── __init__.py
│   └── faiss_manager.py  # Class quản lý FAISS index
├── utils/                # Utilities
│   ├── __init__.py
│   └── index_utils.py    # Helper functions
├── data/                 # Dữ liệu index
│   └── index/           # FAISS index files
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### 1. Cài đặt Dependencies

```bash
cd VectorDB
pip install -r requirements.txt
```

**Lưu ý:**
- Nếu có GPU: `pip install faiss-gpu` thay vì `faiss-cpu`
- Nếu không có GPU: `pip install faiss-cpu` (đã có trong requirements.txt)

### 2. Tạo FAISS Index

```bash
# Sử dụng default settings
python scripts/build_index.py

# Hoặc chỉ định paths
python scripts/build_index.py \
    --embeddings ../Embeddings/data/embeddings/embeddings.npy \
    --output data/index/faiss_index.bin
```

### 3. Kiểm tra Index

Sau khi chạy, bạn sẽ có:
- `data/index/faiss_index.bin` - FAISS index file
- `data/index/index_info.json` - Metadata về index

## 📋 Các Loại Index FAISS

### IndexFlatL2 (Mặc định)
- ✅ Đơn giản, chính xác 100%
- ✅ Phù hợp cho dataset < 1M vectors
- ❌ Chậm hơn với dataset lớn

### IndexIVFFlat (Khuyến nghị cho dataset lớn)
- ✅ Nhanh hơn với dataset > 100K vectors
- ✅ Có thể tune số clusters
- ❌ Cần training trước

### IndexHNSW (Nhanh nhất)
- ✅ Rất nhanh
- ✅ Phù hợp cho dataset rất lớn
- ❌ Tốn nhiều memory hơn

## 💻 Sử Dụng Trong Code

### Load và Sử Dụng Index

```python
from models.faiss_manager import FAISSManager

# Khởi tạo
manager = FAISSManager()

# Load index
manager.load_index(
    index_path="data/index/faiss_index.bin",
    embeddings_path="../Embeddings/data/embeddings/embeddings.npy",
    mapping_path="../Embeddings/data/mappings/chunk_mapping.json"
)

# Tìm kiếm
query_embedding = manager.embedding_model.encode(["Câu hỏi của bạn"])
results = manager.search(query_embedding, top_k=5)

# Lấy chunks
chunks = manager.get_chunks_by_indices(results['indices'])
```

## ⚙️ Cấu Hình

### Index Type

Trong `build_index.py`, bạn có thể chọn loại index:

```python
# IndexFlatL2 (mặc định - chính xác nhất)
index = faiss.IndexFlatL2(dimension)

# IndexIVFFlat (nhanh hơn cho dataset lớn)
nlist = 100  # Số clusters
quantizer = faiss.IndexFlatL2(dimension)
index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
index.train(embeddings)  # Cần training trước
```

## 📊 Performance

Với ~241,451 vectors (dimension 384):

| Index Type | Build Time | Search Time (1 query) | Memory |
|------------|------------|----------------------|--------|
| IndexFlatL2 | ~30s | ~50ms | ~370 MB |
| IndexIVFFlat | ~2min | ~5ms | ~400 MB |
| IndexHNSW | ~5min | ~1ms | ~500 MB |

## 🔧 Troubleshooting

### Lỗi: Out of Memory khi build index
- Giảm số vectors trong một lần
- Sử dụng IndexIVFFlat thay vì IndexFlatL2
- Tăng swap space

### Lỗi: Index không tìm thấy
- Kiểm tra đường dẫn đến embeddings file
- Đảm bảo đã chạy `build_index.py` trước

### Lỗi: Dimension không khớp
- Kiểm tra dimension của embeddings phải khớp với index
- Xem `index_info.json` để biết dimension

## 🔗 Liên Kết

- **Input**: `../Embeddings/data/embeddings/embeddings.npy`
- **Output**: Sử dụng trong `../RAG/` (Bước tiếp theo)

## 📝 Notes

- Index file có thể rất lớn (hàng trăm MB đến GB)
- Nên versioning index khi thay đổi embeddings
- IndexFlatL2 đủ tốt cho dataset < 1M vectors
- Với dataset lớn hơn, cân nhắc IndexIVFFlat hoặc IndexHNSW

