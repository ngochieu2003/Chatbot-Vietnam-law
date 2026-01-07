# 📊 Evaluation Module - Đánh Giá Chatbot RAG

Module này cung cấp các công cụ đánh giá hiệu suất và chất lượng của Chatbot RAG.

## 📁 Cấu Trúc Thư Mục

```
evaluation/
├── test_data/              # Test datasets (question-answer pairs)
│   └── sample_test_dataset.json
├── metrics/                # Evaluation metrics
│   └── evaluation_metrics.py
├── scripts/                # Evaluation scripts
│   ├── evaluator.py        # Script đánh giá chính
│   ├── benchmark.py        # Script benchmark performance
│   └── generate_report.py  # Script tạo HTML report
├── reports/                # Generated reports (JSON + HTML)
├── utils/                  # Utility functions
├── requirements.txt        # Dependencies
└── README.md              # File này
```

## 🚀 Cài Đặt

### 1. Cài đặt dependencies

```bash
cd evaluation
pip install -r requirements.txt
```

### 2. Chuẩn bị RAG System

Đảm bảo RAG System đã được setup và có:
- FAISS index đã được tạo (`VectorDB/data/index/faiss_index.bin`)
- Chunks file (`data_processing/chunks.json`)
- Mapping file (`Embeddings/data/mappings/chunk_mapping.json`)
- API key cho Gemini (trong `.env` hoặc environment variable)

## 📝 Sử Dụng

### 1. Đánh Giá Chatbot (Evaluation)

Chạy đánh giá trên test dataset:

```bash
cd evaluation/scripts
python evaluator.py
```

Script sẽ:
- Load test dataset từ `test_data/sample_test_dataset.json`
- Chạy từng test case qua RAG system
- Tính các metrics: keyword coverage, source relevance, answer quality, etc.
- Lưu kết quả vào `reports/evaluation_report_YYYYMMDD_HHMMSS.json`

**Kết quả bao gồm:**
- Tổng số test cases
- Tỷ lệ thành công
- Điểm trung bình
- Thời gian trung bình mỗi query
- Điểm theo category
- Chi tiết từng test case

### 2. Benchmark Performance

#### A. Search-Only Benchmark (Khuyến nghị - KHÔNG tốn API) ⭐

Chỉ đo FAISS retrieval performance, không gọi LLM:

```bash
cd evaluation/scripts
python search_benchmark_only.py
```

**Tùy chọn:**
```bash
python search_benchmark_only.py --queries 5 --iterations 3 --top-k 5
```

**Lợi ích:**
- ✅ **0 API calls** - Không tốn quota
- ✅ Có thể test nhiều queries
- ✅ Đo retrieval performance chính xác

#### B. Full Benchmark (Có gọi LLM - tốn API)

Đo toàn bộ hiệu suất hệ thống:

```bash
cd evaluation/scripts
python benchmark.py
```

Script sẽ đo:
- **Search performance**: Thời gian tìm kiếm (chỉ retrieval)
- **Query performance**: Thời gian full query (retrieval + generation)
- **Concurrent performance**: Hiệu suất khi có nhiều requests đồng thời

**Metrics:**
- Min/Max/Avg/Median time
- P95, P99 latency
- Throughput (QPS - Queries Per Second)

### 3. Tạo HTML Report

Tạo báo cáo HTML đẹp mắt từ kết quả JSON:

```bash
cd evaluation/scripts
python generate_report.py ../reports/evaluation_report_20241126_120000.json
```

Report sẽ được lưu tại `reports/evaluation_report_YYYYMMDD_HHMMSS.html`

## 📊 Metrics Đánh Giá

### 1. Keyword Coverage
Đánh giá độ bao phủ keywords mong đợi trong câu trả lời.

**Score**: 0.0 - 1.0 (tỷ lệ keywords được tìm thấy)

### 2. Source Relevance
Đánh giá độ liên quan của sources được retrieve so với sources mong đợi.

**Score**: 0.0 - 1.0 (tỷ lệ sources match)

### 3. Answer Quality
Đánh giá chất lượng câu trả lời:
- Có lỗi không (error keywords)
- Có câu hoàn chỉnh không
- Có nội dung thực sự không

**Score**: 0.0 - 1.0

### 4. Answer Length
Đánh giá độ dài câu trả lời (quá ngắn hoặc quá dài đều không tốt).

**Score**: 0.0 - 1.0

### 5. Retrieval Quality
Đánh giá chất lượng retrieval dựa trên distances từ FAISS.

**Score**: 0.0 - 1.0 (distance càng nhỏ càng tốt)

### 6. Overall Score
Điểm tổng hợp từ tất cả metrics với trọng số:
- Keyword Coverage: 25%
- Source Relevance: 20%
- Answer Quality: 30%
- Retrieval Quality: 15%
- Answer Length: 10%

## 📋 Test Dataset Format

Test dataset là file JSON với format:

```json
[
    {
        "id": "test_001",
        "question": "Phạm vi điều chỉnh của luật là gì?",
        "expected_answer_keywords": ["phạm vi", "điều chỉnh", "luật"],
        "expected_sources": ["Điều 1", "Điều 2"],
        "category": "general",
        "difficulty": "easy"
    }
]
```

**Fields:**
- `id`: ID duy nhất của test case
- `question`: Câu hỏi để test
- `expected_answer_keywords`: List keywords mong đợi trong câu trả lời
- `expected_sources`: List sources (điều luật, chương) mong đợi
- `category`: Category của câu hỏi (general, procedural, business, etc.)
- `difficulty`: Độ khó (easy, medium, hard)

## 🔧 Tùy Chỉnh

### Thay đổi trọng số metrics

Sửa trong `evaluation/scripts/evaluator.py`:

```python
overall_score = self.metrics.compute_overall_score(
    keyword_coverage['score'],
    source_relevance['score'],
    answer_quality['score'],
    retrieval_quality['quality_score'],
    answer_length,
    weights={
        'keyword_coverage': 0.30,  # Tăng trọng số
        'source_relevance': 0.20,
        'answer_quality': 0.30,
        'retrieval_quality': 0.15,
        'answer_length': 0.05      # Giảm trọng số
    }
)
```

### Thêm test cases

Thêm vào `test_data/sample_test_dataset.json` hoặc tạo file mới.

### Tùy chỉnh metrics

Sửa trong `evaluation/metrics/evaluation_metrics.py` để thêm metrics mới hoặc thay đổi logic tính toán.

## 📈 Ví Dụ Kết Quả

### Evaluation Results

```
📈 TỔNG KẾT ĐÁNH GIÁ
============================================================
Tổng số test: 10
Thành công: 9
Thất bại: 1
Tỷ lệ thành công: 90.0%
Điểm trung bình: 0.75
Thời gian trung bình: 2.34s
Tổng thời gian: 23.40s

Điểm theo category:
  - general: 0.82
  - procedural: 0.68
  - business: 0.71
============================================================
```

### Benchmark Results

```
📈 TỔNG KẾT BENCHMARK
============================================================

🔍 Search Performance:
   Avg time: 0.123s
   Throughput: 8.13 QPS
   P95: 0.156s

🤖 Full Query Performance:
   Avg time: 2.345s
   Throughput: 0.43 QPS
   P95: 3.120s
   Avg answer length: 450 chars

⚡ Concurrent Performance:
   Success rate: 10/10
   Throughput: 1.25 QPS
============================================================
```

## 🐛 Troubleshooting

### Lỗi: "Chưa load index!"
- Đảm bảo đã chạy `VectorDB/scripts/build_index.py` để tạo FAISS index

### Lỗi: "GEMINI_API_KEY not found"
- Thêm `GEMINI_API_KEY` vào file `.env` hoặc export environment variable

### Lỗi: "No test dataset found"
- Kiểm tra file `test_data/sample_test_dataset.json` có tồn tại không

## 📚 Tài Liệu Tham Khảo

- [RAG System Documentation](../RAG/)
- [FAISS Manager Documentation](../VectorDB/)
- [Project Architecture](../Note/ARCHITECTURE_STRUCTURE.txt)

## 🤝 Đóng Góp

Để thêm metrics mới hoặc cải thiện evaluation:
1. Thêm metric vào `evaluation/metrics/evaluation_metrics.py`
2. Tích hợp vào `evaluation/scripts/evaluator.py`
3. Cập nhật documentation

## 📝 License

Cùng với dự án chính.

