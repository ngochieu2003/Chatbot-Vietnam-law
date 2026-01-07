# Dataset Processing - Chatbot RAG Pháp Luật

## 📁 Cấu Trúc Files

```
chatbot_rag/
├── data_processing/                # Thư mục chứa các script xử lý dữ liệu
│   ├── analyze_data_quality.py      # Phân tích chất lượng dữ liệu
│   ├── data_cleaner.py              # Làm sạch HTML
│   ├── metadata_extractor.py        # Trích xuất metadata
│   ├── data_chunker.py              # Chia nhỏ dữ liệu
│   ├── text_normalizer.py           # Chuẩn hóa văn bản
│   ├── data_pipeline.py             # Pipeline xử lý chính
│   ├── requirements.txt             # Dependencies
│   ├── NEXT_STEPS.md                # Hướng dẫn các bước tiếp theo
│   └── README.md                    # File này
└── Dataset/                      # Thư mục chứa dữ liệu gốc
    ├── demuc/                        # Thư mục chứa file HTML gốc
    ├── BoPhapDien.html
    └── lib/                          # Thư mục chứa CSS/JS
```

## 🚀 Quick Start

### 1. Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

### 2. Chạy Pipeline Xử Lý Dữ Liệu

```bash
python data_pipeline.py
```

Pipeline sẽ:
1. Làm sạch HTML files
2. Trích xuất metadata
3. Chia nhỏ thành chunks
4. Chuẩn hóa văn bản

Kết quả sẽ được lưu trong thư mục `Dataset/processed/`:
- `chunks_normalized.json`: Chunks sẵn sàng cho embedding
- `metadata.json`: Metadata của điều luật
- `pipeline_stats.json`: Thống kê

### 3. Xem Hướng Dẫn Chi Tiết

Xem file `NEXT_STEPS.md` để biết các bước tiếp theo:
- Tạo embeddings
- Xây dựng vector database
- Xây dựng RAG system
- Tích hợp LLM
- Deployment

## 📊 Kết Quả Phân Tích Dữ Liệu

Theo báo cáo `data_quality_report.json`:
- **Tổng số file**: 304 (303 HTML + 1 BoPhapDien.html)
- **Tổng số điều luật ước tính**: ~40,662
- **Kích thước**: ~4.6 MB
- **Đánh giá**: Dữ liệu có cấu trúc tốt, cần làm sạch HTML tags

## 🔧 Sử Dụng Từng Module Riêng Lẻ

### Làm sạch dữ liệu
```python
from data_cleaner import DataCleaner
from pathlib import Path

cleaner = DataCleaner()
base_path = Path(__file__).parent.parent
cleaner.clean_all_files(
    base_path / "Dataset" / "demuc",
    Path("cleaned_data")
)
```

### Trích xuất metadata
```python
from metadata_extractor import MetadataExtractor
from pathlib import Path

extractor = MetadataExtractor()
base_path = Path(__file__).parent.parent
extractor.extract_all_files(
    base_path / "Dataset" / "demuc",
    Path("metadata.json")
)
```

### Chia nhỏ dữ liệu
```python
from data_chunker import DataChunker
from pathlib import Path

chunker = DataChunker(chunk_size=1000, chunk_overlap=200)
base_path = Path(__file__).parent.parent
chunker.chunk_all_files(
    base_path / "Dataset" / "demuc",
    Path("metadata.json"),
    Path("chunks.json")
)
```

## 📝 Notes

- Tất cả các file đều hỗ trợ encoding UTF-8
- Các module có thể chạy độc lập hoặc qua pipeline
- Xem docstring trong mỗi file để biết chi tiết API

