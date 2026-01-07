#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script phân tích và đánh giá chất lượng dữ liệu cho chatbot pháp luật
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter
import json

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("Cảnh báo: BeautifulSoup4 chưa được cài đặt. Một số tính năng sẽ bị hạn chế.")


class DataQualityAnalyzer:
    """Phân tích chất lượng dữ liệu cho chatbot"""
    
    def __init__(self, dataset_path: str = None):
        if dataset_path is None:
            # Trỏ đến Dataset từ Data process
            base_path = Path(__file__).parent.parent
            self.dataset_path = base_path / "Dataset"
        else:
            self.dataset_path = Path(dataset_path)
        
        self.analysis_results = {
            'total_files': 0,
            'html_files': 0,
            'total_size': 0,
            'content_analysis': {},
            'issues': [],
            'recommendations': []
        }
    
    def analyze(self) -> Dict:
        """Phân tích toàn bộ dữ liệu"""
        print("="*70)
        print("PHÂN TÍCH CHẤT LƯỢNG DỮ LIỆU CHO CHATBOT PHÁP LUẬT")
        print("="*70)
        
        # Phân tích file HTML trong demuc
        self._analyze_html_files()
        
        # Phân tích cấu trúc nội dung
        self._analyze_content_structure()
        
        # Kiểm tra các vấn đề
        self._check_issues()
        
        # Đưa ra khuyến nghị
        self._generate_recommendations()
        
        # In kết quả
        self._print_results()
        
        return self.analysis_results
    
    def _analyze_html_files(self):
        """Phân tích các file HTML"""
        demuc_path = self.dataset_path / "demuc"
        
        if not demuc_path.exists():
            self.analysis_results['issues'].append("Không tìm thấy thư mục demuc")
            return
        
        html_files = list(demuc_path.glob("*.html"))
        self.analysis_results['html_files'] = len(html_files)
        self.analysis_results['total_files'] = len(html_files) + 1  # +1 cho BoPhapDien.html
        
        print(f"\n📁 Tìm thấy {len(html_files)} file HTML trong thư mục demuc")
        
        # Phân tích mẫu các file
        sample_size = min(10, len(html_files))
        sample_files = html_files[:sample_size]
        
        total_chars = 0
        total_dieu = 0
        total_chuong = 0
        total_noi_dung = 0
        
        for html_file in sample_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    total_chars += len(content)
                    
                    # Đếm các thành phần
                    total_dieu += len(re.findall(r'class=["\']pDieu["\']', content))
                    total_chuong += len(re.findall(r'class=["\']pChuong["\']', content))
                    total_noi_dung += len(re.findall(r'class=["\']pNoiDung["\']', content))
                    
                    self.analysis_results['total_size'] += html_file.stat().st_size
            except Exception as e:
                self.analysis_results['issues'].append(f"Lỗi đọc file {html_file.name}: {e}")
        
        # Ước tính cho toàn bộ dataset
        avg_chars = total_chars / sample_size if sample_size > 0 else 0
        avg_dieu = total_dieu / sample_size if sample_size > 0 else 0
        avg_chuong = total_chuong / sample_size if sample_size > 0 else 0
        avg_noi_dung = total_noi_dung / sample_size if sample_size > 0 else 0
        
        self.analysis_results['content_analysis'] = {
            'avg_file_size_chars': avg_chars,
            'estimated_total_chars': avg_chars * len(html_files),
            'avg_dieu_per_file': avg_dieu,
            'estimated_total_dieu': avg_dieu * len(html_files),
            'avg_chuong_per_file': avg_chuong,
            'estimated_total_chuong': avg_chuong * len(html_files),
            'avg_noi_dung_per_file': avg_noi_dung,
            'estimated_total_noi_dung': avg_noi_dung * len(html_files)
        }
        
        print(f"  ✓ Đã phân tích {sample_size} file mẫu")
        print(f"  ✓ Trung bình {avg_chars:,.0f} ký tự/file")
        print(f"  ✓ Trung bình {avg_dieu:.1f} điều/file")
    
    def _analyze_content_structure(self):
        """Phân tích cấu trúc nội dung"""
        demuc_path = self.dataset_path / "demuc"
        html_files = list(demuc_path.glob("*.html"))
        
        if not html_files:
            return
        
        # Phân tích một file mẫu chi tiết
        sample_file = html_files[0]
        
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if HAS_BS4:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Trích xuất các thành phần
                dieu_elements = soup.find_all('p', class_='pDieu')
                noi_dung_elements = soup.find_all('p', class_='pNoiDung')
                chuong_elements = soup.find_all('p', class_='pChuong')
                ghi_chu_elements = soup.find_all('p', class_='pGhiChu')
                
                # Phân tích nội dung văn bản
                sample_dieu = dieu_elements[0] if dieu_elements else None
                sample_noi_dung = noi_dung_elements[0] if noi_dung_elements else None
                
                structure_info = {
                    'has_structured_content': True,
                    'has_dieu': len(dieu_elements) > 0,
                    'has_chuong': len(chuong_elements) > 0,
                    'has_noi_dung': len(noi_dung_elements) > 0,
                    'has_ghi_chu': len(ghi_chu_elements) > 0,
                    'sample_dieu_text': sample_dieu.get_text(strip=True)[:100] if sample_dieu else None,
                    'sample_noi_dung_text': sample_noi_dung.get_text(strip=True)[:200] if sample_noi_dung else None,
                    'html_tags_present': True,
                    'has_links': len(soup.find_all('a')) > 0,
                    'has_scripts': len(soup.find_all('script')) > 0,
                    'has_styles': len(soup.find_all('style')) > 0
                }
                
                self.analysis_results['content_analysis'].update(structure_info)
            else:
                # Phân tích cơ bản không dùng BeautifulSoup
                has_dieu = 'class="pDieu"' in content or "class='pDieu'" in content
                has_chuong = 'class="pChuong"' in content or "class='pChuong'" in content
                has_noi_dung = 'class="pNoiDung"' in content or "class='pNoiDung'" in content
                
                self.analysis_results['content_analysis'].update({
                    'has_structured_content': has_dieu or has_chuong or has_noi_dung,
                    'has_dieu': has_dieu,
                    'has_chuong': has_chuong,
                    'has_noi_dung': has_noi_dung,
                    'html_tags_present': True
                })
                
        except Exception as e:
            self.analysis_results['issues'].append(f"Lỗi phân tích cấu trúc: {e}")
    
    def _check_issues(self):
        """Kiểm tra các vấn đề trong dữ liệu"""
        issues = []
        
        # Kiểm tra encoding
        demuc_path = self.dataset_path / "demuc"
        html_files = list(demuc_path.glob("*.html"))
        
        if html_files:
            # Kiểm tra một vài file
            for html_file in html_files[:5]:
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Kiểm tra có ký tự tiếng Việt không
                        if not any(ord(c) > 127 for c in content[:1000]):
                            issues.append(f"File {html_file.name} có thể có vấn đề encoding")
                except UnicodeDecodeError:
                    issues.append(f"File {html_file.name} không thể decode với UTF-8")
        
        # Kiểm tra cấu trúc
        ca = self.analysis_results['content_analysis']
        if not ca.get('has_structured_content', False):
            issues.append("Dữ liệu không có cấu trúc rõ ràng (thiếu class pDieu, pChuong, pNoiDung)")
        
        if ca.get('html_tags_present', False):
            issues.append("Dữ liệu chứa HTML tags - cần làm sạch trước khi sử dụng")
        
        if ca.get('has_scripts', False) or ca.get('has_styles', False):
            issues.append("Dữ liệu chứa script/style tags - cần loại bỏ")
        
        # Kiểm tra độ dài nội dung
        if ca.get('avg_dieu_per_file', 0) < 1:
            issues.append("Số lượng điều luật quá ít - có thể dữ liệu không đầy đủ")
        
        self.analysis_results['issues'] = issues
    
    def _generate_recommendations(self):
        """Tạo các khuyến nghị"""
        recommendations = []
        ca = self.analysis_results['content_analysis']
        issues = self.analysis_results['issues']
        
        # Khuyến nghị về làm sạch dữ liệu
        if any('HTML tags' in issue for issue in issues):
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Data Cleaning',
                'action': 'Loại bỏ HTML tags và trích xuất văn bản thuần túy',
                'description': 'Sử dụng BeautifulSoup hoặc regex để loại bỏ tất cả HTML tags, chỉ giữ lại nội dung văn bản'
            })
        
        if any('script' in issue.lower() for issue in issues):
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Data Cleaning',
                'action': 'Loại bỏ script và style tags',
                'description': 'Xóa tất cả <script> và <style> tags để giảm noise trong dữ liệu'
            })
        
        # Khuyến nghị về chunking
        if ca.get('estimated_total_dieu', 0) > 0:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Data Processing',
                'action': 'Chia nhỏ dữ liệu theo điều luật',
                'description': f'Chia dữ liệu thành {int(ca.get("estimated_total_dieu", 0))} chunks, mỗi chunk là một điều luật. Điều này giúp RAG system tìm kiếm chính xác hơn.'
            })
        
        # Khuyến nghị về metadata
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Metadata Extraction',
            'action': 'Trích xuất metadata cho mỗi điều luật',
            'description': 'Trích xuất: số điều, tên điều, chương, loại văn bản (Luật/Nghị định/Thông tư), ngày ban hành, ngày hiệu lực'
        })
        
        # Khuyến nghị về indexing
        recommendations.append({
            'priority': 'HIGH',
            'category': 'RAG Setup',
            'action': 'Tạo vector embeddings cho dữ liệu',
            'description': 'Sử dụng embedding model hỗ trợ tiếng Việt (như multilingual models) để tạo vector cho mỗi chunk'
        })
        
        # Khuyến nghị về preprocessing
        recommendations.append({
            'priority': 'LOW',
            'category': 'Data Preprocessing',
            'action': 'Chuẩn hóa văn bản',
            'description': 'Loại bỏ khoảng trắng thừa, chuẩn hóa dấu câu, xử lý các ký tự đặc biệt'
        })
        
        self.analysis_results['recommendations'] = recommendations
    
    def _print_results(self):
        """In kết quả phân tích"""
        print("\n" + "="*70)
        print("KẾT QUẢ PHÂN TÍCH")
        print("="*70)
        
        # Thống kê tổng quan
        print("\n📊 THỐNG KÊ TỔNG QUAN:")
        print(f"  • Tổng số file: {self.analysis_results['total_files']}")
        print(f"  • File HTML: {self.analysis_results['html_files']}")
        print(f"  • Kích thước ước tính: {self.analysis_results['total_size']/1024/1024:.2f} MB")
        
        ca = self.analysis_results['content_analysis']
        if ca:
            print(f"\n  • Tổng số ký tự ước tính: {ca.get('estimated_total_chars', 0):,.0f}")
            print(f"  • Tổng số điều luật ước tính: {int(ca.get('estimated_total_dieu', 0))}")
            print(f"  • Tổng số chương ước tính: {int(ca.get('estimated_total_chuong', 0))}")
        
        # Cấu trúc dữ liệu
        print("\n📋 CẤU TRÚC DỮ LIỆU:")
        if ca.get('has_structured_content'):
            print("  ✓ Dữ liệu có cấu trúc rõ ràng")
            print(f"    - Có điều luật (pDieu): {'✓' if ca.get('has_dieu') else '✗'}")
            print(f"    - Có chương (pChuong): {'✓' if ca.get('has_chuong') else '✗'}")
            print(f"    - Có nội dung (pNoiDung): {'✓' if ca.get('has_noi_dung') else '✗'}")
        else:
            print("  ✗ Dữ liệu không có cấu trúc rõ ràng")
        
        # Vấn đề
        print("\n⚠️  CÁC VẤN ĐỀ PHÁT HIỆN:")
        if self.analysis_results['issues']:
            for i, issue in enumerate(self.analysis_results['issues'], 1):
                print(f"  {i}. {issue}")
        else:
            print("  ✓ Không phát hiện vấn đề nghiêm trọng")
        
        # Khuyến nghị
        print("\n💡 KHUYẾN NGHỊ:")
        recommendations = self.analysis_results['recommendations']
        
        # Nhóm theo priority
        high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
        medium_priority = [r for r in recommendations if r['priority'] == 'MEDIUM']
        low_priority = [r for r in recommendations if r['priority'] == 'LOW']
        
        if high_priority:
            print("\n  🔴 ƯU TIÊN CAO:")
            for i, rec in enumerate(high_priority, 1):
                print(f"    {i}. [{rec['category']}] {rec['action']}")
                print(f"       → {rec['description']}")
        
        if medium_priority:
            print("\n  🟡 ƯU TIÊN TRUNG BÌNH:")
            for i, rec in enumerate(medium_priority, 1):
                print(f"    {i}. [{rec['category']}] {rec['action']}")
                print(f"       → {rec['description']}")
        
        if low_priority:
            print("\n  🟢 ƯU TIÊN THẤP:")
            for i, rec in enumerate(low_priority, 1):
                print(f"    {i}. [{rec['category']}] {rec['action']}")
                print(f"       → {rec['description']}")
        
        # Đánh giá tổng thể
        print("\n" + "="*70)
        print("ĐÁNH GIÁ TỔNG THỂ")
        print("="*70)
        
        score = 100
        if self.analysis_results['issues']:
            score -= len(self.analysis_results['issues']) * 10
        
        if not ca.get('has_structured_content'):
            score -= 30
        
        if score >= 80:
            status = "✅ SẴN SÀNG"
            message = "Dữ liệu đã sẵn sàng để xây dựng chatbot. Chỉ cần làm sạch cơ bản."
        elif score >= 60:
            status = "⚠️  CẦN XỬ LÝ"
            message = "Dữ liệu cần được làm sạch và xử lý trước khi sử dụng."
        else:
            status = "❌ CHƯA SẴN SÀNG"
            message = "Dữ liệu cần được xử lý đáng kể trước khi có thể sử dụng."
        
        print(f"\n{status}: {score}/100")
        print(f"\n{message}")
        
        print("\n" + "="*70)


def main():
    """Hàm main"""
    analyzer = DataQualityAnalyzer()
    results = analyzer.analyze()
    
    # Lưu kết quả ra file JSON
    output_file = analyzer.dataset_path / "data_quality_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Báo cáo chi tiết đã được lưu vào: {output_file}")
    
    return analyzer


if __name__ == "__main__":
    analyzer = main()

