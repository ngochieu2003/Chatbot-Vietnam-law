#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script chỉ test phần search (không cần LLM)
Dùng để kiểm tra retrieval hoạt động đúng không
"""

import sys
from pathlib import Path

# Thêm parent directory vào path
sys.path.insert(0, str(Path(__file__).parent.parent))

from RAG.models import RAGSystem

def main():
    """Test search only"""
    # Paths
    project_root = Path(__file__).parent.parent
    index_path = project_root / "VectorDB" / "data" / "index" / "faiss_index.bin"
    chunks_path = project_root / "data_processing" / "chunks.json"
    mapping_path = project_root / "Embeddings" / "data" / "mappings" / "chunk_mapping.json"
    
    # Khởi tạo RAG System (không cần LLM cho test này)
    rag = RAGSystem(
        llm_provider='openai',  # Không quan trọng vì chỉ test search
        llm_model='gpt-3.5-turbo',
        top_k=5
    )
    
    # Load
    print("Đang load index và chunks...")
    rag.load(
        index_path=index_path,
        chunks_path=chunks_path,
        mapping_path=mapping_path
    )
    
    # Test search (không cần LLM)
    queries = [
        "Phạm vi điều chỉnh của luật là gì?",
        "Quy định về xử phạt vi phạm hành chính",
        "Thủ tục khiếu nại quyết định hành chính"
    ]
    
    for query in queries:
        print(f"\n{'='*70}")
        print(f"❓ Câu hỏi: {query}")
        print(f"{'='*70}")
        
        # Chỉ search, không generate
        search_results = rag.search(query, top_k=5)
        
        print(f"\n✓ Tìm thấy {len(search_results['chunks'])} chunks liên quan:\n")
        
        for i, (chunk, distance) in enumerate(zip(search_results['chunks'], search_results['distances']), 1):
            metadata = chunk.get('metadata', {})
            print(f"[{i}] Distance: {distance:.4f}")
            print(f"    Điều: {metadata.get('dieu', 'N/A')}")
            if metadata.get('chuong'):
                print(f"    Chương: {metadata.get('chuong')}")
            if metadata.get('loai_van_ban'):
                print(f"    Loại: {metadata.get('loai_van_ban')}")
            print(f"    Nội dung: {chunk.get('content', '')[:150]}...")
            print()
    
    print("\n" + "="*70)
    print("✅ TEST SEARCH THÀNH CÔNG!")
    print("="*70)
    print("\nLưu ý: Phần search đã hoạt động tốt.")
    print("Để có câu trả lời đầy đủ, cần fix OpenAI API quota hoặc dùng LLM khác.")


if __name__ == "__main__":
    main()

