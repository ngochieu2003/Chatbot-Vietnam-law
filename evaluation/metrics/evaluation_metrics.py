#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluation Metrics cho Chatbot RAG
Các metrics để đánh giá chất lượng chatbot
"""

import re
from typing import Dict, List, Optional, Tuple
from collections import Counter


class EvaluationMetrics:
    """Class chứa các metrics đánh giá chatbot"""
    
    @staticmethod
    def keyword_coverage(
        answer: str,
        expected_keywords: List[str],
        case_sensitive: bool = False
    ) -> Dict[str, float]:
        """
        Đánh giá độ bao phủ keywords trong câu trả lời
        
        Args:
            answer: Câu trả lời của chatbot
            expected_keywords: List keywords mong đợi
            case_sensitive: Có phân biệt hoa thường không
            
        Returns:
            Dict chứa coverage score và chi tiết
        """
        if not expected_keywords:
            return {
                'score': 1.0,
                'found_keywords': [],
                'missing_keywords': [],
                'coverage_ratio': 1.0
            }
        
        answer_lower = answer.lower() if not case_sensitive else answer
        keywords_lower = [kw.lower() if not case_sensitive else kw for kw in expected_keywords]
        
        found_keywords = []
        missing_keywords = []
        
        for kw in keywords_lower:
            if kw in answer_lower:
                found_keywords.append(kw)
            else:
                missing_keywords.append(kw)
        
        coverage_ratio = len(found_keywords) / len(expected_keywords) if expected_keywords else 0.0
        
        return {
            'score': coverage_ratio,
            'found_keywords': found_keywords,
            'missing_keywords': missing_keywords,
            'coverage_ratio': coverage_ratio
        }
    
    @staticmethod
    def source_relevance(
        retrieved_sources: List[Dict],
        expected_sources: List[str]
    ) -> Dict[str, float]:
        """
        Đánh giá độ liên quan của sources được retrieve
        
        Args:
            retrieved_sources: List sources được retrieve
            expected_sources: List sources mong đợi (có thể là điều luật, chương, etc.)
            
        Returns:
            Dict chứa relevance score và chi tiết
        """
        if not expected_sources:
            return {
                'score': 1.0,
                'matched_sources': [],
                'unmatched_sources': [],
                'match_ratio': 1.0
            }
        
        matched_sources = []
        unmatched_sources = []
        
        # Extract source identifiers từ retrieved sources
        retrieved_ids = []
        for source in retrieved_sources:
            dieu = source.get('dieu', '')
            chuong = source.get('chuong', '')
            if dieu:
                retrieved_ids.append(dieu)
            if chuong:
                retrieved_ids.append(chuong)
        
        # So sánh với expected sources
        for expected in expected_sources:
            found = False
            for retrieved in retrieved_ids:
                if expected.lower() in retrieved.lower() or retrieved.lower() in expected.lower():
                    matched_sources.append(expected)
                    found = True
                    break
            if not found:
                unmatched_sources.append(expected)
        
        match_ratio = len(matched_sources) / len(expected_sources) if expected_sources else 0.0
        
        return {
            'score': match_ratio,
            'matched_sources': matched_sources,
            'unmatched_sources': unmatched_sources,
            'match_ratio': match_ratio,
            'retrieved_count': len(retrieved_sources)
        }
    
    @staticmethod
    def answer_length_score(answer: str, min_length: int = 50, max_length: int = 2000) -> float:
        """
        Đánh giá độ dài câu trả lời (quá ngắn hoặc quá dài đều không tốt)
        
        Args:
            answer: Câu trả lời
            min_length: Độ dài tối thiểu (characters)
            max_length: Độ dài tối đa (characters)
            
        Returns:
            Score từ 0.0 đến 1.0
        """
        length = len(answer)
        
        if length < min_length:
            # Quá ngắn - score giảm dần
            return max(0.0, length / min_length)
        elif length > max_length:
            # Quá dài - score giảm dần
            return max(0.0, 1.0 - (length - max_length) / max_length)
        else:
            # Độ dài hợp lý
            return 1.0
    
    @staticmethod
    def answer_quality_score(
        answer: str,
        has_error_keywords: bool = True
    ) -> Dict[str, float]:
        """
        Đánh giá chất lượng câu trả lời dựa trên các indicators
        
        Args:
            answer: Câu trả lời
            has_error_keywords: Có kiểm tra error keywords không
            
        Returns:
            Dict chứa quality score và chi tiết
        """
        error_keywords = [
            'lỗi', 'error', 'exception', 'không tìm thấy', 
            'xin lỗi', 'gặp sự cố', 'hệ thống tạo câu trả lời tự động gặp sự cố'
        ]
        
        has_error = False
        if has_error_keywords:
            answer_lower = answer.lower()
            has_error = any(kw in answer_lower for kw in error_keywords)
        
        # Kiểm tra câu trả lời có ý nghĩa không (có ít nhất một câu hoàn chỉnh)
        sentences = re.split(r'[.!?]\s+', answer)
        has_complete_sentences = len([s for s in sentences if len(s.strip()) > 10]) > 0
        
        # Kiểm tra có nội dung thực sự không (không chỉ là whitespace)
        has_content = len(answer.strip()) > 20
        
        quality_score = 1.0
        if has_error:
            quality_score *= 0.3  # Giảm mạnh nếu có error
        if not has_complete_sentences:
            quality_score *= 0.5  # Giảm nếu không có câu hoàn chỉnh
        if not has_content:
            quality_score = 0.0  # Không có nội dung = 0 điểm
        
        return {
            'score': quality_score,
            'has_error': has_error,
            'has_complete_sentences': has_complete_sentences,
            'has_content': has_content,
            'sentence_count': len(sentences)
        }
    
    @staticmethod
    def retrieval_quality(
        distances: List[float],
        top_k: int
    ) -> Dict[str, float]:
        """
        Đánh giá chất lượng retrieval dựa trên distances
        
        Args:
            distances: List distances từ FAISS search
            top_k: Số kết quả retrieve
            
        Returns:
            Dict chứa retrieval quality metrics
        """
        if not distances:
            return {
                'avg_distance': 0.0,
                'min_distance': 0.0,
                'max_distance': 0.0,
                'quality_score': 0.0
            }
        
        avg_distance = sum(distances) / len(distances)
        min_distance = min(distances)
        max_distance = max(distances)
        
        # Quality score: distance càng nhỏ càng tốt
        # Giả sử distance tốt < 1.0, trung bình < 2.0
        if avg_distance < 1.0:
            quality_score = 1.0
        elif avg_distance < 2.0:
            quality_score = 0.7
        elif avg_distance < 3.0:
            quality_score = 0.4
        else:
            quality_score = 0.1
        
        return {
            'avg_distance': avg_distance,
            'min_distance': min_distance,
            'max_distance': max_distance,
            'quality_score': quality_score,
            'retrieved_count': len(distances)
        }
    
    @staticmethod
    def compute_overall_score(
        keyword_coverage: float,
        source_relevance: float,
        answer_quality: float,
        retrieval_quality: float,
        answer_length: float,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Tính điểm tổng hợp từ các metrics
        
        Args:
            keyword_coverage: Keyword coverage score
            source_relevance: Source relevance score
            answer_quality: Answer quality score
            retrieval_quality: Retrieval quality score
            answer_length: Answer length score
            weights: Trọng số cho từng metric (mặc định đều bằng nhau)
            
        Returns:
            Overall score từ 0.0 đến 1.0
        """
        if weights is None:
            weights = {
                'keyword_coverage': 0.25,
                'source_relevance': 0.20,
                'answer_quality': 0.30,
                'retrieval_quality': 0.15,
                'answer_length': 0.10
            }
        
        # Fix typo in weights
        if 'retrieval_quality ' in weights:
            weights['retrieval_quality'] = weights.pop('retrieval_quality ')
        
        overall = (
            keyword_coverage * weights.get('keyword_coverage', 0.25) +
            source_relevance * weights.get('source_relevance', 0.20) +
            answer_quality * weights.get('answer_quality', 0.30) +
            retrieval_quality * weights.get('retrieval_quality', 0.15) +
            answer_length * weights.get('answer_length', 0.10)
        )
        
        return overall

