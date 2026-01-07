#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script phân tích kết quả evaluation và tạo báo cáo đánh giá
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime


def analyze_evaluation_results(results_path: Path) -> Dict:
    """
    Phân tích kết quả evaluation và tạo báo cáo đánh giá
    
    Args:
        results_path: Đường dẫn đến file JSON kết quả
        
    Returns:
        Dict chứa phân tích chi tiết
    """
    with open(results_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Extract summary
    summary = {
        'total_tests': results.get('total_tests', 0),
        'successful_tests': results.get('successful_tests', 0),
        'failed_tests': results.get('failed_tests', 0),
        'success_rate': results.get('success_rate', 0.0),
        'average_score': results.get('average_score', 0.0),
        'average_query_time': results.get('average_query_time', 0.0),
        'category_scores': results.get('category_scores', {})
    }
    
    # Analyze individual results
    test_results = results.get('results', [])
    
    # Collect all metrics
    keyword_scores = []
    source_relevance_scores = []
    answer_quality_scores = []
    retrieval_quality_scores = []
    answer_length_scores = []
    overall_scores = []
    query_times = []
    
    # Category analysis
    category_metrics = {}
    
    # Issue detection
    issues = []
    strengths = []
    
    for result in test_results:
        if not result.get('success', False):
            issues.append(f"Test {result.get('test_id', 'unknown')} failed: {result.get('error', 'Unknown error')}")
            continue
        
        metrics = result.get('metrics', {})
        
        # Collect scores
        keyword_cov = metrics.get('keyword_coverage', {}).get('score', 0.0)
        source_rel = metrics.get('source_relevance', {}).get('score', 0.0)
        answer_qual = metrics.get('answer_quality', {}).get('score', 0.0)
        retrieval_qual = metrics.get('retrieval_quality', {}).get('quality_score', 0.0)
        answer_len = metrics.get('answer_length', 1.0)
        overall = metrics.get('overall_score', 0.0)
        
        keyword_scores.append(keyword_cov)
        source_relevance_scores.append(source_rel)
        answer_quality_scores.append(answer_qual)
        retrieval_quality_scores.append(retrieval_qual)
        answer_length_scores.append(answer_len)
        overall_scores.append(overall)
        query_times.append(result.get('query_time', 0.0))
        
        # Category analysis
        category = result.get('category', 'unknown')
        if category not in category_metrics:
            category_metrics[category] = {
                'count': 0,
                'scores': [],
                'times': []
            }
        category_metrics[category]['count'] += 1
        category_metrics[category]['scores'].append(overall)
        category_metrics[category]['times'].append(result.get('query_time', 0.0))
        
        # Detect issues
        if keyword_cov < 0.5:
            issues.append(f"Test {result.get('test_id')}: Keyword coverage thấp ({keyword_cov:.2f})")
        
        if answer_qual < 0.5:
            issues.append(f"Test {result.get('test_id')}: Answer quality thấp ({answer_qual:.2f})")
            if metrics.get('answer_quality', {}).get('has_error', False):
                issues.append(f"  → Có lỗi trong câu trả lời")
        
        if retrieval_qual < 0.3:
            issues.append(f"Test {result.get('test_id')}: Retrieval quality thấp ({retrieval_qual:.2f})")
        
        if result.get('query_time', 0) > 30:
            issues.append(f"Test {result.get('test_id')}: Query time quá lâu ({result.get('query_time', 0):.2f}s)")
        
        # Detect strengths
        if keyword_cov >= 0.9:
            strengths.append(f"Test {result.get('test_id')}: Keyword coverage xuất sắc ({keyword_cov:.2f})")
        
        if answer_qual >= 0.9:
            strengths.append(f"Test {result.get('test_id')}: Answer quality tốt ({answer_qual:.2f})")
        
        if overall >= 0.8:
            strengths.append(f"Test {result.get('test_id')}: Overall score cao ({overall:.2f})")
    
    # Calculate averages
    def safe_avg(lst):
        return sum(lst) / len(lst) if lst else 0.0
    
    analysis = {
        'summary': summary,
        'metrics_average': {
            'keyword_coverage': safe_avg(keyword_scores),
            'source_relevance': safe_avg(source_relevance_scores),
            'answer_quality': safe_avg(answer_quality_scores),
            'retrieval_quality': safe_avg(retrieval_quality_scores),
            'answer_length': safe_avg(answer_length_scores),
            'overall_score': safe_avg(overall_scores),
            'query_time': safe_avg(query_times)
        },
        'metrics_min': {
            'keyword_coverage': min(keyword_scores) if keyword_scores else 0.0,
            'source_relevance': min(source_relevance_scores) if source_relevance_scores else 0.0,
            'answer_quality': min(answer_quality_scores) if answer_quality_scores else 0.0,
            'retrieval_quality': min(retrieval_quality_scores) if retrieval_quality_scores else 0.0,
            'overall_score': min(overall_scores) if overall_scores else 0.0,
            'query_time': min(query_times) if query_times else 0.0
        },
        'metrics_max': {
            'keyword_coverage': max(keyword_scores) if keyword_scores else 0.0,
            'source_relevance': max(source_relevance_scores) if source_relevance_scores else 0.0,
            'answer_quality': max(answer_quality_scores) if answer_quality_scores else 0.0,
            'retrieval_quality': max(retrieval_quality_scores) if retrieval_quality_scores else 0.0,
            'overall_score': max(overall_scores) if overall_scores else 0.0,
            'query_time': max(query_times) if query_times else 0.0
        },
        'category_analysis': {
            cat: {
                'count': data['count'],
                'avg_score': safe_avg(data['scores']),
                'avg_time': safe_avg(data['times'])
            }
            for cat, data in category_metrics.items()
        },
        'issues': issues,
        'strengths': strengths
    }
    
    # Generate recommendations
    analysis['recommendations'] = generate_recommendations(summary, analysis)
    
    return analysis


def generate_recommendations(summary: Dict, analysis: Dict) -> List[str]:
    """Tạo các khuyến nghị cải thiện"""
    recommendations = []
    
    avg_score = summary.get('average_score', 0.0)
    avg_time = summary.get('average_query_time', 0.0)
    
    # Score recommendations
    if avg_score < 0.5:
        recommendations.append("⚠️ Điểm tổng thể thấp (< 0.5). Cần cải thiện chất lượng retrieval và generation")
    elif avg_score < 0.7:
        recommendations.append("📈 Điểm tổng thể ở mức trung bình. Có thể cải thiện bằng cách:")
        recommendations.append("   - Tối ưu hóa embedding model")
        recommendations.append("   - Cải thiện prompt engineering")
        recommendations.append("   - Tăng số chunks retrieved")
    else:
        recommendations.append("✅ Điểm tổng thể tốt! Tiếp tục duy trì và tối ưu hóa")
    
    # Time recommendations
    if avg_time > 20:
        recommendations.append("⏱️ Thời gian query trung bình khá lâu (>20s). Có thể:")
        recommendations.append("   - Giảm số chunks retrieve (top_k)")
        recommendations.append("   - Sử dụng model nhanh hơn (gemini-2.5-flash)")
        recommendations.append("   - Tối ưu hóa retry logic")
    
    # Metric-specific recommendations
    metrics_avg = analysis.get('metrics_average', {})
    
    if metrics_avg.get('retrieval_quality', 0.0) < 0.3:
        recommendations.append("🔍 Retrieval quality thấp. Cần:")
        recommendations.append("   - Kiểm tra embedding model có phù hợp không")
        recommendations.append("   - Xem xét cải thiện chunking strategy")
        recommendations.append("   - Tăng số chunks retrieve")
    
    if metrics_avg.get('answer_quality', 0.0) < 0.7:
        recommendations.append("💬 Answer quality cần cải thiện:")
        recommendations.append("   - Tối ưu prompt template")
        recommendations.append("   - Kiểm tra LLM model và parameters")
        recommendations.append("   - Xử lý tốt hơn các trường hợp không tìm thấy thông tin")
    
    if metrics_avg.get('keyword_coverage', 0.0) < 0.7:
        recommendations.append("🔑 Keyword coverage thấp:")
        recommendations.append("   - Cải thiện cách format context cho LLM")
        recommendations.append("   - Đảm bảo LLM hiểu và sử dụng keywords từ context")
    
    return recommendations


def print_analysis_report(analysis: Dict):
    """In báo cáo phân tích ra console"""
    print("\n" + "="*70)
    print("📊 BÁO CÁO ĐÁNH GIÁ CHATBOT RAG")
    print("="*70)
    
    summary = analysis['summary']
    metrics_avg = analysis['metrics_average']
    
    # Overall Summary
    print("\n📈 TỔNG QUAN")
    print("-" * 70)
    print(f"Tổng số test cases: {summary['total_tests']}")
    print(f"Thành công: {summary['successful_tests']} ({summary['success_rate']:.1%})")
    print(f"Thất bại: {summary['failed_tests']}")
    print(f"Điểm trung bình: {summary['average_score']:.2f}/1.0")
    print(f"Thời gian trung bình: {summary['average_query_time']:.2f}s")
    
    # Score Interpretation
    avg_score = summary['average_score']
    if avg_score >= 0.8:
        score_grade = "🟢 XUẤT SẮC"
    elif avg_score >= 0.7:
        score_grade = "🟡 TỐT"
    elif avg_score >= 0.6:
        score_grade = "🟠 TRUNG BÌNH"
    elif avg_score >= 0.5:
        score_grade = "🔴 CẦN CẢI THIỆN"
    else:
        score_grade = "❌ YẾU"
    
    print(f"\nĐánh giá tổng thể: {score_grade}")
    
    # Metrics Breakdown
    print("\n📊 CHI TIẾT METRICS")
    print("-" * 70)
    print(f"Keyword Coverage:     {metrics_avg['keyword_coverage']:.2f} (Tốt nếu > 0.7)")
    print(f"Source Relevance:      {metrics_avg['source_relevance']:.2f} (Tốt nếu > 0.7)")
    print(f"Answer Quality:       {metrics_avg['answer_quality']:.2f} (Tốt nếu > 0.7)")
    print(f"Retrieval Quality:    {metrics_avg['retrieval_quality']:.2f} (Tốt nếu > 0.5)")
    print(f"Answer Length:        {metrics_avg['answer_length']:.2f} (Tốt nếu = 1.0)")
    print(f"Overall Score:        {metrics_avg['overall_score']:.2f}")
    print(f"Query Time:           {metrics_avg['query_time']:.2f}s")
    
    # Category Analysis
    if analysis.get('category_analysis'):
        print("\n📁 PHÂN TÍCH THEO CATEGORY")
        print("-" * 70)
        for category, data in analysis['category_analysis'].items():
            print(f"{category:20s}: Score {data['avg_score']:.2f}, Time {data['avg_time']:.2f}s ({data['count']} tests)")
    
    # Strengths
    if analysis.get('strengths'):
        print("\n✅ ĐIỂM MẠNH")
        print("-" * 70)
        for strength in analysis['strengths']:
            print(f"  • {strength}")
    
    # Issues
    if analysis.get('issues'):
        print("\n⚠️ VẤN ĐỀ CẦN QUAN TÂM")
        print("-" * 70)
        for issue in analysis['issues']:
            print(f"  • {issue}")
    else:
        print("\n✅ Không có vấn đề nghiêm trọng được phát hiện")
    
    # Recommendations
    if analysis.get('recommendations'):
        print("\n💡 KHUYẾN NGHỊ CẢI THIỆN")
        print("-" * 70)
        for rec in analysis['recommendations']:
            print(f"  {rec}")
    
    print("\n" + "="*70)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Phân tích kết quả evaluation')
    parser.add_argument(
        'results_file',
        type=str,
        help='Đường dẫn đến file JSON kết quả evaluation'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Lưu báo cáo phân tích vào file JSON (optional)'
    )
    
    args = parser.parse_args()
    
    results_path = Path(args.results_file)
    
    if not results_path.exists():
        print(f"❌ Không tìm thấy file: {results_path}")
        return
    
    # Analyze
    analysis = analyze_evaluation_results(results_path)
    
    # Print report
    print_analysis_report(analysis)
    
    # Save if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Đã lưu báo cáo phân tích vào: {output_path}")


if __name__ == "__main__":
    main()

