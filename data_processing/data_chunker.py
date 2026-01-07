#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module chia nhỏ dữ liệu theo điều luật (chunking)
Ưu tiên: MEDIUM
Mỗi chunk là một điều luật để RAG system tìm kiếm chính xác hơn
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Tag


class DataChunker:
    """Chia nhỏ dữ liệu thành các chunks theo điều luật"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Args:
            chunk_size: Kích thước tối đa của mỗi chunk (số ký tự)
            chunk_overlap: Số ký tự overlap giữa các chunk
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunks = []
    
    def chunk_html_file(self, html_file_path: Path, metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Chia nhỏ một file HTML thành các chunks
        
        Args:
            html_file_path: Đường dẫn đến file HTML
            metadata: Metadata của file (nếu có)
            
        Returns:
            List các chunks, mỗi chunk là một dictionary
        """
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            content_div = soup.find('div', class_='_content')
            if not content_div:
                content_div = soup.find('body') or soup
            
            chunks = []
            current_chuong = None
            current_dieu = None
            current_ghi_chu = None
            current_noi_dung = []
            
            for element in content_div.children:
                if isinstance(element, Tag):
                    classes = element.get('class', [])
                    
                    if 'pChuong' in classes:
                        current_chuong = element.get_text(strip=True)
                    
                    elif 'pDieu' in classes:
                        # Lưu điều luật trước đó nếu có
                        if current_dieu and current_noi_dung:
                            chunk = self._create_chunk(
                                current_dieu,
                                current_noi_dung,
                                current_chuong,
                                current_ghi_chu,
                                html_file_path,
                                metadata
                            )
                            if chunk:
                                chunks.append(chunk)
                        
                        # Bắt đầu điều luật mới
                        current_dieu = element.get_text(strip=True)
                        current_ghi_chu = None
                        current_noi_dung = []
                    
                    elif 'pGhiChu' in classes:
                        current_ghi_chu = element.get_text(strip=True)
                    
                    elif 'pNoiDung' in classes:
                        noi_dung_text = element.get_text(separator='\n', strip=True)
                        current_noi_dung.append(noi_dung_text)
            
            # Lưu điều luật cuối cùng
            if current_dieu and current_noi_dung:
                chunk = self._create_chunk(
                    current_dieu,
                    current_noi_dung,
                    current_chuong,
                    current_ghi_chu,
                    html_file_path,
                    metadata
                )
                if chunk:
                    chunks.append(chunk)
            
            self.chunks.extend(chunks)
            return chunks
            
        except Exception as e:
            print(f"Lỗi khi chunk file {html_file_path.name}: {e}")
            return []
    
    def _create_chunk(
        self,
        dieu: str,
        noi_dung: List[str],
        chuong: Optional[str],
        ghi_chu: Optional[str],
        file_path: Path,
        metadata: Optional[Dict]
    ) -> Optional[Dict]:
        """Tạo một chunk từ thông tin điều luật"""
        # Kết hợp nội dung
        content_parts = []
        
        if chuong:
            content_parts.append(f"Chương: {chuong}")
        
        content_parts.append(f"Điều: {dieu}")
        
        if ghi_chu:
            content_parts.append(f"Ghi chú: {ghi_chu}")
        
        content_parts.append("Nội dung:")
        content_parts.extend(noi_dung)
        
        full_content = "\n".join(content_parts)
        
        # Nếu nội dung quá dài, có thể chia nhỏ hơn
        if len(full_content) > self.chunk_size:
            # Chia nhỏ nội dung điều luật
            sub_chunks = self._split_long_content(full_content, dieu, chuong, ghi_chu, file_path, metadata)
            return sub_chunks
        
        # Tạo chunk metadata
        chunk_metadata = {
            'file_id': file_path.stem,
            'file_name': file_path.name,
            'chuong': chuong,
            'dieu': dieu,
            'ghi_chu': ghi_chu,
            'content_length': len(full_content)
        }
        
        if metadata:
            chunk_metadata.update(metadata)
        
        return {
            'id': f"{file_path.stem}_{len(self.chunks)}",
            'content': full_content,
            'metadata': chunk_metadata
        }
    
    def _split_long_content(
        self,
        content: str,
        dieu: str,
        chuong: Optional[str],
        ghi_chu: Optional[str],
        file_path: Path,
        metadata: Optional[Dict]
    ) -> List[Dict]:
        """Chia nhỏ nội dung quá dài thành nhiều chunks"""
        chunks = []
        lines = content.split('\n')
        
        current_chunk_lines = []
        current_length = 0
        
        for line in lines:
            line_length = len(line) + 1  # +1 for newline
            
            if current_length + line_length > self.chunk_size and current_chunk_lines:
                # Tạo chunk hiện tại
                chunk_content = '\n'.join(current_chunk_lines)
                chunk_metadata = {
                    'file_id': file_path.stem,
                    'file_name': file_path.name,
                    'chuong': chuong,
                    'dieu': dieu,
                    'ghi_chu': ghi_chu,
                    'content_length': len(chunk_content),
                    'is_partial': True
                }
                if metadata:
                    chunk_metadata.update(metadata)
                
                chunks.append({
                    'id': f"{file_path.stem}_{len(self.chunks) + len(chunks)}",
                    'content': chunk_content,
                    'metadata': chunk_metadata
                })
                
                # Bắt đầu chunk mới với overlap
                overlap_lines = current_chunk_lines[-self.chunk_overlap//50:] if len(current_chunk_lines) > self.chunk_overlap//50 else []
                current_chunk_lines = overlap_lines + [line]
                current_length = sum(len(l) for l in current_chunk_lines)
            else:
                current_chunk_lines.append(line)
                current_length += line_length
        
        # Lưu chunk cuối cùng
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            chunk_metadata = {
                'file_id': file_path.stem,
                'file_name': file_path.name,
                'chuong': chuong,
                'dieu': dieu,
                'ghi_chu': ghi_chu,
                'content_length': len(chunk_content),
                'is_partial': len(chunks) > 0
            }
            if metadata:
                chunk_metadata.update(metadata)
            
            chunks.append({
                'id': f"{file_path.stem}_{len(self.chunks) + len(chunks)}",
                'content': chunk_content,
                'metadata': chunk_metadata
            })
        
        return chunks
    
    def chunk_all_files(
        self,
        input_dir: Path,
        metadata_file: Optional[Path] = None,
        output_file: Path = None
    ) -> Dict:
        """
        Chia nhỏ tất cả các file HTML
        
        Args:
            input_dir: Thư mục chứa file HTML
            metadata_file: File JSON chứa metadata (nếu có)
            output_file: File JSON để lưu chunks
            
        Returns:
            Dictionary chứa thống kê
        """
        # Load metadata nếu có
        metadata_dict = {}
        if metadata_file and metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata_list = json.load(f)
                # Tạo dict với key là file_id
                for meta in metadata_list:
                    file_id = meta.get('file_id')
                    if file_id:
                        if file_id not in metadata_dict:
                            metadata_dict[file_id] = []
                        metadata_dict[file_id].append(meta)
        
        html_files = list(input_dir.glob("*.html"))
        total_chunks = 0
        
        print(f"Bắt đầu chia nhỏ {len(html_files)} file...")
        
        for html_file in html_files:
            file_metadata = metadata_dict.get(html_file.stem, None)
            chunks = self.chunk_html_file(html_file, file_metadata[0] if file_metadata else None)
            total_chunks += len(chunks)
        
        # Lưu chunks vào file JSON
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        
        result = {
            'total_files': len(html_files),
            'total_chunks': len(self.chunks),
            'avg_chunks_per_file': len(self.chunks) / len(html_files) if html_files else 0
        }
        
        print(f"\nHoàn thành chia nhỏ dữ liệu:")
        print(f"  - Tổng số file: {len(html_files)}")
        print(f"  - Tổng số chunks: {len(self.chunks)}")
        print(f"  - Trung bình chunks/file: {result['avg_chunks_per_file']:.1f}")
        
        return result


def main():
    """Hàm main để chạy thử"""
    from pathlib import Path
    
    # Trỏ đến Dataset/demuc từ Data process
    base_path = Path(__file__).parent.parent
    input_dir = base_path / "Dataset" / "demuc"
    metadata_file = Path(__file__).parent / "metadata.json"
    output_file = Path(__file__).parent / "chunks.json"
    
    chunker = DataChunker(chunk_size=1000, chunk_overlap=200)
    result = chunker.chunk_all_files(input_dir, metadata_file, output_file)
    
    return result


if __name__ == "__main__":
    main()

