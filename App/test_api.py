#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script cho FastAPI backend
Chạy: python App/test_api.py
Hoặc: cd App && python test_api.py
"""

import requests
import json
from typing import Dict, Optional

API_URL = "http://localhost:8000"


def test_health() -> bool:
    """Test health endpoint"""
    print("="*70)
    print("TEST: Health Check")
    print("="*70)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print(f"Status: {data.get('status')}")
        print(f"RAG Loaded: {data.get('rag_loaded')}")
        print(f"LLM Provider: {data.get('llm_provider')}")
        print(f"LLM Model: {data.get('llm_model')}")
        
        if data.get('status') == 'ready' and data.get('rag_loaded'):
            print("✅ Health check PASSED")
            return True
        else:
            print("⚠️  Health check: RAG System chưa được load")
            return False
    
    except Exception as e:
        print(f"❌ Health check FAILED: {e}")
        return False


def test_search(query: str, top_k: int = 5) -> Optional[Dict]:
    """Test search endpoint"""
    print("\n" + "="*70)
    print(f"TEST: Search - '{query}'")
    print("="*70)
    
    try:
        response = requests.post(
            f"{API_URL}/search",
            json={"query": query, "top_k": top_k},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"Query: {data.get('query')}")
        print(f"Top K: {data.get('top_k')}")
        print(f"Results: {len(data.get('chunks', []))} chunks")
        
        for i, (chunk, dist) in enumerate(zip(data.get('chunks', []), data.get('distances', [])), 1):
            metadata = chunk.get('metadata', {})
            print(f"\n[{i}] Distance: {dist:.4f}")
            print(f"    Điều: {metadata.get('dieu', 'N/A')}")
            if metadata.get('chuong'):
                print(f"    Chương: {metadata['chuong']}")
        
        print("✅ Search test PASSED")
        return data
    
    except Exception as e:
        print(f"❌ Search test FAILED: {e}")
        return None


def test_chat(query: str, top_k: int = 5) -> Optional[Dict]:
    """Test chat endpoint"""
    print("\n" + "="*70)
    print(f"TEST: Chat - '{query}'")
    print("="*70)
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "query": query,
                "top_k": top_k,
                "temperature": 0.7,
                "max_tokens": 2000
            },
            timeout=120  # 2 phút cho LLM
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"Query: {data.get('query')}")
        print(f"\nAnswer:\n{data.get('answer')}")
        print(f"\nSources: {data.get('num_sources')} điều luật")
        
        for i, source in enumerate(data.get('sources', [])[:3], 1):  # Chỉ hiển thị 3 đầu
            print(f"\n  [{i}] {source.get('dieu', 'N/A')}")
            if source.get('loai_van_ban'):
                print(f"      Loại: {source['loai_van_ban']}")
        
        print("✅ Chat test PASSED")
        return data
    
    except Exception as e:
        print(f"❌ Chat test FAILED: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"   Error detail: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Status code: {e.response.status_code}")
        return None


def main():
    """Main test function"""
    print("\n" + "="*70)
    print("TESTING FASTAPI BACKEND")
    print("="*70)
    print(f"\nAPI URL: {API_URL}")
    print("Đảm bảo FastAPI server đang chạy:")
    print("  uvicorn App.api.fastapi_app:app --reload --host 0.0.0.0 --port 8000")
    print("  hoặc: cd App && uvicorn api.fastapi_app:app --reload\n")
    
    # Test 1: Health check
    if not test_health():
        print("\n⚠️  RAG System chưa được load. Hãy kiểm tra:")
        print("   1. Index file có tồn tại không?")
        print("   2. API key đã được cấu hình chưa?")
        print("   3. Xem logs của FastAPI server")
        return
    
    # Test 2: Search
    test_queries = [
        "Phạm vi điều chỉnh của luật",
        "Quy định về xử phạt vi phạm hành chính"
    ]
    
    for query in test_queries:
        test_search(query, top_k=3)
    
    # Test 3: Chat
    chat_queries = [
        "Phạm vi điều chỉnh của luật là gì?",
        "Quy định về xử phạt vi phạm hành chính như thế nào?"
    ]
    
    for query in chat_queries:
        test_chat(query, top_k=5)
    
    print("\n" + "="*70)
    print("✅ TẤT CẢ TESTS HOÀN THÀNH!")
    print("="*70)


if __name__ == "__main__":
    main()

