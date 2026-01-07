#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG System
Kết hợp Vector Database với LLM để tạo chatbot
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

# Thêm parent directories vào path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Tự động load file .env nằm cùng thư mục nếu python-dotenv được cài
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()
except Exception:
    # Nếu không cài python-dotenv thì bỏ qua (người dùng có thể export env thủ công)
    pass

from VectorDB.models.faiss_manager import FAISSManager
from RAG.utils.llm_utils import generate_response_gemini, format_prompt


class RAGSystem:
    """RAG System - Kết hợp retrieval và generation"""
    
    def __init__(
        self,
        embedding_model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2',
        llm_provider: str = 'gemini',  # 'openai', 'claude', 'gemini'
        llm_model: str = 'gemini-pro',  # Model name tùy theo provider
        top_k: int = 5,
        api_key: Optional[str] = None
    ):
        """
        Khởi tạo RAG System với OpenAI (hoặc Claude)
        
        Args:
            embedding_model_name: Tên embedding model (phải giống với model đã dùng)
            llm_provider: LLM provider ('gemini', 'openai', 'claude')
                - 'gemini': Google Gemini (cần GEMINI_API_KEY hoặc GOOGLE_API_KEY) - Mặc định
                - 'openai': OpenAI GPT (cần API key)
                - 'claude': Anthropic Claude (cần API key)
            llm_model: Tên model tùy theo provider
                - Gemini: 'gemini-pro', 'gemini-1.5-flash', etc.
                - OpenAI: 'gpt-3.5-turbo' (rẻ), 'gpt-4', 'gpt-4-turbo', etc.
                - Claude: 'claude-3-haiku-20240307' (rẻ nhất), 'claude-3-sonnet-20240229', 'claude-3-opus-20240229', etc.
            top_k: Số chunks top để retrieve
            api_key: API key cho OpenAI hoặc Claude (nếu không có trong .env)
        """
        self.vector_db = FAISSManager(embedding_model_name=embedding_model_name)
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.api_key = api_key
        self.top_k = top_k
        self.is_loaded = False
        
        # Chỉ hỗ trợ Gemini trong cấu hình hiện tại
        if llm_provider != 'gemini':
            raise ValueError(f"LLM provider không hợp lệ: {llm_provider}. Chỉ hỗ trợ 'gemini'.")

        # Kiểm tra GEMINI API key (có thể dùng GEMINI_API_KEY hoặc GOOGLE_API_KEY)
        if not (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or api_key):
            print("⚠️  Cảnh báo: Chưa có GEMINI_API_KEY!")
            print("   Hãy tạo file .env với GEMINI_API_KEY=... hoặc truyền api_key vào constructor")
        else:
            print(f"🤖 RAG System: Sử dụng Gemini ({llm_model})")
    
    def load(
        self,
        index_path: Path,
        chunks_path: Path,
        mapping_path: Optional[Path] = None,
        embeddings_path: Optional[Path] = None
    ) -> None:
        """
        Load VectorDB index và chunks
        
        Args:
            index_path: Đường dẫn FAISS index
            chunks_path: Đường dẫn chunks.json
            mapping_path: Đường dẫn chunk_mapping.json (optional)
            embeddings_path: Đường dẫn embeddings.npy (optional)
        """
        self.vector_db.load_index(
            index_path=index_path,
            chunks_path=chunks_path,
            mapping_path=mapping_path,
            embeddings_path=embeddings_path
        )
        self.is_loaded = True
        print("✓ RAG System đã sẵn sàng!")
    
    def search(self, query: str, top_k: Optional[int] = None) -> Dict:
        """
        Tìm kiếm chunks liên quan (chỉ search, không generate)
        
        Args:
            query: Câu hỏi
            top_k: Số kết quả (mặc định dùng self.top_k)
            
        Returns:
            Dictionary chứa chunks và metadata
        """
        if not self.is_loaded:
            raise ValueError("Chưa load index! Gọi load() trước.")
        
        top_k = top_k or self.top_k
        results = self.vector_db.search_by_text(query, top_k=top_k, return_distances=True)
        
        return {
            'chunks': results.get('chunks', []),
            'indices': results['indices'],
            'distances': results.get('distances', []),
            'query': query
        }
    
    def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        temperature: float = 0.4,
        max_tokens: int = 2000
    ) -> Dict:
        """
        Query RAG System - Tìm kiếm và generate response
        
        Args:
            query: Câu hỏi của người dùng
            top_k: Số chunks để retrieve (mặc định dùng self.top_k)
            temperature: Temperature cho LLM (0.0-1.0)
            max_tokens: Số tokens tối đa cho response
            
        Returns:
            Dictionary chứa answer, sources, và metadata
        """
        if not self.is_loaded:
            raise ValueError("Chưa load index! Gọi load() trước.")
        
        top_k = min(top_k or self.top_k, 5)  # Limit to 5 chunks max to keep prompt shorter
        
        # Bước 1: Tìm kiếm chunks liên quan
        print(f"🔍 Đang tìm kiếm chunks liên quan...")
        search_results = self.search(query, top_k)
        chunks = search_results['chunks']
        
        if not chunks:
            return {
                'answer': 'Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn.',
                'sources': [],
                'query': query
            }
        
        # Bước 2: Format context từ chunks
        context = self._format_context(chunks)
        
        # Bước 3: Tạo prompt
        prompt = format_prompt(query, context)
        
        # Bước 4: Generate response với LLM (với multi-level retry)
        print(f"🤖 Đang tạo câu trả lời...")
        last_err = None

        def _is_error_result(res: Optional[str]) -> bool:
            if not res:
                return True
            if isinstance(res, str):
                bad_keywords = [
                    'Lỗi', 'Lỗi khi tạo response', 'response structure unexpected',
                    'Invalid operation', 'An error occurred', 'MAX_TOKENS', 'finish_reason'
                ]
                return any(k in res for k in bad_keywords)
            return False

        # First attempt: original prompt
        try:
            result = self._generate_response(prompt, temperature, max_tokens)
            if not _is_error_result(result):
                answer = result
            else:
                last_err = result
                answer = None
                print(f"⚠️ LLM returned error-like result on first attempt: {last_err}")
        except Exception as e:
            last_err = str(e)
            answer = None
            print(f"⚠️ Exception on first attempt: {last_err}")

        # Multi-level retry: reduce top_k and progressively truncate chunks
        if not answer:
            requested_top_k = top_k or self.top_k
            # build a sequence of top_k reductions (keep unique and >=1)
            top_k_options = []
            for t in [requested_top_k, min(4, requested_top_k), 3, 2]:
                if t >= 1 and t not in top_k_options:
                    top_k_options.append(t)

            truncate_lengths = [800, 600, 400, 200]

            succeeded = False
            for tk in top_k_options:
                for tl in truncate_lengths:
                    try:
                        print(f"🔁 Retry attempt: top_k={tk}, truncate_len={tl}")
                        truncated_chunks = [
                            {**c, 'content': (c.get('content') or '')[:tl]} for c in chunks[:tk]
                        ]
                        truncated_context = self._format_context(truncated_chunks)
                        truncated_prompt = format_prompt(query, truncated_context)

                        # slightly reduce temperature to improve determinism
                        temp = max(0.0, float(temperature) * 0.7)
                        # keep max_tokens same (do not increase) to avoid exceeding account/model limits
                        result = self._generate_response(truncated_prompt, temp, max_tokens)

                        if not _is_error_result(result):
                            answer = result
                            succeeded = True
                            print(f"✅ Retry success: top_k={tk}, truncate_len={tl}")
                            break
                        else:
                            last_err = result
                            print(f"⚠️ Retry returned error-like result: {last_err}")

                    except Exception as e:
                        last_err = str(e)
                        print(f"⚠️ Exception during retry (top_k={tk}, tl={tl}): {last_err}")

                if succeeded:
                    break

        # If still no answer, build fallback
        if not answer:
            error_msg = last_err or 'Lỗi không xác định khi gọi LLM.'
            print(f"⚠️ LLM final failure: {error_msg}")
            fallback_parts = [f"⚠️ Lỗi: {error_msg}\n"]
            for i, ch in enumerate(chunks[: min(5, len(chunks)) ], 1):
                meta = ch.get('metadata', {})
                title = meta.get('dieu') or meta.get('chuong') or f"Nguồn {i}"
                content = ch.get('content', '') or ''
                snippet = content.strip().replace('\n', ' ')[:400]
                fallback_parts.append(f"[{i}] {title}: {snippet}")

            fallback_answer = (
                "Hệ thống tạo câu trả lời tự động gặp sự cố. Chi tiết lỗi và tóm tắt từ các nguồn liên quan:\n\n"
                + "\n\n".join(fallback_parts)
            )
            answer = fallback_answer
        
        # Bước 5: Format sources
        sources = self._format_sources(chunks)
        
        return {
            'answer': answer,
            'sources': sources,
            'query': query,
            'num_sources': len(sources),
            'chunks_used': top_k
        }
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """Format context từ chunks để đưa vào prompt"""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get('metadata', {})
            content = chunk.get('content', '')
            
            # Lấy thông tin điều luật
            dieu = metadata.get('dieu', 'N/A')
            chuong = metadata.get('chuong', '')
            loai_van_ban = metadata.get('loai_van_ban', '')
            
            context_part = f"[{i}] "
            if chuong:
                context_part += f"{chuong}\n"
            context_part += f"{dieu}\n"
            if loai_van_ban:
                context_part += f"Loại văn bản: {loai_van_ban}\n"
            context_part += f"Nội dung: {content}\n"
            
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Format sources để trả về cho người dùng"""
        sources = []
        
        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            # Normalize None -> empty string to avoid Pydantic validation errors
            dieu = metadata.get('dieu', 'N/A') or 'N/A'
            chuong = metadata.get('chuong') or ''
            loai_van_ban = metadata.get('loai_van_ban') or ''
            so_van_ban = metadata.get('so_van_ban') or ''
            ngay_ban_hanh = metadata.get('ngay_ban_hanh') or ''
            content = chunk.get('content', '') or ''
            content_preview = content[:200] + '...' if len(content) > 200 else content

            sources.append({
                'dieu': dieu,
                'chuong': chuong,
                'loai_van_ban': loai_van_ban,
                'so_van_ban': so_van_ban,
                'ngay_ban_hanh': ngay_ban_hanh,
                'content_preview': content_preview
            })
        
        return sources
    
    def _generate_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response từ LLM (OpenAI hoặc Claude)"""
        # Hiện tại chỉ hỗ trợ Gemini
        if self.llm_provider != 'gemini':
            raise ValueError(f"LLM provider không hợp lệ: {self.llm_provider}. Chỉ hỗ trợ 'gemini'.")

        # Retry/fallback strategy:
        # 1) Try with provided params
        # 2) If error, retry with increased max_tokens and lower temperature
        # 3) If still error, try a flash model as fallback
        attempts = []
        attempts.append({
            'model': self.llm_model,
            'temperature': temperature,
            'max_tokens': max_tokens
        })

        # second attempt: increase tokens, reduce temperature
        attempts.append({
            'model': self.llm_model,
            'temperature': max(0.0, float(temperature) * 0.3),
            'max_tokens': min(2000, int(max_tokens * 2))
        })

        # third attempt: try a flash model if different from current
        fallback_model = 'models/gemini-2.5-flash'
        if self.llm_model != fallback_model:
            attempts.append({
                'model': fallback_model,
                'temperature': 0.2,
                'max_tokens': min(2000, int(max_tokens * 2))
            })

        last_err = None
        for i, a in enumerate(attempts, 1):
            try:
                print(f"🔁 Lần thử #{i}: model={a['model']} temp={a['temperature']} max_tokens={a['max_tokens']}")
                result = generate_response_gemini(
                    prompt=prompt,
                    model=a['model'],
                    temperature=a['temperature'],
                    max_tokens=a['max_tokens'],
                    api_key=self.api_key
                )

                # Detect error-like responses (the helper returns Vietnamese error messages)
                if not result or isinstance(result, str) and (
                    result.startswith('Lỗi') or
                    'Lỗi khi tạo response' in result or
                    'response structure unexpected' in result or
                    'Invalid operation' in result or
                    'An error occurred' in result
                ):
                    last_err = result
                    print(f"⚠️  Attempt #{i} failed: {result}")
                    continue

                # Successful response
                return result

            except Exception as e:
                last_err = str(e)
                print(f"⚠️  Exception on attempt #{i}: {e}")
                continue

        # If all attempts failed, raise an exception so callers can handle fallback
        raise RuntimeError(last_err or 'Lỗi không xác định khi gọi LLM.')


def main():
    """Test function"""
    from pathlib import Path
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    index_path = project_root / "VectorDB" / "data" / "index" / "faiss_index.bin"
    chunks_path = project_root / "data_processing" / "chunks.json"
    mapping_path = project_root / "Embeddings" / "data" / "mappings" / "chunk_mapping.json"
    
    
    rag = RAGSystem(
        llm_provider='gemini',  # Dùng Gemini
        llm_model='models/gemini-2.5-flash',
        top_k=12
    )
    
    # Hoặc dùng Claude:
    # rag = RAGSystem(
    #     llm_provider='claude',
    #     llm_model='claude-3-sonnet-20240229',
    #     top_k=5
    # )
    
    # Load
    if index_path.exists():
        rag.load(
            index_path=index_path,
            chunks_path=chunks_path,
            mapping_path=mapping_path
        )
        
        # Test query
        query = "Phạm vi điều chỉnh của luật là gì?"
        print(f"\n❓ Câu hỏi: {query}\n")
        
        response = rag.query(query, max_tokens=1500)
        
        print(f"\n💬 Trả lời:\n{response['answer']}\n")
        print(f"\n📚 Nguồn tham khảo ({response['num_sources']} điều luật):")
        for i, source in enumerate(response['sources'], 1):
            print(f"\n  [{i}] {source['dieu']}")
            if source['loai_van_ban']:
                print(f"      Loại: {source['loai_van_ban']}")
    else:
        print("Index chưa được tạo. Chạy VectorDB/scripts/build_index.py trước.")


if __name__ == "__main__":
    main()

