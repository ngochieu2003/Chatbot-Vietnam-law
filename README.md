# Chatbot RAG - Pháp Luật Việt Nam

Chatbot hỏi đáp về pháp luật Việt Nam sử dụng kiến trúc RAG (Retrieval-Augmented Generation).

## 📋 Tổng Quan

Dự án này xây dựng một hệ thống chatbot có khả năng trả lời câu hỏi về pháp luật Việt Nam bằng cách:
- Tìm kiếm thông tin liên quan từ database các văn bản pháp luật đã được xử lý
- Sử dụng LLM (Google Gemini) để tạo câu trả lời dựa trên thông tin tìm được
- Cung cấp nguồn tham khảo (điều luật, chương, văn bản) cho mỗi câu trả lời

## 🏗️ Kiến Trúc

```
Dataset → data_processing → Embeddings → VectorDB → RAG → App
```

### Các thành phần chính:

1. **Data Processing** (`data_processing/`): Xử lý và làm sạch dữ liệu pháp luật
2. **Embeddings** (`Embeddings/`): Tạo embeddings từ text chunks
3. **VectorDB** (`VectorDB/`): Quản lý FAISS index cho vector search
4. **RAG** (`RAG/`): Hệ thống RAG chính (retrieval + generation)
5. **App** (`App/`): FastAPI backend và Streamlit frontend
6. **Evaluation** (`evaluation/`): Module đánh giá chất lượng chatbot

## 🚀 Cài Đặt

### Yêu cầu

- Python 3.9+
- GEMINI_API_KEY (từ Google AI Studio)

### Cài đặt dependencies

```bash
# Cài đặt dependencies cho từng module
pip install -r App/requirements.txt
pip install -r RAG/requirements.txt
pip install -r VectorDB/requirements.txt
pip install -r Embeddings/requirements.txt
pip install -r data_processing/requirements.txt
pip install -r evaluation/requirements.txt
```

### Thiết lập môi trường

Tạo file `.env` trong thư mục gốc hoặc `RAG/models/`:

```env
GEMINI_API_KEY=your_api_key_here
```

## 📖 Sử Dụng

### 1. Chuẩn bị dữ liệu

```bash
# Xử lý dữ liệu
python data_processing/data_chunker.py
python data_processing/metadata_extractor.py

# Tạo embeddings
python Embeddings/scripts/create_embeddings.py

# Xây dựng FAISS index
python VectorDB/scripts/build_index.py
```

### 2. Chạy Backend API

```bash
cd App
uvicorn api.fastapi_app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Chạy Frontend

```bash
cd App
streamlit run frontend/streamlit_app.py
```

### 4. Đánh giá Chatbot

```bash
cd evaluation/scripts
python evaluator.py --max-tests 1  # Tiết kiệm API quota
```

Xem [evaluation/README.md](evaluation/README.md) để biết chi tiết.

## 📁 Cấu Trúc Thư Mục

```
chatbot_rag/
├── App/                    # Frontend và API
│   ├── api/               # FastAPI backend
│   └── frontend/           # Streamlit frontend
├── RAG/                    # Core RAG system
│   ├── models/            # RAGSystem class
│   └── utils/             # LLM utilities
├── VectorDB/               # FAISS vector database
├── Embeddings/             # Embedding generation
├── data_processing/        # Data preprocessing
├── evaluation/             # Evaluation module
└── Note/                   # Documentation
```

## ⚠️ Lưu Ý

- Các file lớn (>100MB) như `embeddings.npy`, `faiss_index.bin`, `chunks.json` không được commit vào Git
- Cần tạo các file này bằng cách chạy các scripts trong từng module
- Dataset gốc không được bao gồm trong repository

## 📚 Tài Liệu

- [Architecture Structure](Note/ARCHITECTURE_STRUCTURE.txt)
- [Project Summary](Note/PROJECT_SUMMARY.txt)
- [Evaluation Guide](evaluation/README.md)
- [Data Processing Guide](Note/README_DataProcess.md)

## 🔧 Công Nghệ Sử Dụng

- **LLM**: Google Gemini
- **Vector Database**: FAISS
- **Embeddings**: sentence-transformers
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Language**: Python 3.9+

## 📝 License

MIT License

## 👤 Tác Giả

Ngô Chiếu - [GitHub](https://github.com/ngochieu2003)

