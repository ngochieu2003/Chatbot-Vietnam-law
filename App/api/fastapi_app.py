#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Backend cho RAG Chatbot Pháp Luật
Chạy: uvicorn App.api.fastapi_app:app --reload --host 0.0.0.0 --port 8000
Hoặc: cd App && uvicorn api.fastapi_app:app --reload --host 0.0.0.0 --port 8000
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Thêm parent directory vào path để import RAG module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from RAG.models.rag_system import RAGSystem

# Khởi tạo FastAPI app
app = FastAPI(
    title="RAG Chatbot Pháp Luật API",
    description="API cho chatbot hỏi đáp về pháp luật Việt Nam sử dụng RAG",
    version="1.0.0"
)

# CORS middleware để frontend có thể gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production, nên chỉ định domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG System instance
rag_system: Optional[RAGSystem] = None


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model cho query"""
    query: str = Field(..., description="Câu hỏi của người dùng")
    top_k: Optional[int] = Field(5, description="Số chunks để retrieve", ge=1, le=20)
    temperature: Optional[float] = Field(0.7, description="Temperature cho LLM", ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(500, description="Số tokens tối đa cho response", ge=100, le=3000)


class SearchRequest(BaseModel):
    """Request model cho search only"""
    query: str = Field(..., description="Câu hỏi tìm kiếm")
    top_k: Optional[int] = Field(5, description="Số kết quả", ge=1, le=20)


class SourceResponse(BaseModel):
    """Response model cho source"""
    dieu: str
    chuong: str = ""
    loai_van_ban: str = ""
    so_van_ban: str = ""
    ngay_ban_hanh: str = ""
    content_preview: str


class ChatResponse(BaseModel):
    """Response model cho chat"""
    answer: str
    sources: List[SourceResponse]
    query: str
    num_sources: int
    chunks_used: int


class SearchResponse(BaseModel):
    """Response model cho search"""
    chunks: List[Dict]
    indices: List[int]
    distances: List[float]
    query: str
    top_k: int


class HealthResponse(BaseModel):
    """Response model cho health check"""
    status: str
    rag_loaded: bool
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


# Initialize RAG System
def init_rag_system():
    """Khởi tạo RAG System khi server start"""
    global rag_system
    
    if rag_system is not None:
        return
    
    try:
        # Paths - từ App/ lên root rồi vào các thư mục
        project_root = Path(__file__).parent.parent.parent
        index_path = project_root / "VectorDB" / "data" / "index" / "faiss_index.bin"
        chunks_path = project_root / "data_processing" / "chunks.json"
        mapping_path = project_root / "Embeddings" / "data" / "mappings" / "chunk_mapping.json"
        
        # Kiểm tra files tồn tại
        if not index_path.exists():
            print(f"⚠️  Warning: Index file không tồn tại: {index_path}")
            print("   API sẽ không hoạt động cho đến khi index được tạo.")
            return
        
        # Khởi tạo RAG System
        llm_provider = os.getenv('LLM_PROVIDER', 'gemini')
        llm_model = os.getenv('LLM_MODEL', 'gemini-pro')
        
        # Lấy API key tùy theo provider
        api_key = (
            os.getenv('GEMINI_API_KEY') or 
            os.getenv('GOOGLE_API_KEY') or 
            os.getenv('OPENAI_API_KEY') or 
            os.getenv('ANTHROPIC_API_KEY')
        )
        
        rag_system = RAGSystem(
            llm_provider=llm_provider,
            llm_model=llm_model,
            top_k=5,
            api_key=api_key
        )
        
        # Load data
        rag_system.load(
            index_path=index_path,
            chunks_path=chunks_path,
            mapping_path=mapping_path
        )
        
        print("✅ RAG System đã được khởi tạo và load thành công!")
        
    except Exception as e:
        print(f"❌ Lỗi khi khởi tạo RAG System: {e}")
        import traceback
        traceback.print_exc()


# Startup event
@app.on_event("startup")
async def startup_event():
    """Khởi tạo RAG System khi server start"""
    print("🚀 Đang khởi động FastAPI server...")
    init_rag_system()


# Endpoints
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Chatbot Pháp Luật API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    global rag_system
    
    if rag_system is None or not rag_system.is_loaded:
        return HealthResponse(
            status="not_ready",
            rag_loaded=False
        )
    
    return HealthResponse(
        status="ready",
        rag_loaded=True,
        llm_provider=rag_system.llm_provider,
        llm_model=rag_system.llm_model
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: QueryRequest):
    """
    Chat endpoint - Tìm kiếm và generate response
    
    Args:
        request: QueryRequest chứa query và các tham số
    
    Returns:
        ChatResponse chứa answer, sources, và metadata
    """
    global rag_system
    
    if rag_system is None or not rag_system.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="RAG System chưa được load. Hãy kiểm tra /health endpoint."
        )
    
    try:
        # Query RAG System
        response = rag_system.query(
            query=request.query,
            top_k=request.top_k,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        # Note: rag_system.query() now returns fallback answer with error details if LLM fails,
        # so we don't need to check for error strings here. The answer is always valid.
        # The fallback already includes error info + chunk summaries for user transparency.
        
        # Format sources
        sources = [
            SourceResponse(
                dieu=source.get('dieu', 'N/A'),
                chuong=source.get('chuong') or '',
                loai_van_ban=source.get('loai_van_ban') or '',
                so_van_ban=source.get('so_van_ban') or '',
                ngay_ban_hanh=source.get('ngay_ban_hanh') or '',
                content_preview=source.get('content_preview') or ''
            )
            for source in response['sources']
        ]
        
        return ChatResponse(
            answer=response['answer'],
            sources=sources,
            query=response['query'],
            num_sources=response['num_sources'],
            chunks_used=response['chunks_used']
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xử lý query: {str(e)}"
        )


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(request: SearchRequest):
    """
    Search endpoint - Chỉ tìm kiếm, không generate
    
    Args:
        request: SearchRequest chứa query và top_k
    
    Returns:
        SearchResponse chứa chunks, indices, và distances
    """
    global rag_system
    
    if rag_system is None or not rag_system.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="RAG System chưa được load. Hãy kiểm tra /health endpoint."
        )
    
    try:
        # Search only
        results = rag_system.search(
            query=request.query,
            top_k=request.top_k
        )
        
        return SearchResponse(
            chunks=results['chunks'],
            indices=results['indices'],
            distances=results.get('distances', []),
            query=results['query'],
            top_k=request.top_k
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tìm kiếm: {str(e)}"
        )


def main():
    """Main function để chạy server"""
    uvicorn.run(
        "App.api.fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()

