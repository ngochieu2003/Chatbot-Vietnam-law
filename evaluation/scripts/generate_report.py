#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tạo báo cáo đánh giá từ kết quả JSON
Tạo HTML report đẹp mắt và dễ đọc
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def generate_html_report(evaluation_results: Dict, output_path: Path):
    """
    Tạo HTML report từ kết quả đánh giá
    
    Args:
        evaluation_results: Dict chứa kết quả đánh giá
        output_path: Đường dẫn file HTML output
    """
    
    # Extract data
    summary = {
        'total_tests': evaluation_results.get('total_tests', 0),
        'successful_tests': evaluation_results.get('successful_tests', 0),
        'failed_tests': evaluation_results.get('failed_tests', 0),
        'success_rate': evaluation_results.get('success_rate', 0.0),
        'average_score': evaluation_results.get('average_score', 0.0),
        'average_query_time': evaluation_results.get('average_query_time', 0.0),
        'category_scores': evaluation_results.get('category_scores', {}),
        'timestamp': evaluation_results.get('timestamp', '')
    }
    
    results = evaluation_results.get('results', [])
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Báo Cáo Đánh Giá Chatbot RAG</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .summary-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .summary-card h3 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        
        .summary-card .label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .category-scores {{
            margin-bottom: 40px;
        }}
        
        .category-scores h2 {{
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        
        .category-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        
        .category-item .name {{
            font-weight: bold;
            color: #333;
        }}
        
        .category-item .score {{
            font-size: 1.2em;
            color: #667eea;
            font-weight: bold;
        }}
        
        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .results-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        
        .results-table td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        
        .results-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .score-badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .score-excellent {{
            background: #28a745;
            color: white;
        }}
        
        .score-good {{
            background: #17a2b8;
            color: white;
        }}
        
        .score-fair {{
            background: #ffc107;
            color: #333;
        }}
        
        .score-poor {{
            background: #dc3545;
            color: white;
        }}
        
        .status-success {{
            color: #28a745;
            font-weight: bold;
        }}
        
        .status-failed {{
            color: #dc3545;
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Báo Cáo Đánh Giá Chatbot RAG</h1>
            <p>Generated: {summary['timestamp']}</p>
        </div>
        
        <div class="content">
            <div class="summary">
                <div class="summary-card">
                    <h3>Tổng số test</h3>
                    <div class="value">{summary['total_tests']}</div>
                </div>
                <div class="summary-card">
                    <h3>Thành công</h3>
                    <div class="value">{summary['successful_tests']}</div>
                    <div class="label">({summary['success_rate']:.1%})</div>
                </div>
                <div class="summary-card">
                    <h3>Điểm trung bình</h3>
                    <div class="value">{summary['average_score']:.2f}</div>
                    <div class="label">/ 1.0</div>
                </div>
                <div class="summary-card">
                    <h3>Thời gian TB</h3>
                    <div class="value">{summary['average_query_time']:.2f}s</div>
                    <div class="label">per query</div>
                </div>
            </div>
            
            <div class="category-scores">
                <h2>📈 Điểm theo Category</h2>
"""
    
    # Category scores
    for category, score in summary['category_scores'].items():
        html += f"""
                <div class="category-item">
                    <span class="name">{category}</span>
                    <span class="score">{score:.2f}</span>
                </div>
"""
    
    html += """
            </div>
            
            <h2>📋 Chi Tiết Kết Quả</h2>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Câu hỏi</th>
                        <th>Status</th>
                        <th>Overall Score</th>
                        <th>Keyword Coverage</th>
                        <th>Answer Quality</th>
                        <th>Time (s)</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Results table
    for result in results:
        test_id = result.get('test_id', 'N/A')
        question = result.get('question', '')[:50] + '...' if len(result.get('question', '')) > 50 else result.get('question', '')
        success = result.get('success', False)
        metrics = result.get('metrics', {})
        overall_score = metrics.get('overall_score', 0.0)
        keyword_coverage = metrics.get('keyword_coverage', {}).get('score', 0.0)
        answer_quality = metrics.get('answer_quality', {}).get('score', 0.0)
        query_time = result.get('query_time', 0.0)
        
        # Score badge class
        if overall_score >= 0.8:
            score_class = 'score-excellent'
        elif overall_score >= 0.6:
            score_class = 'score-good'
        elif overall_score >= 0.4:
            score_class = 'score-fair'
        else:
            score_class = 'score-poor'
        
        status_class = 'status-success' if success else 'status-failed'
        status_text = '✅ Success' if success else '❌ Failed'
        
        html += f"""
                    <tr>
                        <td>{test_id}</td>
                        <td>{question}</td>
                        <td class="{status_class}">{status_text}</td>
                        <td><span class="score-badge {score_class}">{overall_score:.2f}</span></td>
                        <td>{keyword_coverage:.2f}</td>
                        <td>{answer_quality:.2f}</td>
                        <td>{query_time:.2f}</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Generated by Chatbot RAG Evaluation System</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save HTML
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Đã tạo HTML report tại: {output_path}")


def main():
    """Main function"""
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <evaluation_results.json>")
        print("Example: python generate_report.py ../reports/evaluation_report_20241126_120000.json")
        return
    
    input_path = Path(sys.argv[1])
    
    if not input_path.exists():
        print(f"❌ Không tìm thấy file: {input_path}")
        return
    
    # Load results
    with open(input_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Generate report
    output_path = input_path.parent / f"{input_path.stem}.html"
    generate_html_report(results, output_path)
    
    print(f"\n✅ Hoàn thành! Mở file HTML trong browser để xem báo cáo.")


if __name__ == "__main__":
    main()

