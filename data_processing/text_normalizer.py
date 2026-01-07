#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module chuẩn hóa văn bản tiếng Việt
Ưu tiên: LOW
Loại bỏ khoảng trắng thừa, chuẩn hóa dấu câu, xử lý các ký tự đặc biệt
"""

import re
from typing import Optional


class TextNormalizer:
    """Chuẩn hóa văn bản tiếng Việt"""
    
    def __init__(self):
        # Pattern để loại bỏ các ký tự không cần thiết
        self.whitespace_pattern = re.compile(r'\s+')
        self.multiple_newlines_pattern = re.compile(r'\n\s*\n\s*\n+')
        self.leading_trailing_whitespace_pattern = re.compile(r'^\s+|\s+$', re.MULTILINE)
    
    def normalize(self, text: str) -> str:
        """
        Chuẩn hóa văn bản
        
        Args:
            text: Văn bản cần chuẩn hóa
            
        Returns:
            Văn bản đã được chuẩn hóa
        """
        if not text:
            return ""
        
        # Loại bỏ các ký tự điều khiển không cần thiết
        text = self._remove_control_characters(text)
        
        # Chuẩn hóa khoảng trắng
        text = self._normalize_whitespace(text)
        
        # Chuẩn hóa dấu câu
        text = self._normalize_punctuation(text)
        
        # Loại bỏ khoảng trắng thừa ở đầu và cuối dòng
        text = self._trim_lines(text)
        
        # Loại bỏ các dòng trống thừa
        text = self._normalize_newlines(text)
        
        # Loại bỏ khoảng trắng ở đầu và cuối toàn bộ văn bản
        text = text.strip()
        
        return text
    
    def _remove_control_characters(self, text: str) -> str:
        """Loại bỏ các ký tự điều khiển không cần thiết"""
        # Giữ lại các ký tự: newline, tab, space
        # Loại bỏ các ký tự điều khiển khác
        return ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    def _normalize_whitespace(self, text: str) -> str:
        """Chuẩn hóa khoảng trắng"""
        # Thay nhiều khoảng trắng liên tiếp bằng một khoảng trắng
        text = self.whitespace_pattern.sub(' ', text)
        
        # Loại bỏ khoảng trắng trước dấu câu
        text = re.sub(r'\s+([,.:;!?])', r'\1', text)
        
        # Đảm bảo có khoảng trắng sau dấu câu (nếu chưa có)
        text = re.sub(r'([,.:;!?])([^\s])', r'\1 \2', text)
        
        return text
    
    def _normalize_punctuation(self, text: str) -> str:
        """Chuẩn hóa dấu câu"""
        # Chuẩn hóa dấu ngoặc kép
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        
        # Chuẩn hóa dấu gạch ngang
        text = re.sub(r'[–—]', '-', text)
        
        # Loại bỏ các dấu câu lặp lại
        text = re.sub(r'([,.:;!?])\1+', r'\1', text)
        
        return text
    
    def _trim_lines(self, text: str) -> str:
        """Loại bỏ khoảng trắng ở đầu và cuối mỗi dòng"""
        lines = text.split('\n')
        trimmed_lines = [line.strip() for line in lines]
        return '\n'.join(trimmed_lines)
    
    def _normalize_newlines(self, text: str) -> str:
        """Chuẩn hóa các dòng trống"""
        # Thay nhiều dòng trống liên tiếp bằng tối đa 2 dòng trống
        text = self.multiple_newlines_pattern.sub('\n\n', text)
        return text
    
    def normalize_chunk(self, chunk: dict) -> dict:
        """
        Chuẩn hóa một chunk dữ liệu
        
        Args:
            chunk: Dictionary chứa chunk với key 'content'
            
        Returns:
            Chunk đã được chuẩn hóa
        """
        if 'content' in chunk:
            chunk['content'] = self.normalize(chunk['content'])
        return chunk
    
    def normalize_chunks(self, chunks: list) -> list:
        """
        Chuẩn hóa một list các chunks
        
        Args:
            chunks: List các dictionary chứa chunks
            
        Returns:
            List các chunks đã được chuẩn hóa
        """
        return [self.normalize_chunk(chunk) for chunk in chunks]


def main():
    """Hàm main để test"""
    normalizer = TextNormalizer()
    
    # Test với văn bản mẫu
    test_text = """
    Điều   1.   Phạm vi điều chỉnh
    
    
    Luật này quy định về vị trí, chức năng, nhiệm vụ, quyền hạn, tổ chức và hoạt động của Cảnh sát cơ động.
    
    """
    
    normalized = normalizer.normalize(test_text)
    print("Văn bản gốc:")
    print(repr(test_text))
    print("\nVăn bản đã chuẩn hóa:")
    print(repr(normalized))
    print("\nVăn bản đã chuẩn hóa (hiển thị):")
    print(normalized)


if __name__ == "__main__":
    main()

