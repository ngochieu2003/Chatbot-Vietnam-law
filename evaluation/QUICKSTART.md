# 🚀 Quick Start - Đánh Giá Chatbot

Hướng dẫn nhanh để bắt đầu đánh giá chatbot.

## Bước 1: Chuẩn Bị

1. **Đảm bảo RAG System đã sẵn sàng:**
   ```bash
   # Kiểm tra index đã được tạo chưa
   ls VectorDB/data/index/faiss_index.bin
   
   # Nếu chưa có, chạy:
   python VectorDB/scripts/build_index.py
   ```

2. **Kiểm tra API key:**
   ```bash
   # Đảm bảo có GEMINI_API_KEY trong .env hoặc environment
   echo $GEMINI_API_KEY
   ```

## Bước 2: Chạy Đánh Giá

### Đánh giá chất lượng (Evaluation)

```bash
cd evaluation/scripts
python evaluator.py
```

**Tiết kiệm API quota:** Sử dụng `--max-tests` để giới hạn số test cases:
```bash
python evaluator.py --max-tests 1  # Chỉ chạy 1 test case
```

Kết quả sẽ được lưu tại: `evaluation/reports/evaluation_report_YYYYMMDD_HHMMSS.json`

> 💡 **Lưu ý:** File test dataset mặc định đã được giảm xuống 1 test case để tiết kiệm API quota.

### Benchmark hiệu suất

**Full benchmark (có gọi LLM - tốn API):**
```bash
cd evaluation/scripts
python benchmark.py
```

**Chỉ Search Benchmark (KHÔNG tốn API - khuyến nghị):**
```bash
cd evaluation/scripts
python search_benchmark_only.py
```

Script `search_benchmark_only.py` chỉ test FAISS retrieval, không gọi LLM nên:
- ✅ **0 API calls** - Không tốn quota
- ✅ Có thể test nhiều queries
- ✅ Đo retrieval performance chính xác

Kết quả sẽ được lưu tại: `evaluation/reports/benchmark_report_YYYYMMDD_HHMMSS.json` hoặc `search_benchmark_YYYYMMDD_HHMMSS.json`

## Bước 3: Xem Báo Cáo

### Tạo HTML report

```bash
cd evaluation/scripts
python generate_report.py ../reports/evaluation_report_20241126_120000.json
```

Mở file HTML trong browser để xem báo cáo đẹp mắt.

## 📊 Các Metrics Quan Trọng

- **Overall Score**: Điểm tổng hợp (0.0 - 1.0), càng cao càng tốt
- **Success Rate**: Tỷ lệ queries thành công
- **Average Query Time**: Thời gian trung bình mỗi query
- **Throughput (QPS)**: Số queries xử lý được mỗi giây

## 💡 Tips

1. **Thêm test cases mới**: Sửa file `test_data/sample_test_dataset.json`
2. **Tùy chỉnh metrics**: Sửa trong `metrics/evaluation_metrics.py`
3. **So sánh kết quả**: Lưu các reports để so sánh giữa các phiên bản

## ❓ Troubleshooting

- **Lỗi "Chưa load index"**: Chạy `VectorDB/scripts/build_index.py`
- **Lỗi API key**: Kiểm tra `.env` file hoặc environment variables
- **Kết quả thấp**: Kiểm tra test dataset có phù hợp không, có thể cần điều chỉnh expected keywords

Xem [README.md](README.md) để biết chi tiết đầy đủ.

