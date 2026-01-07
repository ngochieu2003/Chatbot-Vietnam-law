#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module làm sạch dữ liệu HTML - Loại bỏ HTML tags và trích xuất văn bản thuần túy
Ưu tiên: HIGH
"""

import re
from pathlib import Path
from typing import Dict, Optional
from bs4 import BeautifulSoup, Tag, NavigableString


class DataCleaner:
    """Làm sạch dữ liệu HTML từ các file pháp điển"""
    
    def __init__(self):
        self.cleaned_count = 0
        self.error_count = 0
    
    def clean_html_file(self, html_file_path: Path) -> Optional[str]:
        """
        Làm sạch một file HTML và trả về văn bản thuần túy
        
        Args:
            html_file_path: Đường dẫn đến file HTML
            
        Returns:
            Văn bản đã được làm sạch hoặc None nếu có lỗi
        """
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Sử dụng BeautifulSoup để parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Loại bỏ script và style tags
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Làm sạch và trích xuất nội dung
            cleaned_text = self._extract_structured_content(soup)
            
            self.cleaned_count += 1
            return cleaned_text
            
        except Exception as e:
            print(f"Lỗi khi làm sạch file {html_file_path.name}: {e}")
            self.error_count += 1
            return None
    
    def _extract_structured_content(self, soup: BeautifulSoup) -> str:
        """
        Trích xuất nội dung có cấu trúc từ HTML
        
        Args:
            soup: BeautifulSoup object đã parse
            
        Returns:
            Văn bản đã được làm sạch và có cấu trúc
        """
        content_parts = []
        
        # Tìm container chính
        content_div = soup.find('div', class_='_content')
        if not content_div:
            # Nếu không có div._content, lấy toàn bộ body
            content_div = soup.find('body') or soup
        
        # Duyệt qua các phần tử có cấu trúc
        for element in content_div.children:
            if isinstance(element, Tag):
                text = self._extract_element_text(element)
                if text and text.strip():
                    content_parts.append(text.strip())
        
        return '\n\n'.join(content_parts)
    
    def _extract_element_text(self, element: Tag) -> str:
        """
        Trích xuất văn bản từ một phần tử HTML, giữ lại cấu trúc
        
        Args:
            element: BeautifulSoup Tag element
            
        Returns:
            Văn bản đã được làm sạch
        """
        # Xác định loại phần tử
        classes = element.get('class', [])
        
        if 'pDieu' in classes:
            # Điều luật - giữ nguyên cấu trúc
            return self._clean_text(element.get_text(separator=' ', strip=True))
        
        elif 'pChuong' in classes:
            # Chương - giữ nguyên
            return self._clean_text(element.get_text(separator=' ', strip=True))
        
        elif 'pNoiDung' in classes:
            # Nội dung điều luật - làm sạch kỹ hơn
            text = element.get_text(separator='\n', strip=True)
            # Loại bỏ các dòng trống thừa
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return self._clean_text('\n'.join(lines))
        
        elif 'pGhiChu' in classes:
            # Ghi chú - có thể giữ lại hoặc loại bỏ tùy nhu cầu
            # Ở đây giữ lại vì chứa metadata quan trọng
            return self._clean_text(element.get_text(separator=' ', strip=True))
        
        elif 'pChiDan' in classes:
            # Chỉ dẫn - có thể giữ lại hoặc loại bỏ
            # Ở đây giữ lại vì có thể hữu ích cho RAG
            return self._clean_text(element.get_text(separator=' ', strip=True))
        
        else:
            # Các phần tử khác - chỉ lấy text
            return self._clean_text(element.get_text(separator=' ', strip=True))
    
    def _clean_text(self, text: str) -> str:
        """
        Làm sạch văn bản: loại bỏ khoảng trắng thừa, chuẩn hóa
        
        Args:
            text: Văn bản cần làm sạch
            
        Returns:
            Văn bản đã được làm sạch
        """
        if not text:
            return ""
        
        # Loại bỏ các ký tự đặc biệt không cần thiết
        text = re.sub(r'\s+', ' ', text)  # Nhiều khoảng trắng thành 1
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Nhiều dòng trống thành 2
        text = text.strip()
        
        return text
    
    def clean_all_files(self, input_dir: Path, output_dir: Path) -> Dict:
        """
        Làm sạch tất cả các file HTML trong thư mục
        
        Args:
            input_dir: Thư mục chứa file HTML gốc
            output_dir: Thư mục lưu file đã làm sạch
            
        Returns:
            Dictionary chứa thống kê kết quả
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        html_files = list(input_dir.glob("*.html"))
        total_files = len(html_files)
        
        print(f"Bắt đầu làm sạch {total_files} file HTML...")
        
        for html_file in html_files:
            cleaned_text = self.clean_html_file(html_file)
            
            if cleaned_text:
                # Lưu file đã làm sạch
                output_file = output_dir / f"{html_file.stem}_cleaned.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_text)
        
        result = {
            'total_files': total_files,
            'cleaned_count': self.cleaned_count,
            'error_count': self.error_count,
            'success_rate': (self.cleaned_count / total_files * 100) if total_files > 0 else 0
        }
        
        print(f"\nHoàn thành làm sạch:")
        print(f"  - Tổng số file: {total_files}")
        print(f"  - Thành công: {self.cleaned_count}")
        print(f"  - Lỗi: {self.error_count}")
        print(f"  - Tỷ lệ thành công: {result['success_rate']:.2f}%")
        
        return result


def main():
    """Hàm main để chạy thử"""
    from pathlib import Path
    
    dataset_path = Path(__file__).parent
    input_dir = dataset_path / "demuc"
    output_dir = dataset_path / "cleaned_data"
    
    cleaner = DataCleaner()
    result = cleaner.clean_all_files(input_dir, output_dir)
    
    return result


if __name__ == "__main__":
    main()

