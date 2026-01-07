# Hướng Dẫn Các Bước Tiếp Theo - Xây Dựng Chatbot RAG

## 📋 Tổng Quan

Sau khi đã xử lý dữ liệu theo các khuyến nghị từ báo cáo phân tích chất lượng, bạn cần thực hiện các bước sau để xây dựng hệ thống chatbot RAG (Retrieval-Augmented Generation) hoàn chỉnh.

---

## 🚀 Bước 1: Chạy Pipeline Xử Lý Dữ Liệu

### 1.1. Cài đặt Dependencies

```bash
cd Dataset
pip install -r requirements.txt
```

### 1.2. Chạy Pipeline Xử Lý Dữ Liệu

```bash
python data_pipeline.py
```

Pipeline sẽ thực hiện các bước:
- ✅ Làm sạch HTML (loại bỏ tags, scripts, styles)
- ✅ Trích xuất metadata (số điều, chương, ngày ban hành, hiệu lực...)
- ✅ Chia nhỏ dữ liệu thành chunks (mỗi chunk = 1 điều luật)
- ✅ Chuẩn hóa văn bản (loại bỏ khoảng trắng thừa, chuẩn hóa dấu câu)

**Kết quả:** Thư mục `processed/` chứa:
- `chunks_normalized.json`: Các chunks đã sẵn sàng cho embedding
- `metadata.json`: Metadata của tất cả điều luật
- `pipeline_stats.json`: Thống kê quá trình xử lý

---

## 🔍 Bước 2: Tạo Vector Embeddings

### 2.1. Chọn Embedding Model

**Khuyến nghị cho tiếng Việt:**

1. **Multilingual Models (Khuyến nghị):**
   - `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (nhẹ, nhanh)
   - `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (chất lượng cao hơn)
   - `intfloat/multilingual-e5-base` (chất lượng rất cao)

2. **Vietnamese-Specific Models:**
   - `keepitreal/vietnamese-sbert` (chuyên cho tiếng Việt)
   - `VoVanPhuc/sup-SimCSE-VietNamese-phobert-base`

### 2.2. Tạo File Embedding

Tạo file `create_embeddings.py`:

```python
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

# Load model
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Load chunks
chunks_file = Path("processed/chunks_normalized.json")
with open(chunks_file, 'r', encoding='utf-8') as f:
    chunks = json.load(f)

# Tạo embeddings
print("Đang tạo embeddings...")
texts = [chunk['content'] for chunk in chunks]
embeddings = model.encode(texts, show_progress_bar=True)

# Lưu embeddings
np.save("processed/embeddings.npy", embeddings)

# Lưu mapping (chunk_id -> index)
mapping = {chunk['id']: i for i, chunk in enumerate(chunks)}
with open("processed/chunk_mapping.json", 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"Đã tạo {len(embeddings)} embeddings")
```

### 2.3. Cài đặt Thư viện

```bash
pip install sentence-transformers numpy
```

---

## 💾 Bước 3: Chọn Vector Database

### 3.1. Các Lựa Chọn

**Option 1: FAISS (Khuyến nghị cho bắt đầu)**
- ✅ Miễn phí, mã nguồn mở
- ✅ Nhanh, hiệu quả
- ✅ Dễ sử dụng
- ❌ Chỉ lưu trữ local

**Option 2: Chroma**
- ✅ Dễ sử dụng, API đơn giản
- ✅ Hỗ trợ metadata filtering tốt
- ✅ Có thể chạy local hoặc server

**Option 3: Pinecone / Weaviate (Cloud)**
- ✅ Quản lý tự động, scalable
- ✅ API đơn giản
- ❌ Có phí (hoặc free tier giới hạn)

### 3.2. Ví dụ với FAISS

```python
import faiss
import numpy as np
import json

# Load embeddings
embeddings = np.load("processed/embeddings.npy").astype('float32')

# Tạo FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)  # L2 distance
index.add(embeddings)

# Lưu index
faiss.write_index(index, "processed/faiss_index.bin")
```

---

## 🤖 Bước 4: Xây Dựng RAG System

### 4.1. Kiến Trúc RAG

```
User Query
    ↓
Query Embedding (cùng model với document embeddings)
    ↓
Vector Search (tìm top-k chunks liên quan)
    ↓
Retrieve Context (lấy nội dung chunks)
    ↓
LLM Prompt (query + context)
    ↓
Generated Response
```

### 4.2. Tạo File RAG System

Tạo file `rag_system.py`:

```python
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path

class RAGSystem:
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        self.embedding_model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = None
        self.chunk_mapping = None
        
    def load_index(self, index_path, chunks_path, mapping_path):
        """Load FAISS index và chunks"""
        self.index = faiss.read_index(index_path)
        with open(chunks_path, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
        with open(mapping_path, 'r', encoding='utf-8') as f:
            self.chunk_mapping = json.load(f)
    
    def search(self, query, top_k=5):
        """Tìm kiếm chunks liên quan"""
        # Tạo embedding cho query
        query_embedding = self.embedding_model.encode([query])
        query_embedding = query_embedding.astype('float32')
        
        # Tìm kiếm
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Lấy kết quả
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            chunk_id = list(self.chunk_mapping.keys())[list(self.chunk_mapping.values()).index(idx)]
            chunk = next(c for c in self.chunks if c['id'] == chunk_id)
            results.append({
                'chunk': chunk,
                'score': float(dist),
                'content': chunk['content'],
                'metadata': chunk.get('metadata', {})
            })
        
        return results
    
    def format_context(self, results):
        """Format context từ kết quả tìm kiếm"""
        context_parts = []
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            context_parts.append(
                f"[{i}] {metadata.get('dieu', 'N/A')}\n"
                f"{result['content']}\n"
            )
        return "\n".join(context_parts)
```

### 4.3. Tích hợp với LLM

**Option 1: OpenAI GPT**
```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

def generate_response(query, context):
    prompt = f"""Bạn là trợ lý pháp luật chuyên nghiệp. 
Dựa vào các điều luật sau, hãy trả lời câu hỏi của người dùng một cách chính xác và đầy đủ.

Các điều luật liên quan:
{context}

Câu hỏi: {query}

Trả lời:"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content
```

**Option 2: Local LLM (Ollama)**
```python
import requests

def generate_response(query, context):
    prompt = f"""Bạn là trợ lý pháp luật. Dựa vào các điều luật sau, trả lời câu hỏi.

Điều luật:
{context}

Câu hỏi: {query}

Trả lời:"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama2",
            "prompt": prompt
        }
    )
    
    return response.json()["response"]
```

---

## 🎯 Bước 5: Xây Dựng API/Interface

### 5.1. FastAPI Backend

Tạo file `api.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from rag_system import RAGSystem

app = FastAPI()
rag = RAGSystem()
rag.load_index("processed/faiss_index.bin", 
               "processed/chunks_normalized.json",
               "processed/chunk_mapping.json")

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/search")
async def search(request: QueryRequest):
    results = rag.search(request.query, request.top_k)
    return {"results": results}

@app.post("/chat")
async def chat(request: QueryRequest):
    results = rag.search(request.query, request.top_k)
    context = rag.format_context(results)
    response = generate_response(request.query, context)
    return {"response": response, "sources": results}
```

### 5.2. Streamlit Frontend

Tạo file `app.py`:

```python
import streamlit as st
import requests

st.title("🤖 Chatbot Pháp Luật")

query = st.text_input("Nhập câu hỏi của bạn:")

if st.button("Tìm kiếm"):
    response = requests.post(
        "http://localhost:8000/chat",
        json={"query": query, "top_k": 5}
    )
    
    result = response.json()
    st.write("**Trả lời:**")
    st.write(result["response"])
    
    st.write("**Nguồn tham khảo:**")
    for i, source in enumerate(result["sources"], 1):
        with st.expander(f"Điều luật {i}: {source['metadata'].get('dieu', 'N/A')}"):
            st.write(source['content'])
```

---

## 📊 Bước 6: Đánh Giá và Tối Ưu

### 6.1. Đánh Giá Chất Lượng

**Metrics cần theo dõi:**
- **Relevance**: Kết quả tìm kiếm có liên quan không?
- **Accuracy**: Câu trả lời có chính xác không?
- **Completeness**: Câu trả lời có đầy đủ không?
- **Response Time**: Thời gian phản hồi

**Tạo file đánh giá:**

```python
# evaluation.py
def evaluate_rag(query, expected_answer, rag_system):
    results = rag_system.search(query, top_k=5)
    context = rag_system.format_context(results)
    generated_answer = generate_response(query, context)
    
    # Tính điểm (có thể dùng BLEU, ROUGE, hoặc manual evaluation)
    score = calculate_score(generated_answer, expected_answer)
    return score
```

### 6.2. Tối Ưu Hóa

**1. Cải thiện Chunking:**
- Điều chỉnh `chunk_size` và `chunk_overlap`
- Thử các phương pháp chunking khác (semantic chunking)

**2. Cải thiện Embedding:**
- Thử các model embedding khác
- Fine-tune model trên dữ liệu pháp luật

**3. Cải thiện Retrieval:**
- Thử các phương pháp re-ranking
- Kết hợp keyword search với vector search (hybrid search)

**4. Cải thiện Generation:**
- Tối ưu prompt engineering
- Thử các LLM khác nhau
- Thêm chain-of-thought reasoning

---

## 🔧 Bước 7: Deployment

### 7.1. Local Deployment

```bash
# Backend
uvicorn api:app --host 0.0.0.0 --port 8000

# Frontend
streamlit run app.py
```

### 7.2. Cloud Deployment

**Option 1: Docker**
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Option 2: Cloud Platforms**
- **Heroku**: Dễ deploy, có free tier
- **AWS/GCP/Azure**: Scalable, nhiều tính năng
- **Railway/Render**: Đơn giản, giá rẻ

---

## 📝 Checklist Hoàn Thành

- [ ] Chạy pipeline xử lý dữ liệu thành công
- [ ] Tạo embeddings cho tất cả chunks
- [ ] Xây dựng vector database (FAISS/Chroma)
- [ ] Xây dựng RAG system với retrieval
- [ ] Tích hợp LLM (OpenAI/Local)
- [ ] Xây dựng API backend
- [ ] Xây dựng frontend interface
- [ ] Đánh giá chất lượng hệ thống
- [ ] Tối ưu hóa performance
- [ ] Deploy lên production

---

## 🎓 Lời Khuyên Chi Tiết

### 1. **Về Embedding Model**
- Bắt đầu với `paraphrase-multilingual-MiniLM-L12-v2` (nhẹ, nhanh)
- Nếu chất lượng không đủ, nâng cấp lên `multilingual-e5-base`
- Cân nhắc fine-tune model trên dữ liệu pháp luật nếu có đủ tài nguyên

### 2. **Về Chunking Strategy**
- Hiện tại: Mỗi chunk = 1 điều luật (tốt cho độ chính xác)
- Có thể thử: Chia nhỏ điều luật dài thành nhiều chunks nhỏ hơn
- Lưu ý: Giữ overlap để không mất context

### 3. **Về Retrieval**
- Bắt đầu với top-k = 5 chunks
- Có thể tăng lên 10-15 nếu câu hỏi phức tạp
- Thêm re-ranking để cải thiện chất lượng

### 4. **Về LLM**
- **OpenAI GPT-4**: Chất lượng cao nhất, nhưng có phí
- **GPT-3.5-turbo**: Cân bằng giữa chất lượng và chi phí
- **Local LLM (Ollama)**: Miễn phí, nhưng cần GPU mạnh
- **Anthropic Claude**: Chất lượng tốt, hỗ trợ context dài

### 5. **Về Prompt Engineering**
- Luôn bao gồm context (các điều luật liên quan)
- Yêu cầu LLM trích dẫn nguồn
- Thêm instructions về format câu trả lời
- Ví dụ prompt tốt:
  ```
  Bạn là trợ lý pháp luật chuyên nghiệp. 
  Dựa vào các điều luật sau, hãy trả lời câu hỏi một cách chính xác.
  Nếu không tìm thấy thông tin, hãy nói rõ.
  Luôn trích dẫn số điều luật khi trả lời.
  
  Điều luật liên quan:
  {context}
  
  Câu hỏi: {query}
  ```

### 6. **Về Performance**
- Cache embeddings để tránh tính lại
- Sử dụng batch processing khi tạo embeddings
- Optimize FAISS index (IndexIVFFlat cho dataset lớn)
- Monitor response time và optimize bottleneck

### 7. **Về Security & Privacy**
- Không hardcode API keys
- Sử dụng environment variables
- Implement rate limiting
- Log và monitor các queries

---

## 🚨 Các Vấn Đề Thường Gặp

### 1. **Embeddings quá lớn**
- **Giải pháp**: Sử dụng model nhỏ hơn hoặc giảm dimension
- **Hoặc**: Sử dụng vector database có compression

### 2. **Tìm kiếm không chính xác**
- **Giải pháp**: Thử model embedding khác
- **Hoặc**: Cải thiện chunking strategy
- **Hoặc**: Thêm keyword search (hybrid)

### 3. **LLM trả lời không chính xác**
- **Giải pháp**: Cải thiện prompt
- **Hoặc**: Tăng số lượng chunks (top_k)
- **Hoặc**: Thêm re-ranking

### 4. **Response time chậm**
- **Giải pháp**: Cache embeddings
- **Hoặc**: Sử dụng model nhẹ hơn
- **Hoặc**: Optimize FAISS index

---

## 📚 Tài Liệu Tham Khảo

1. **RAG Papers:**
   - "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)
   - "REALM: Retrieval-Augmented Language Model Pre-training" (Guu et al., 2020)

2. **Libraries:**
   - [LangChain](https://python.langchain.com/) - Framework RAG phổ biến
   - [LlamaIndex](https://www.llamaindex.ai/) - Framework RAG chuyên nghiệp
   - [Haystack](https://haystack.deepset.ai/) - End-to-end NLP framework

3. **Vector Databases:**
   - [FAISS Documentation](https://github.com/facebookresearch/faiss)
   - [Chroma Documentation](https://www.trychroma.com/)
   - [Pinecone Documentation](https://www.pinecone.io/learn/)

---

## 💡 Tips Cuối Cùng

1. **Bắt đầu đơn giản**: Xây dựng prototype đơn giản trước, tối ưu sau
2. **Test thường xuyên**: Đánh giá chất lượng ở mỗi bước
3. **Iterate**: Cải thiện dần dần dựa trên feedback
4. **Monitor**: Theo dõi performance và user feedback
5. **Document**: Ghi lại các quyết định và lý do

---

**Chúc bạn thành công với dự án Chatbot RAG! 🚀**

