#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script benchmark performance cho Chatbot RAG
Đo latency, throughput, và resource usage
"""

import sys
import time
import statistics
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import json

# Thêm parent directories vào path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from RAG.models.rag_system import RAGSystem


class PerformanceBenchmark:
    """Class benchmark performance của RAG system"""
    
    def __init__(self, rag_system: RAGSystem):
        """
        Khởi tạo benchmark
        
        Args:
            rag_system: RAGSystem instance đã được load
        """
        self.rag_system = rag_system
    
    def benchmark_search(
        self,
        queries: List[str],
        top_k: int = 5,
        iterations: int = 1
    ) -> Dict:
        """
        Benchmark search performance
        
        Args:
            queries: List câu hỏi để test
            top_k: Số kết quả retrieve
            iterations: Số lần lặp lại mỗi query
            
        Returns:
            Dict chứa kết quả benchmark
        """
        print(f"\n🔍 Benchmarking search performance...")
        print(f"   Queries: {len(queries)}, Top-K: {top_k}, Iterations: {iterations}\n")
        
        search_times = []
        
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] Testing: {query[:50]}...")
            
            for iteration in range(iterations):
                start_time = time.time()
                try:
                    results = self.rag_system.search(query, top_k=top_k)
                    elapsed = time.time() - start_time
                    search_times.append(elapsed)
                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    continue
        
        if not search_times:
            return {
                'success': False,
                'error': 'No successful searches'
            }
        
        return {
            'success': True,
            'total_queries': len(queries) * iterations,
            'successful_queries': len(search_times),
            'min_time': min(search_times),
            'max_time': max(search_times),
            'avg_time': statistics.mean(search_times),
            'median_time': statistics.median(search_times),
            'std_time': statistics.stdev(search_times) if len(search_times) > 1 else 0.0,
            'p95_time': self._percentile(search_times, 95),
            'p99_time': self._percentile(search_times, 99),
            'throughput_qps': 1.0 / statistics.mean(search_times) if search_times else 0.0
        }
    
    def benchmark_query(
        self,
        queries: List[str],
        top_k: int = 5,
        iterations: int = 1
    ) -> Dict:
        """
        Benchmark full query performance (search + generation)
        
        Args:
            queries: List câu hỏi để test
            top_k: Số kết quả retrieve
            iterations: Số lần lặp lại mỗi query
            
        Returns:
            Dict chứa kết quả benchmark
        """
        print(f"\n🤖 Benchmarking full query performance...")
        print(f"   Queries: {len(queries)}, Top-K: {top_k}, Iterations: {iterations}\n")
        
        query_times = []
        answer_lengths = []
        success_count = 0
        
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] Testing: {query[:50]}...")
            
            for iteration in range(iterations):
                start_time = time.time()
                try:
                    response = self.rag_system.query(
                        query=query,
                        top_k=top_k,
                        temperature=0.4,
                        max_tokens=2000
                    )
                    elapsed = time.time() - start_time
                    query_times.append(elapsed)
                    answer_lengths.append(len(response.get('answer', '')))
                    success_count += 1
                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    continue
        
        if not query_times:
            return {
                'success': False,
                'error': 'No successful queries'
            }
        
        return {
            'success': True,
            'total_queries': len(queries) * iterations,
            'successful_queries': success_count,
            'min_time': min(query_times),
            'max_time': max(query_times),
            'avg_time': statistics.mean(query_times),
            'median_time': statistics.median(query_times),
            'std_time': statistics.stdev(query_times) if len(query_times) > 1 else 0.0,
            'p95_time': self._percentile(query_times, 95),
            'p99_time': self._percentile(query_times, 99),
            'throughput_qps': 1.0 / statistics.mean(query_times) if query_times else 0.0,
            'avg_answer_length': statistics.mean(answer_lengths) if answer_lengths else 0.0
        }
    
    def benchmark_concurrent(
        self,
        queries: List[str],
        concurrent_requests: int = 5
    ) -> Dict:
        """
        Benchmark concurrent requests (simulated)
        
        Args:
            queries: List câu hỏi để test
            concurrent_requests: Số requests đồng thời
            
        Returns:
            Dict chứa kết quả benchmark
        """
        import threading
        
        print(f"\n⚡ Benchmarking concurrent requests...")
        print(f"   Queries: {len(queries)}, Concurrent: {concurrent_requests}\n")
        
        results = []
        errors = []
        
        def run_query(query, result_list, error_list):
            start_time = time.time()
            try:
                response = self.rag_system.query(query, top_k=5)
                elapsed = time.time() - start_time
                result_list.append({
                    'query': query,
                    'time': elapsed,
                    'success': True
                })
            except Exception as e:
                elapsed = time.time() - start_time
                error_list.append({
                    'query': query,
                    'error': str(e),
                    'time': elapsed
                })
        
        threads = []
        start_time = time.time()
        
        # Chia queries thành batches
        for i in range(0, len(queries), concurrent_requests):
            batch = queries[i:i+concurrent_requests]
            batch_threads = []
            
            for query in batch:
                thread = threading.Thread(
                    target=run_query,
                    args=(query, results, errors)
                )
                thread.start()
                batch_threads.append(thread)
            
            # Đợi batch hoàn thành
            for thread in batch_threads:
                thread.join()
        
        total_time = time.time() - start_time
        
        if not results:
            return {
                'success': False,
                'error': 'No successful concurrent queries'
            }
        
        times = [r['time'] for r in results]
        
        return {
            'success': True,
            'total_queries': len(queries),
            'successful_queries': len(results),
            'failed_queries': len(errors),
            'total_time': total_time,
            'avg_time': statistics.mean(times) if times else 0.0,
            'min_time': min(times) if times else 0.0,
            'max_time': max(times) if times else 0.0,
            'throughput_qps': len(results) / total_time if total_time > 0 else 0.0
        }
    
    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Tính percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
    
    def run_full_benchmark(
        self,
        test_queries: List[str],
        iterations: int = 3
    ) -> Dict:
        """
        Chạy full benchmark suite
        
        Args:
            test_queries: List câu hỏi để test
            iterations: Số lần lặp lại
            
        Returns:
            Dict chứa tất cả kết quả benchmark
        """
        print("="*60)
        print("🚀 BẮT ĐẦU BENCHMARK PERFORMANCE")
        print("="*60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_queries_count': len(test_queries),
            'iterations': iterations
        }
        
        # 1. Search benchmark
        search_results = self.benchmark_search(test_queries, iterations=iterations)
        results['search_benchmark'] = search_results
        
        # 2. Full query benchmark
        query_results = self.benchmark_query(test_queries, iterations=iterations)
        results['query_benchmark'] = query_results
        
        # 3. Concurrent benchmark (giảm số queries để tiết kiệm API)
        concurrent_results = self.benchmark_concurrent(test_queries[:min(2, len(test_queries))])  # Limit để tiết kiệm API
        results['concurrent_benchmark'] = concurrent_results
        
        return results
    
    def save_results(self, results: Dict, output_path: Path):
        """Lưu kết quả benchmark vào file JSON"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Đã lưu kết quả benchmark vào {output_path}")


def main():
    """Main function để chạy benchmark"""
    from pathlib import Path
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    index_path = project_root / "VectorDB" / "data" / "index" / "faiss_index.bin"
    chunks_path = project_root / "data_processing" / "chunks.json"
    mapping_path = project_root / "Embeddings" / "data" / "mappings" / "chunk_mapping.json"
    output_path = project_root / "evaluation" / "reports" / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Test queries (giảm xuống tối thiểu để tiết kiệm API quota)
    test_queries = [
        "Phạm vi điều chỉnh của luật là gì?"
    ]
    
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
    
    # Khởi tạo Benchmark
    print("\n📊 Đang khởi tạo Performance Benchmark...")
    benchmark = PerformanceBenchmark(rag_system)
    
    # Chạy benchmark
    results = benchmark.run_full_benchmark(test_queries, iterations=3)
    
    # In summary
    print("\n" + "="*60)
    print("📈 TỔNG KẾT BENCHMARK")
    print("="*60)
    
    if results.get('search_benchmark', {}).get('success'):
        sb = results['search_benchmark']
        print(f"\n🔍 Search Performance:")
        print(f"   Avg time: {sb['avg_time']:.3f}s")
        print(f"   Throughput: {sb['throughput_qps']:.2f} QPS")
        print(f"   P95: {sb['p95_time']:.3f}s")
    
    if results.get('query_benchmark', {}).get('success'):
        qb = results['query_benchmark']
        print(f"\n🤖 Full Query Performance:")
        print(f"   Avg time: {qb['avg_time']:.3f}s")
        print(f"   Throughput: {qb['throughput_qps']:.2f} QPS")
        print(f"   P95: {qb['p95_time']:.3f}s")
        print(f"   Avg answer length: {qb['avg_answer_length']:.0f} chars")
    
    if results.get('concurrent_benchmark', {}).get('success'):
        cb = results['concurrent_benchmark']
        print(f"\n⚡ Concurrent Performance:")
        print(f"   Success rate: {cb['successful_queries']}/{cb['total_queries']}")
        print(f"   Throughput: {cb['throughput_qps']:.2f} QPS")
    
    print("="*60)
    
    # Lưu kết quả
    benchmark.save_results(results, output_path)
    
    print(f"\n✅ Hoàn thành! Kết quả đã được lưu tại: {output_path}")


if __name__ == "__main__":
    main()

