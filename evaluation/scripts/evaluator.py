#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script đánh giá chính cho Chatbot RAG
Chạy đánh giá trên test dataset và tạo báo cáo
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Thêm parent directories vào path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from RAG.models.rag_system import RAGSystem
from evaluation.metrics.evaluation_metrics import EvaluationMetrics


class ChatbotEvaluator:
    """Class đánh giá chatbot RAG"""
    
    def __init__(
        self,
        rag_system: RAGSystem,
        test_dataset_path: Optional[Path] = None
    ):
        """
        Khởi tạo evaluator
        
        Args:
            rag_system: RAGSystem instance đã được load
            test_dataset_path: Đường dẫn đến test dataset JSON
        """
        self.rag_system = rag_system
        self.metrics = EvaluationMetrics()
        self.test_dataset = []
        
        if test_dataset_path and test_dataset_path.exists():
            self.load_test_dataset(test_dataset_path)
    
    def load_test_dataset(self, dataset_path: Path):
        """Load test dataset từ file JSON"""
        with open(dataset_path, 'r', encoding='utf-8') as f:
            self.test_dataset = json.load(f)
        print(f"✓ Đã load {len(self.test_dataset)} test cases từ {dataset_path}")
    
    def evaluate_single_query(
        self,
        question: str,
        expected_keywords: Optional[List[str]] = None,
        expected_sources: Optional[List[str]] = None
    ) -> Dict:
        """
        Đánh giá một câu hỏi
        
        Args:
            question: Câu hỏi
            expected_keywords: Keywords mong đợi trong câu trả lời
            expected_sources: Sources mong đợi
            
        Returns:
            Dict chứa kết quả đánh giá
        """
        start_time = time.time()
        
        # Query RAG system
        try:
            response = self.rag_system.query(
                query=question,
                top_k=5,
                temperature=0.4,
                max_tokens=2000
            )
            
            answer = response.get('answer', '')
            sources = response.get('sources', [])
            query_time = time.time() - start_time
            
            # Tính metrics
            keyword_coverage = self.metrics.keyword_coverage(
                answer,
                expected_keywords or []
            )
            
            source_relevance = self.metrics.source_relevance(
                sources,
                expected_sources or []
            )
            
            answer_quality = self.metrics.answer_quality_score(answer)
            answer_length = self.metrics.answer_length_score(answer)
            
            # Retrieval quality (cần distances từ search)
            search_results = self.rag_system.search(question, top_k=5)
            distances = search_results.get('distances', [])
            retrieval_quality = self.metrics.retrieval_quality(distances, top_k=5)
            
            # Overall score
            overall_score = self.metrics.compute_overall_score(
                keyword_coverage['score'],
                source_relevance['score'],
                answer_quality['score'],
                retrieval_quality['quality_score'],
                answer_length
            )
            
            return {
                'question': question,
                'answer': answer,
                'sources': sources,
                'query_time': query_time,
                'metrics': {
                    'keyword_coverage': keyword_coverage,
                    'source_relevance': source_relevance,
                    'answer_quality': answer_quality,
                    'answer_length': answer_length,
                    'retrieval_quality': retrieval_quality,
                    'overall_score': overall_score
                },
                'success': True,
                'error': None
            }
            
        except Exception as e:
            query_time = time.time() - start_time
            return {
                'question': question,
                'answer': '',
                'sources': [],
                'query_time': query_time,
                'metrics': {
                    'overall_score': 0.0
                },
                'success': False,
                'error': str(e)
            }
    
    def evaluate_dataset(
        self,
        test_dataset: Optional[List[Dict]] = None,
        max_tests: Optional[int] = None
    ) -> Dict:
        """
        Đánh giá toàn bộ test dataset
        
        Args:
            test_dataset: Test dataset (nếu None thì dùng self.test_dataset)
            max_tests: Giới hạn số test cases (để tiết kiệm API quota)
            
        Returns:
            Dict chứa kết quả đánh giá tổng hợp
        """
        dataset = test_dataset or self.test_dataset
        
        if not dataset:
            raise ValueError("Không có test dataset! Hãy load test dataset trước.")
        
        # Giới hạn số test cases nếu có
        if max_tests and max_tests > 0:
            dataset = dataset[:max_tests]
            print(f"⚠️  Giới hạn số test cases: {max_tests} (để tiết kiệm API quota)")
        
        print(f"\n🔍 Bắt đầu đánh giá {len(dataset)} test cases...\n")
        
        results = []
        total_time = 0.0
        
        for i, test_case in enumerate(dataset, 1):
            question = test_case.get('question', '')
            expected_keywords = test_case.get('expected_answer_keywords', [])
            expected_sources = test_case.get('expected_sources', [])
            test_id = test_case.get('id', f'test_{i}')
            
            print(f"[{i}/{len(dataset)}] Đang đánh giá: {question[:60]}...")
            
            result = self.evaluate_single_query(
                question=question,
                expected_keywords=expected_keywords,
                expected_sources=expected_sources
            )
            
            result['test_id'] = test_id
            result['category'] = test_case.get('category', 'unknown')
            result['difficulty'] = test_case.get('difficulty', 'unknown')
            
            results.append(result)
            total_time += result['query_time']
            
            # In kết quả nhanh
            score = result['metrics'].get('overall_score', 0.0)
            status = "✅" if result['success'] else "❌"
            print(f"    {status} Score: {score:.2f}, Time: {result['query_time']:.2f}s\n")
        
        # Tính tổng hợp
        successful_tests = [r for r in results if r['success']]
        avg_score = sum(r['metrics'].get('overall_score', 0.0) for r in successful_tests) / len(successful_tests) if successful_tests else 0.0
        avg_time = total_time / len(results) if results else 0.0
        
        # Phân tích theo category
        category_scores = {}
        for result in successful_tests:
            category = result.get('category', 'unknown')
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(result['metrics'].get('overall_score', 0.0))
        
        category_avg = {
            cat: sum(scores) / len(scores)
            for cat, scores in category_scores.items()
        }
        
        summary = {
            'total_tests': len(dataset),
            'successful_tests': len(successful_tests),
            'failed_tests': len(results) - len(successful_tests),
            'success_rate': len(successful_tests) / len(dataset) if dataset else 0.0,
            'average_score': avg_score,
            'average_query_time': avg_time,
            'total_time': total_time,
            'category_scores': category_avg,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def save_results(self, results: Dict, output_path: Path):
        """Lưu kết quả đánh giá vào file JSON"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Đã lưu kết quả vào {output_path}")


def main():
    """Main function để chạy evaluation"""
    import argparse
    from pathlib import Path
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Đánh giá Chatbot RAG')
    parser.add_argument(
        '--max-tests',
        type=int,
        default=None,
        help='Giới hạn số test cases (để tiết kiệm API quota). Ví dụ: --max-tests 1'
    )
    args = parser.parse_args()
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    index_path = project_root / "VectorDB" / "data" / "index" / "faiss_index.bin"
    chunks_path = project_root / "data_processing" / "chunks.json"
    mapping_path = project_root / "Embeddings" / "data" / "mappings" / "chunk_mapping.json"
    test_dataset_path = project_root / "evaluation" / "test_data" / "sample_test_dataset.json"
    output_path = project_root / "evaluation" / "reports" / f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Khởi tạo RAG System
    print("🚀 Đang khởi tạo RAG System...")
    rag_system = RAGSystem(
        llm_provider='gemini',
        llm_model='models/gemini-2.5-flash',
        top_k=5
    )
    
    if not index_path.exists():
        print(f"❌ Không tìm thấy index file: {index_path}")
        print("   Hãy chạy VectorDB/scripts/build_index.py trước.")
        return
    
    # Load RAG System
    rag_system.load(
        index_path=index_path,
        chunks_path=chunks_path,
        mapping_path=mapping_path
    )
    
    # Khởi tạo Evaluator
    print("\n📊 Đang khởi tạo Evaluator...")
    evaluator = ChatbotEvaluator(rag_system, test_dataset_path)
    
    # Chạy evaluation với giới hạn số test cases nếu có
    results = evaluator.evaluate_dataset(max_tests=args.max_tests)
    
    # In summary
    print("\n" + "="*60)
    print("📈 TỔNG KẾT ĐÁNH GIÁ")
    print("="*60)
    print(f"Tổng số test: {results['total_tests']}")
    print(f"Thành công: {results['successful_tests']}")
    print(f"Thất bại: {results['failed_tests']}")
    print(f"Tỷ lệ thành công: {results['success_rate']:.1%}")
    print(f"Điểm trung bình: {results['average_score']:.2f}")
    print(f"Thời gian trung bình: {results['average_query_time']:.2f}s")
    print(f"Tổng thời gian: {results['total_time']:.2f}s")
    print("\nĐiểm theo category:")
    for category, score in results['category_scores'].items():
        print(f"  - {category}: {score:.2f}")
    print("="*60)
    
    # Lưu kết quả
    evaluator.save_results(results, output_path)
    
    print(f"\n✅ Hoàn thành! Kết quả đã được lưu tại: {output_path}")


if __name__ == "__main__":
    main()

