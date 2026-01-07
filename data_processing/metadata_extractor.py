#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module trích xuất metadata từ các điều luật
Ưu tiên: MEDIUM
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup, Tag


class MetadataExtractor:
    """Trích xuất metadata từ các file HTML pháp điển"""
    
    def __init__(self):
        self.extracted_count = 0
        self.error_count = 0
    
    def extract_from_html_file(self, html_file_path: Path) -> List[Dict]:
        """
        Trích xuất metadata từ một file HTML
        
        Args:
            html_file_path: Đường dẫn đến file HTML
            
        Returns:
            List các dictionary chứa metadata của từng điều luật
        """
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Lấy thông tin đề mục từ đầu file
            demuc_info = self._extract_demuc_info(soup, html_file_path)
            
            # Trích xuất metadata cho từng điều luật
            metadata_list = []
            content_div = soup.find('div', class_='_content')
            if not content_div:
                content_div = soup.find('body') or soup
            
            current_chuong = None
            current_dieu = None
            current_ghi_chu = None
            
            for element in content_div.children:
                if isinstance(element, Tag):
                    classes = element.get('class', [])
                    
                    if 'pChuong' in classes:
                        current_chuong = self._extract_chuong_info(element)
                    
                    elif 'pDieu' in classes:
                        # Lưu điều luật trước đó nếu có
                        if current_dieu:
                            metadata_list.append({
                                **demuc_info,
                                **current_chuong,
                                **current_dieu,
                                'ghi_chu': current_ghi_chu
                            })
                        
                        # Bắt đầu điều luật mới
                        current_dieu = self._extract_dieu_info(element)
                        current_ghi_chu = None
                    
                    elif 'pGhiChu' in classes:
                        current_ghi_chu = self._extract_ghi_chu_info(element)
                        if current_dieu:
                            current_dieu['ngay_ban_hanh'] = current_ghi_chu.get('ngay_ban_hanh')
                            current_dieu['ngay_hieu_luc'] = current_ghi_chu.get('ngay_hieu_luc')
                            current_dieu['loai_van_ban'] = current_ghi_chu.get('loai_van_ban')
                            current_dieu['so_van_ban'] = current_ghi_chu.get('so_van_ban')
            
            # Lưu điều luật cuối cùng
            if current_dieu:
                metadata_list.append({
                    **demuc_info,
                    **current_chuong,
                    **current_dieu,
                    'ghi_chu': current_ghi_chu
                })
            
            self.extracted_count += len(metadata_list)
            return metadata_list
            
        except Exception as e:
            print(f"Lỗi khi trích xuất metadata từ {html_file_path.name}: {e}")
            self.error_count += 1
            return []
    
    def _extract_demuc_info(self, soup: BeautifulSoup, file_path: Path) -> Dict:
        """Trích xuất thông tin đề mục"""
        demuc_info = {
            'file_id': file_path.stem,
            'file_name': file_path.name,
            'de_muc': None,
            'de_muc_so': None
        }
        
        # Tìm thẻ h3 chứa đề mục
        h3_tag = soup.find('h3')
        if h3_tag:
            text = h3_tag.get_text(strip=True)
            # Ví dụ: "Đề mục 39.14\nCảnh sát cơ động"
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if lines:
                # Tìm số đề mục
                match = re.search(r'Đề mục\s+([\d.]+)', lines[0])
                if match:
                    demuc_info['de_muc_so'] = match.group(1)
                    if len(lines) > 1:
                        demuc_info['de_muc'] = lines[1]
                    else:
                        demuc_info['de_muc'] = lines[0]
        
        return demuc_info
    
    def _extract_chuong_info(self, element: Tag) -> Dict:
        """Trích xuất thông tin chương"""
        text = element.get_text(strip=True)
        chuong_info = {
            'chuong': None,
            'chuong_so': None,
            'chuong_ten': None
        }
        
        # Tìm số chương và tên chương
        # Ví dụ: "Chương I" hoặc "Chương II\nNHỮNG QUY ĐỊNH CHUNG"
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            match = re.search(r'Chương\s+([IVX]+|[0-9]+)', lines[0], re.IGNORECASE)
            if match:
                chuong_info['chuong_so'] = match.group(1)
                chuong_info['chuong'] = lines[0]
                if len(lines) > 1:
                    chuong_info['chuong_ten'] = lines[1]
        
        return chuong_info
    
    def _extract_dieu_info(self, element: Tag) -> Dict:
        """Trích xuất thông tin điều luật"""
        text = element.get_text(strip=True)
        dieu_info = {
            'dieu': text,
            'dieu_so': None,
            'dieu_ten': None,
            'dieu_id': None
        }
        
        # Lấy ID từ thuộc tính name
        name_attr = element.find('a', attrs={'name': True})
        if name_attr:
            dieu_info['dieu_id'] = name_attr.get('name')
        
        # Trích xuất số điều và tên điều
        # Ví dụ: "Điều 39.14.LQ.1. Phạm vi điều chỉnh"
        match = re.match(r'Điều\s+([\d.]+(?:\.[A-Z]+)?(?:\.[\d]+)?)\.?\s*(.+)', text)
        if match:
            dieu_info['dieu_so'] = match.group(1)
            dieu_info['dieu_ten'] = match.group(2).strip()
        
        return dieu_info
    
    def _extract_ghi_chu_info(self, element: Tag) -> Dict:
        """Trích xuất thông tin từ ghi chú (ngày ban hành, hiệu lực, loại văn bản)"""
        ghi_chu_info = {
            'ngay_ban_hanh': None,
            'ngay_hieu_luc': None,
            'loai_van_ban': None,
            'so_van_ban': None,
            'co_quan_ban_hanh': None
        }
        
        text = element.get_text(strip=True)
        
        # Trích xuất loại văn bản (Luật, Nghị định, Thông tư)
        loai_match = re.search(r'(Luật|Nghị định|Thông tư|Pháp lệnh|Quyết định)', text)
        if loai_match:
            ghi_chu_info['loai_van_ban'] = loai_match.group(1)
        
        # Trích xuất số văn bản
        # Ví dụ: "Luật số 04/2022/QH15"
        so_vb_match = re.search(r'số\s+([\d/]+/[A-Z\d]+)', text, re.IGNORECASE)
        if so_vb_match:
            ghi_chu_info['so_van_ban'] = so_vb_match.group(1)
        
        # Trích xuất ngày ban hành
        # Ví dụ: "ngày 14/06/2022"
        ngay_bh_match = re.search(r'ngày\s+(\d{1,2}/\d{1,2}/\d{4})', text, re.IGNORECASE)
        if ngay_bh_match:
            try:
                date_str = ngay_bh_match.group(1)
                ghi_chu_info['ngay_ban_hanh'] = self._parse_date(date_str)
            except:
                ghi_chu_info['ngay_ban_hanh'] = date_str
        
        # Trích xuất ngày hiệu lực
        # Ví dụ: "có hiệu lực thi hành kể từ ngày 01/01/2023"
        ngay_hl_match = re.search(r'hiệu lực.*?ngày\s+(\d{1,2}/\d{1,2}/\d{4})', text, re.IGNORECASE)
        if ngay_hl_match:
            try:
                date_str = ngay_hl_match.group(1)
                ghi_chu_info['ngay_hieu_luc'] = self._parse_date(date_str)
            except:
                ghi_chu_info['ngay_hieu_luc'] = date_str
        
        # Trích xuất cơ quan ban hành
        co_quan_match = re.search(r'của\s+([^,]+)', text)
        if co_quan_match:
            ghi_chu_info['co_quan_ban_hanh'] = co_quan_match.group(1).strip()
        
        return ghi_chu_info
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse ngày tháng từ string"""
        try:
            # Format: dd/mm/yyyy
            parts = date_str.split('/')
            if len(parts) == 3:
                return f"{parts[2]}-{parts[1]}-{parts[0]}"  # ISO format
        except:
            pass
        return date_str
    
    def extract_all_files(self, input_dir: Path, output_file: Path) -> Dict:
        """
        Trích xuất metadata từ tất cả các file HTML
        
        Args:
            input_dir: Thư mục chứa file HTML
            output_file: File JSON để lưu metadata
            
        Returns:
            Dictionary chứa thống kê
        """
        import json
        
        all_metadata = []
        html_files = list(input_dir.glob("*.html"))
        
        print(f"Bắt đầu trích xuất metadata từ {len(html_files)} file...")
        
        for html_file in html_files:
            metadata_list = self.extract_from_html_file(html_file)
            all_metadata.extend(metadata_list)
        
        # Lưu vào file JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, ensure_ascii=False, indent=2)
        
        result = {
            'total_files': len(html_files),
            'total_articles': len(all_metadata),
            'extracted_count': self.extracted_count,
            'error_count': self.error_count
        }
        
        print(f"\nHoàn thành trích xuất metadata:")
        print(f"  - Tổng số file: {len(html_files)}")
        print(f"  - Tổng số điều luật: {len(all_metadata)}")
        print(f"  - Lỗi: {self.error_count}")
        
        return result


def main():
    """Hàm main để chạy thử"""
    from pathlib import Path
    
    # Trỏ đến Dataset/demuc từ Data process
    base_path = Path(__file__).parent.parent
    input_dir = base_path / "Dataset" / "demuc"
    output_file = Path(__file__).parent / "metadata.json"
    
    extractor = MetadataExtractor()
    result = extractor.extract_all_files(input_dir, output_file)
    
    return result


if __name__ == "__main__":
    main()



