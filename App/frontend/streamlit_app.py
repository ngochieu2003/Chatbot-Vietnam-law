#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit Frontend cho RAG Chatbot Pháp Luật
Chạy: streamlit run App/frontend/streamlit_app.py
Hoặc: cd App && streamlit run frontend/streamlit_app.py
"""

import streamlit as st
import requests
import sys
from pathlib import Path
from typing import Optional

# Page config
st.set_page_config(
    page_title="Chatbot hỗ trợ tìm hiểu pháp luật Việt Nam",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API URL
API_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .source-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .answer-box {
        background-color: #e8f4f8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Kiểm tra API có sẵn sàng không"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('status') == 'ready' and data.get('rag_loaded', False)
        return False
    except:
        return False


def chat_with_api(query: str, top_k: int = 5, temperature: float = 0.7, max_tokens: int = 2000) -> Optional[dict]:
    """Gọi API chat endpoint"""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "query": query,
                "top_k": top_k,
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            timeout=120  # Timeout 2 phút cho LLM
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Lỗi khi gọi API: {str(e)}")
        return None


def search_only(query: str, top_k: int = 5) -> Optional[dict]:
    """Gọi API search endpoint"""
    try:
        response = requests.post(
            f"{API_URL}/search",
            json={
                "query": query,
                "top_k": top_k
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Lỗi khi gọi API: {str(e)}")
        return None


def main():
    """Main function"""
    
    # Header
    st.markdown('<div class="main-header">⚖️ Chatbot hỗ trợ tìm hiểu pháp luật Việt Nam</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Cài Đặt")
        
        # API URL
        global API_URL
        api_url_input = st.text_input("API URL", value=API_URL)
        if api_url_input:
            API_URL = api_url_input
        
        # Health check
        st.subheader("Trạng Thái")
        if check_api_health():
            st.success("✅ API đang hoạt động")
        else:
            st.error("❌ API không khả dụng")
            st.info("Hãy đảm bảo FastAPI server đang chạy tại " + API_URL)
            st.stop()
        
        # Settings
        st.subheader("Tham Số")
        top_k = st.slider("Số kết quả (top_k)", 1, 20, 5)
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        max_tokens = st.slider("Max Tokens", 100, 2000, 2000, 50)
        
        st.markdown("---")
        st.markdown("### 📚 Hướng Dẫn")
        st.markdown("""
        1. Nhập câu hỏi về pháp luật
        2. Chọn chế độ: Chat hoặc Search
        3. Xem kết quả và nguồn tham khảo
        """)
    
    # Main content
    tab1, tab2 = st.tabs(["💬 Chat", "🔍 Search Only"])
    
    # Tab 1: Chat
    with tab1:
        st.subheader("💬 Hỏi Đáp Về Pháp Luật")
        
        # Chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Manage prompt state for Streamlit 1.12
        if "chat_prompt" not in st.session_state:
            st.session_state.chat_prompt = ""
        if st.session_state.get("clear_prompt_flag"):
            st.session_state.chat_prompt = ""
            st.session_state.clear_prompt_flag = False

        # Display chat history (compat với Streamlit < 1.23)
        for idx, message in enumerate(st.session_state.messages):
            role_label = "👤 Người dùng" if message["role"] == "user" else "🤖 Trợ lý"
            st.markdown(f"**{role_label}:**")
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander(f"📚 Nguồn tham khảo ({len(message['sources'])} điều luật)", expanded=False):
                    for i, source in enumerate(message["sources"], 1):
                        st.markdown(f"**[{i}] {source.get('dieu', 'N/A')}**")
                        if source.get('loai_van_ban'):
                            st.caption(f"Loại: {source['loai_van_ban']}")
                        if source.get('so_van_ban'):
                            st.caption(f"Số văn bản: {source['so_van_ban']}")
                        if source.get('ngay_ban_hanh'):
                            st.caption(f"Ngày ban hành: {source['ngay_ban_hanh']}")
                        st.text(source.get('content_preview', '')[:300] + '...')
            st.markdown("---")

        # Chat input controls thay cho st.chat_input (Streamlit 1.12)
        st.markdown("### ✍️ Nhập câu hỏi")
        prompt = st.text_area("Câu hỏi của bạn", key="chat_prompt", height=120)
        send_col, clear_col = st.columns(2)

        with send_col:
            send_clicked = st.button("Gửi câu hỏi", key="send_chat")
        with clear_col:
            if st.button("🗑️ Xóa lịch sử chat", key="clear_chat"):
                st.session_state.messages = []
                st.session_state.clear_prompt_flag = True
                st.experimental_rerun()

        if send_clicked and prompt.strip():
            user_message = prompt.strip()
            st.session_state.messages.append({"role": "user", "content": user_message})
            with st.spinner("Đang tìm kiếm và tạo câu trả lời..."):
                result = chat_with_api(user_message, top_k, temperature, max_tokens)
                if result:
                    answer = result.get('answer', 'Không có câu trả lời')
                    sources = result.get('sources', [])
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                else:
                    st.error("Không thể lấy câu trả lời. Vui lòng thử lại.")
            st.session_state.clear_prompt_flag = True
            st.experimental_rerun()
        elif send_clicked:
            st.warning("Vui lòng nhập câu hỏi trước khi gửi.")
    
    # Tab 2: Search Only
    with tab2:
        st.subheader("🔍 Tìm Kiếm Điều Luật")
        
        search_query = st.text_input("Nhập từ khóa tìm kiếm:", key="search_input")
        
        if st.button("🔍 Tìm kiếm", key="search_button") or search_query:
            if search_query:
                with st.spinner("Đang tìm kiếm..."):
                    result = search_only(search_query, top_k)
                    
                    if result:
                        chunks = result.get('chunks', [])
                        distances = result.get('distances', [])
                        
                        st.success(f"Tìm thấy {len(chunks)} kết quả")
                        
                        for i, (chunk, distance) in enumerate(zip(chunks, distances), 1):
                            with st.expander(f"[{i}] {chunk.get('metadata', {}).get('dieu', 'N/A')} (Distance: {distance:.4f})"):
                                metadata = chunk.get('metadata', {})
                                
                                if metadata.get('chuong'):
                                    st.markdown(f"**Chương:** {metadata['chuong']}")
                                
                                st.markdown(f"**Điều:** {metadata.get('dieu', 'N/A')}")
                                
                                if metadata.get('loai_van_ban'):
                                    st.markdown(f"**Loại văn bản:** {metadata['loai_van_ban']}")
                                
                                if metadata.get('so_van_ban'):
                                    st.markdown(f"**Số văn bản:** {metadata['so_van_ban']}")
                                
                                st.markdown("---")
                                st.markdown("**Nội dung:**")
                                st.text(chunk.get('content', '')[:1000])
                    else:
                        st.error("Không tìm thấy kết quả. Vui lòng thử lại.")


if __name__ == "__main__":
    main()

