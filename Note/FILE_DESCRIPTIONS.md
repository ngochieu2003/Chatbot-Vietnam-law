# Mô Tả Chi Tiết Vai Trò Các File Code

Tài liệu này mô tả chi tiết vai trò, chức năng và cách sử dụng của từng file code trong thư mục `data_processing`.

---

## 📋 Tổng Quan

Thư mục `data_processing` chứa các module xử lý dữ liệu pháp điển, được thiết kế theo kiến trúc modular để dễ bảo trì và mở rộng. Các file được sắp xếp theo thứ tự xử lý: Phân tích → Làm sạch → Trích xuất → Chia nhỏ → Chuẩn hóa → Pipeline.

---

## 📁 Chi Tiết Từng File

### 1. `analyze_data_quality.py` 
**Vai trò:** Phân tích và đánh giá chất lượng dữ liệu ban đầu

**Chức năng chính:**
- Phân tích cấu trúc dữ liệu HTML trong thư mục `Dataset/demuc`
- Đếm số lượng file, điều luật, chương
- Kiểm tra encoding, cấu trúc HTML
- Phát hiện các vấn đề: HTML tags, scripts, styles
- Tạo báo cáo chất lượng dữ liệu (`data_quality_report.json`)
- Đưa ra khuyến nghị xử lý theo mức độ ưu tiên (HIGH/MEDIUM/LOW)

**Class chính:**
- `DataQualityAnalyzer`: Class chính thực hiện phân tích

**Output:**
- `data_quality_report.json`: Báo cáo chi tiết về chất lượng dữ liệu
- Thống kê: tổng số file, điều luật, kích thước, các vấn đề phát hiện

**Cách sử dụng:**
```python
from analyze_data_quality import DataQualityAnalyzer

analyzer = DataQualityAnalyzer()
results = analyzer.analyze()
```

**Khi nào sử dụng:**
- Trước khi bắt đầu xử lý dữ liệu để hiểu rõ dataset
- Để xác định các vấn đề cần xử lý
- Để đánh giá chất lượng dữ liệu sau khi thu thập

---

### 2. `data_cleaner.py`
**Vai trò:** Làm sạch dữ liệu HTML - Loại bỏ HTML tags và trích xuất văn bản thuần túy

**Ưu tiên:** HIGH (Theo khuyến nghị từ phân tích chất lượng)

**Chức năng chính:**
- Parse HTML sử dụng BeautifulSoup
- Loại bỏ các thẻ `<script>` và `<style>`
- Trích xuất văn bản từ các phần tử có cấu trúc:
  - `pDieu`: Điều luật
  - `pChuong`: Chương
  - `pNoiDung`: Nội dung điều luật
  - `pGhiChu`: Ghi chú (metadata)
  - `pChiDan`: Chỉ dẫn liên quan
- Làm sạch văn bản: loại bỏ khoảng trắng thừa, chuẩn hóa
- Giữ lại cấu trúc logic của văn bản

**Class chính:**
- `DataCleaner`: Class thực hiện làm sạch dữ liệu

**Methods quan trọng:**
- `clean_html_file()`: Làm sạch một file HTML
- `clean_all_files()`: Làm sạch tất cả file trong thư mục
- `_extract_structured_content()`: Trích xuất nội dung có cấu trúc
- `_extract_element_text()`: Trích xuất text từ từng phần tử
- `_clean_text()`: Làm sạch văn bản

**Output:**
- Các file `.txt` đã được làm sạch (nếu chạy riêng)
- Hoặc dữ liệu đã làm sạch được truyền trực tiếp cho bước tiếp theo

**Cách sử dụng:**
```python
from data_cleaner import DataCleaner
from pathlib import Path

cleaner = DataCleaner()
input_dir = Path("../Dataset/demuc")
output_dir = Path("cleaned_data")
result = cleaner.clean_all_files(input_dir, output_dir)
```

**Khi nào sử dụng:**
- Bước đầu tiên trong pipeline xử lý dữ liệu
- Cần thiết để loại bỏ HTML tags trước khi tạo embeddings
- Giúp giảm noise trong dữ liệu

---

### 3. `metadata_extractor.py`
**Vai trò:** Trích xuất metadata từ các điều luật

**Ưu tiên:** MEDIUM (Theo khuyến nghị từ phân tích chất lượng)

**Chức năng chính:**
- Trích xuất thông tin đề mục (số đề mục, tên đề mục)
- Trích xuất thông tin chương (số chương, tên chương)
- Trích xuất thông tin điều luật:
  - Số điều, tên điều, ID điều
- Trích xuất metadata từ ghi chú:
  - Loại văn bản (Luật/Nghị định/Thông tư/Pháp lệnh)
  - Số văn bản
  - Ngày ban hành
  - Ngày hiệu lực
  - Cơ quan ban hành
- Parse và chuẩn hóa ngày tháng (dd/mm/yyyy → yyyy-mm-dd)

**Class chính:**
- `MetadataExtractor`: Class trích xuất metadata

**Methods quan trọng:**
- `extract_from_html_file()`: Trích xuất metadata từ một file HTML
- `extract_all_files()`: Trích xuất từ tất cả file
- `_extract_demuc_info()`: Trích xuất thông tin đề mục
- `_extract_chuong_info()`: Trích xuất thông tin chương
- `_extract_dieu_info()`: Trích xuất thông tin điều luật
- `_extract_ghi_chu_info()`: Trích xuất metadata từ ghi chú
- `_parse_date()`: Parse ngày tháng

**Output:**
- `metadata.json`: File JSON chứa metadata của tất cả điều luật
- Mỗi entry chứa: file_id, đề mục, chương, điều, ngày ban hành, hiệu lực, loại văn bản

**Cách sử dụng:**
```python
from metadata_extractor import MetadataExtractor
from pathlib import Path

extractor = MetadataExtractor()
input_dir = Path("../Dataset/demuc")
output_file = Path("metadata.json")
result = extractor.extract_all_files(input_dir, output_file)
```

**Khi nào sử dụng:**
- Sau bước làm sạch dữ liệu
- Cần thiết để tạo metadata cho RAG system
- Giúp filter và tìm kiếm theo loại văn bản, ngày ban hành

---

### 4. `data_chunker.py`
**Vai trò:** Chia nhỏ dữ liệu thành các chunks theo điều luật

**Ưu tiên:** MEDIUM (Theo khuyến nghị từ phân tích chất lượng)

**Chức năng chính:**
- Chia dữ liệu thành các chunks, mỗi chunk = 1 điều luật
- Giữ lại cấu trúc: Chương → Điều → Ghi chú → Nội dung
- Xử lý điều luật dài: tự động chia nhỏ với overlap
- Tạo metadata cho mỗi chunk
- Hỗ trợ overlap giữa các chunks để không mất context

**Class chính:**
- `DataChunker`: Class chia nhỏ dữ liệu

**Parameters:**
- `chunk_size`: Kích thước tối đa mỗi chunk (mặc định: 1000 ký tự)
- `chunk_overlap`: Số ký tự overlap giữa các chunks (mặc định: 200)

**Methods quan trọng:**
- `chunk_html_file()`: Chia nhỏ một file HTML
- `chunk_all_files()`: Chia nhỏ tất cả file
- `_create_chunk()`: Tạo một chunk từ thông tin điều luật
- `_split_long_content()`: Chia nhỏ nội dung quá dài

**Output:**
- `chunks.json`: File JSON chứa tất cả chunks
- Mỗi chunk có: `id`, `content`, `metadata`

**Cấu trúc chunk:**
```json
{
  "id": "file_id_0",
  "content": "Chương: ...\nĐiều: ...\nNội dung: ...",
  "metadata": {
    "file_id": "...",
    "chuong": "...",
    "dieu": "...",
    "ghi_chu": "..."
  }
}
```

**Cách sử dụng:**
```python
from data_chunker import DataChunker
from pathlib import Path

chunker = DataChunker(chunk_size=1000, chunk_overlap=200)
input_dir = Path("../Dataset/demuc")
metadata_file = Path("metadata.json")
output_file = Path("chunks.json")
result = chunker.chunk_all_files(input_dir, metadata_file, output_file)
```

**Khi nào sử dụng:**
- Sau bước trích xuất metadata
- Cần thiết để tạo embeddings cho RAG system
- Mỗi chunk sẽ được vectorize riêng để tìm kiếm chính xác

**Lưu ý:**
- Chunking theo điều luật giúp RAG system tìm kiếm chính xác hơn
- Có thể điều chỉnh `chunk_size` và `chunk_overlap` tùy nhu cầu

---

### 5. `text_normalizer.py`
**Vai trò:** Chuẩn hóa văn bản tiếng Việt

**Ưu tiên:** LOW (Theo khuyến nghị từ phân tích chất lượng)

**Chức năng chính:**
- Loại bỏ các ký tự điều khiển không cần thiết
- Chuẩn hóa khoảng trắng: nhiều khoảng trắng → 1 khoảng trắng
- Chuẩn hóa dấu câu: loại bỏ khoảng trắng trước dấu câu
- Chuẩn hóa dấu ngoặc kép, gạch ngang
- Loại bỏ khoảng trắng thừa ở đầu/cuối dòng
- Chuẩn hóa các dòng trống: nhiều dòng trống → tối đa 2 dòng

**Class chính:**
- `TextNormalizer`: Class chuẩn hóa văn bản

**Methods quan trọng:**
- `normalize()`: Chuẩn hóa một đoạn văn bản
- `normalize_chunk()`: Chuẩn hóa một chunk
- `normalize_chunks()`: Chuẩn hóa một list chunks
- `_remove_control_characters()`: Loại bỏ ký tự điều khiển
- `_normalize_whitespace()`: Chuẩn hóa khoảng trắng
- `_normalize_punctuation()`: Chuẩn hóa dấu câu
- `_trim_lines()`: Loại bỏ khoảng trắng đầu/cuối dòng
- `_normalize_newlines()`: Chuẩn hóa dòng trống

**Output:**
- Văn bản đã được chuẩn hóa (không tạo file riêng, xử lý trực tiếp)

**Cách sử dụng:**
```python
from text_normalizer import TextNormalizer

normalizer = TextNormalizer()
text = "Điều   1.   Phạm vi điều chỉnh"
normalized = normalizer.normalize(text)

# Hoặc chuẩn hóa chunks
chunks = [...]  # List các chunks
normalized_chunks = normalizer.normalize_chunks(chunks)
```

**Khi nào sử dụng:**
- Bước cuối cùng trong pipeline trước khi tạo embeddings
- Giúp cải thiện chất lượng embeddings
- Giảm noise trong dữ liệu

---

### 6. `data_pipeline.py`
**Vai trò:** Pipeline xử lý dữ liệu chính - Kết hợp tất cả các bước

**Chức năng chính:**
- Điều phối toàn bộ quá trình xử lý dữ liệu
- Chạy các bước theo thứ tự:
  1. Làm sạch dữ liệu (DataCleaner)
  2. Trích xuất metadata (MetadataExtractor)
  3. Chia nhỏ dữ liệu (DataChunker)
  4. Chuẩn hóa văn bản (TextNormalizer)
- Tạo thống kê chi tiết cho mỗi bước
- Lưu kết quả vào thư mục `Dataset/processed/`

**Class chính:**
- `DataPipeline`: Class điều phối pipeline

**Parameters:**
- `dataset_path`: Đường dẫn đến thư mục Dataset
- `output_dir`: Thư mục lưu kết quả (mặc định: `dataset_path/processed`)
- `chunk_size`: Kích thước chunk (mặc định: 1000)
- `chunk_overlap`: Overlap giữa chunks (mặc định: 200)

**Methods quan trọng:**
- `run()`: Chạy toàn bộ pipeline
- `_print_summary()`: In tóm tắt kết quả

**Output:**
- `Dataset/processed/cleaned/`: Các file đã làm sạch (nếu không skip)
- `Dataset/processed/metadata.json`: Metadata của điều luật
- `Dataset/processed/chunks.json`: Các chunks chưa chuẩn hóa
- `Dataset/processed/chunks_normalized.json`: **Các chunks đã sẵn sàng cho embedding**
- `Dataset/processed/pipeline_stats.json`: Thống kê chi tiết

**Cách sử dụng:**
```python
from data_pipeline import DataPipeline
from pathlib import Path

# Từ thư mục data_processing
base_path = Path(__file__).parent.parent
dataset_path = base_path / "Dataset"

pipeline = DataPipeline(
    dataset_path=dataset_path,
    chunk_size=1000,
    chunk_overlap=200
)

# Chạy pipeline
stats = pipeline.run(skip_cleaning=False)
```

**Hoặc chạy trực tiếp:**
```bash
cd "data_processing"
python data_pipeline.py
```

**Khi nào sử dụng:**
- Khi muốn chạy toàn bộ quá trình xử lý dữ liệu một lần
- File chính để xử lý dữ liệu trước khi tạo embeddings
- Tạo ra `chunks_normalized.json` - file cuối cùng sẵn sàng cho bước tiếp theo

---

## 🔄 Luồng Xử Lý Dữ Liệu

```
1. analyze_data_quality.py
   ↓ (Phân tích và đánh giá)
   
2. data_pipeline.py
   ├──→ data_cleaner.py (Làm sạch HTML)
   ├──→ metadata_extractor.py (Trích xuất metadata)
   ├──→ data_chunker.py (Chia nhỏ dữ liệu)
   └──→ text_normalizer.py (Chuẩn hóa văn bản)
   ↓
   
3. Output: chunks_normalized.json
   ↓
   
4. Bước tiếp theo (xem NEXT_STEPS.md):
   - Tạo embeddings
   - Xây dựng vector database
   - Xây dựng RAG system
```

---

## 📊 Dependencies

Tất cả các file sử dụng các thư viện sau (xem `requirements.txt`):
- `beautifulsoup4`: Parse và xử lý HTML
- `lxml`: Parser cho BeautifulSoup
- `python-dateutil`: Xử lý ngày tháng (optional)

---

## 🎯 Kết Quả Cuối Cùng

Sau khi chạy `data_pipeline.py`, bạn sẽ có:
- **`chunks_normalized.json`**: File quan trọng nhất, chứa các chunks đã sẵn sàng để:
  - Tạo vector embeddings
  - Xây dựng vector database (FAISS/Chroma)
  - Sử dụng trong RAG system

Mỗi chunk trong file này có cấu trúc:
```json
{
  "id": "unique_chunk_id",
  "content": "Nội dung điều luật đã được làm sạch và chuẩn hóa",
  "metadata": {
    "file_id": "...",
    "chuong": "...",
    "dieu": "...",
    "ngay_ban_hanh": "...",
    "ngay_hieu_luc": "...",
    "loai_van_ban": "..."
  }
}
```

---

## 💡 Lưu Ý Quan Trọng

1. **Thứ tự chạy:**
   - Có thể chạy `analyze_data_quality.py` trước để hiểu dữ liệu
   - Sau đó chạy `data_pipeline.py` để xử lý toàn bộ

2. **Chạy riêng lẻ:**
   - Các module có thể chạy độc lập nếu cần
   - Mỗi module có hàm `main()` để test

3. **Đường dẫn:**
   - Tất cả các file đã được cấu hình để trỏ đến `../Dataset/demuc`
   - Kết quả được lưu trong `Dataset/processed/`

4. **Performance:**
   - Với ~40,000 điều luật, pipeline có thể mất vài phút
   - Có thể tối ưu bằng cách chạy song song (chưa implement)

---

## 📚 Tài Liệu Liên Quan

- `README.md`: Hướng dẫn sử dụng nhanh
- `NEXT_STEPS.md`: Hướng dẫn các bước tiếp theo (tạo embeddings, RAG system)
- `requirements.txt`: Danh sách dependencies

---

**Tạo bởi:** AI Engineer  
**Ngày:** 2024  
**Mục đích:** Xử lý dữ liệu pháp điển cho Chatbot RAG



