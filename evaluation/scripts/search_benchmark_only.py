#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script benchmark chỉ cho Search Performance (không gọi LLM)
Chỉ đo FAISS retrieval performance - KHÔNG tốn API quota
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


class SearchOnlyBenchmark:
    """Class benchmark chỉ cho search performance (không gọi LLM)"""
    
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
        iterations: int = 3
    ) -> Dict:
        """
        Benchmark search performance (chỉ FAISS, không gọi LLM)
        
        Args:
            queries: List câu hỏi để test
            top_k: Số kết quả retrieve
            iterations: Số lần lặp lại mỗi query
            
        Returns:
            Dict chứa kết quả benchmark
        """
        print(f"\n🔍 Benchmarking search performance (FAISS only - không tốn API)...")
        print(f"   Queries: {len(queries)}, Top-K: {top_k}, Iterations: {iterations}\n")
        
        search_times = []
        all_distances = []
        all_chunk_counts = []
        
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] Testing: {query[:60]}...")
            
            for iteration in range(iterations):
                start_time = time.time()
                try:
                    results = self.rag_system.search(query, top_k=top_k)
                    elapsed = time.time() - start_time
                    search_times.append(elapsed)
                    
                    # Lấy distances nếu có
                    distances = results.get('distances', [])
                    if distances:
                        all_distances.extend(distances)
                    
                    # Đếm số chunks
                    chunks = results.get('chunks', [])
                    all_chunk_counts.append(len(chunks))
                    
                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    continue
        
        if not search_times:
            return {
                'success': False,
                'error': 'No successful searches'
            }
        
        # Tính toán statistics
        avg_distance = statistics.mean(all_distances) if all_distances else 0.0
        min_distance = min(all_distances) if all_distances else 0.0
        max_distance = max(all_distances) if all_distances else 0.0
        
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
            'throughput_qps': 1.0 / statistics.mean(search_times) if search_times else 0.0,
            'retrieval_quality': {
                'avg_distance': avg_distance,
                'min_distance': min_distance,
                'max_distance': max_distance,
                'total_results': len(all_distances),
                'avg_chunks_per_query': statistics.mean(all_chunk_counts) if all_chunk_counts else 0.0
            }
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
    
    def save_results(self, results: Dict, output_path: Path):
        """Lưu kết quả benchmark vào file JSON"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Đã lưu kết quả benchmark vào {output_path}")


def main():
    """Main function để chạy search-only benchmark"""
    import argparse
    from pathlib import Path
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Benchmark Search Performance (không tốn API)')
    parser.add_argument(
        '--queries',
        type=int,
        default=5,
        help='Số queries để test (mặc định: 5)'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=3,
        help='Số lần lặp lại mỗi query (mặc định: 3)'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Số kết quả retrieve (mặc định: 5)'
    )
    args = parser.parse_args()
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    index_path = project_root / "VectorDB" / "data" / "index" / "faiss_index.bin"
    chunks_path = project_root / "data_processing" / "chunks.json"
    mapping_path = project_root / "Embeddings" / "data" / "mappings" / "chunk_mapping.json"
    output_path = project_root / "evaluation" / "reports" / f"search_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Test queries (có thể tăng số lượng vì không tốn API)
    test_queries = [
        "Phạm vi điều chỉnh của luật là gì?",
        "Quy định về thời hiệu khởi kiện",
        "Điều kiện để được cấp giấy phép kinh doanh",
        "Mức phạt vi phạm giao thông",
        "Quyền và nghĩa vụ của người lao động",
        "Quy định về hợp đồng lao động",
        "Thủ tục đăng ký doanh nghiệp",
        "Quy định về thuế giá trị gia tăng",
        "Quy định về bảo hiểm xã hội",
        "Quy định về nghĩa vụ quân sự"
    ]
    
    # Giới hạn số queries nếu có
    if args.queries > 0:
        test_queries = test_queries[:args.queries]
    
    # Khởi tạo RAG System
    print("🚀 Đang khởi tạo RAG System...")
    print("   ⚠️  Lưu ý: Script này KHÔNG gọi LLM, chỉ test FAISS search")
    print("   ✅ KHÔNG tốn API quota!\n")
    
    rag_system = RAGSystem(
        llm_provider='gemini',
        llm_model='models/gemini-2.5-flash',
        top_k=args.top_k
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
    print("📊 Đang khởi tạo Search-Only Benchmark...")
    benchmark = SearchOnlyBenchmark(rag_system)
    
    # Chạy benchmark
    print("="*60)
    print("🚀 BẮT ĐẦU SEARCH BENCHMARK (KHÔNG TỐN API)")
    print("="*60)
    
    results = benchmark.benchmark_search(
        test_queries,
        top_k=args.top_k,
        iterations=args.iterations
    )
    
    # In summary
    print("\n" + "="*60)
    print("📈 TỔNG KẾT SEARCH BENCHMARK")
    print("="*60)
    
    if results.get('success'):
        print(f"\n✅ Thành công: {results['successful_queries']}/{results['total_queries']} queries")
        print(f"\n🔍 Search Performance:")
        print(f"   Min time: {results['min_time']:.4f}s")
        print(f"   Max time: {results['max_time']:.4f}s")
        print(f"   Avg time: {results['avg_time']:.4f}s")
        print(f"   Median time: {results['median_time']:.4f}s")
        print(f"   Std dev: {results['std_time']:.4f}s")
        print(f"   P95: {results['p95_time']:.4f}s")
        print(f"   P99: {results['p99_time']:.4f}s")
        print(f"   Throughput: {results['throughput_qps']:.2f} QPS")
        
        rq = results.get('retrieval_quality', {})
        if rq:
            print(f"\n📊 Retrieval Quality:")
            print(f"   Avg distance: {rq['avg_distance']:.4f}")
            print(f"   Min distance: {rq['min_distance']:.4f}")
            print(f"   Max distance: {rq['max_distance']:.4f}")
            print(f"   Avg chunks per query: {rq['avg_chunks_per_query']:.2f}")
    else:
        print(f"\n❌ Lỗi: {results.get('error', 'Unknown error')}")
    
    print("="*60)
    print("\n💰 API Calls: 0 (chỉ dùng FAISS, không gọi LLM)")
    
    # Lưu kết quả
    benchmark.save_results(results, output_path)
    
    print(f"\n✅ Hoàn thành! Kết quả đã được lưu tại: {output_path}")


if __name__ == "__main__":
    main()


