import fitz
from pdf2image import convert_from_path
from pptx import Presentation
from openpyxl import load_workbook
from docx import Document as DocxDocument
from PIL import Image
import io
import base64
import os
from typing import List, Dict, Any
import re
import unicodedata


def clean_text(text: str) -> str:
    """Clean text: fix encoding issues, normalize unicode, remove control characters"""
    if not text:
        return text
    
    # Normalize unicode (decompose special characters)
    text = unicodedata.normalize('NFKD', text)
    
    # Remove control characters but keep common ones (newline, tab)
    text = ''.join(
        char if unicodedata.category(char)[0] != 'C' or char in '\n\r\t'
        else '' for char in text
    )
    
    # Fix common encoding issues
    replacements = {
        '\xa0': ' ',      # Non-breaking space -> space
        '\u2013': '-',    # En dash -> hyphen
        '\u2014': '-',    # Em dash -> hyphen
        '\u2019': "'",    # Right single quote -> apostrophe
        '\u201c': '"',    # Left double quote -> quote
        '\u201d': '"',    # Right double quote -> quote
        '\u2022': '•',    # Bullet point (keep but normalize)
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Clean up extra whitespace but preserve structure
    lines = []
    for line in text.split('\n'):
        line = line.rstrip()  # Remove trailing whitespace
        if line:
            lines.append(line)
    
    text = '\n'.join(lines)
    return text


def normalize_bullets(text: str) -> str:
    """Normalize bullet points to consistent format"""
    lines = text.split('\n')
    normalized_lines = []
    
    for line in lines:
        stripped = line.lstrip()
        
        # Detect bullet markers
        bullet_patterns = [
            (r'^[\•\-\*\+]\s+', '• '),          # Bullet, dash, asterisk, plus
            (r'^\d+[\.\)]\s+', lambda m: f"{m.group(0)[0]}. "),  # Numbered
            (r'^[a-zA-Z][\.\)]\s+', lambda m: f"{m.group(0)[0]}. "),  # Lettered
        ]
        
        for pattern, replacement in bullet_patterns:
            if re.match(pattern, stripped):
                stripped = re.sub(pattern, replacement, stripped)
                break
        
        # Preserve indentation
        indent = len(line) - len(line.lstrip())
        if indent > 0:
            normalized_lines.append(' ' * indent + stripped)
        else:
            normalized_lines.append(stripped)
    
    return '\n'.join(normalized_lines)


def clean_element_text(text: str) -> str:
    """Full text cleaning pipeline"""
    text = clean_text(text)
    text = normalize_bullets(text)
    return text


def normalize_table(text: str) -> Dict[str, Any]:
    """Convert unstructured table text into normalized column structure with proper JSON rows"""
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    
    if not lines:
        return {"columns": [], "rows": [], "row_count": 0, "column_count": 0}
    
    # Parse rows - split by multiple spaces or tabs
    parsed_rows = []
    for line in lines:
        # Split by multiple spaces (2+) or tabs
        cells = re.split(r'\s{2,}|\t|\|', line)
        # Clean and filter cells
        cells = [cell.strip() for cell in cells if cell.strip()]
        if cells:
            parsed_rows.append(cells)
    
    if not parsed_rows:
        return {"columns": [], "rows": [], "row_count": 0, "column_count": 0}
    
    # Determine number of columns
    max_cols = max(len(row) for row in parsed_rows)
    
    # Detect header row (usually first row or row with non-numeric content)
    header = None
    data_start = 0
    
    if len(parsed_rows) > 1:
        first_row = parsed_rows[0]
        # Check if first row looks like a header
        is_header = any(
            not any(c.isdigit() for c in cell) and len(cell) > 0
            for cell in first_row
        )
        
        if is_header:
            header = first_row + [''] * (max_cols - len(first_row))
            data_start = 1
    
    # Use first row as header if not detected
    if header is None:
        header = [f"Column_{i+1}" for i in range(max_cols)]
        data_start = 0
    
    # Normalize all rows to have same column count
    normalized_rows = []
    for row in parsed_rows[data_start:]:
        # Pad or trim to match column count
        normalized_row = (row + [''] * max_cols)[:max_cols]
        # Convert to dictionary using headers
        row_dict = {
            header[i]: normalized_row[i] 
            for i in range(len(header))
        }
        normalized_rows.append(row_dict)
    
    return {
        "columns": header[:max_cols],
        "rows": normalized_rows,
        "row_count": len(normalized_rows),
        "column_count": len(header),
        "raw_data": {
            "max_columns": max_cols,
            "rows": [
                (row + [''] * max_cols)[:max_cols]
                for row in parsed_rows[data_start:]
            ]
        }
    }


class DocumentProcessor:
    
    @staticmethod
    def pdf_to_images(pdf_path: str) -> List[Image.Image]:
        try:
            images = convert_from_path(pdf_path, dpi=150)
            return images
        except Exception as e:
            raise Exception(f"PDF conversion failed: {str(e)}")
    
    @staticmethod
    def pdf_extract_pages(pdf_path: str) -> List[Dict[str, Any]]:
        pages = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            text = page.get_text()
            
            pages.append({
                "page_number": page_num + 1,
                "image": img,
                "text": text,
                "width": page.rect.width,
                "height": page.rect.height
            })
        
        doc.close()
        return pages
    
    @staticmethod
    def ppt_to_images(ppt_path: str) -> List[Dict[str, Any]]:
        prs = Presentation(ppt_path)
        slides = []
        
        for idx, slide in enumerate(prs.slides):
            text_content = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text_content.append(shape.text)
            
            slides.append({
                "slide_number": idx + 1,
                "text": "\n".join(text_content),
                "shapes_count": len(slide.shapes)
            })
        
        return slides
    
    @staticmethod
    def xlsx_extract_data(xlsx_path: str) -> List[Dict[str, Any]]:
        wb = load_workbook(xlsx_path, data_only=True)
        sheets_data = []
        
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            
            data = []
            for row in ws.iter_rows(values_only=True):
                if any(cell is not None for cell in row):
                    data.append(list(row))
            
            sheets_data.append({
                "sheet_name": sheet_name,
                "data": data,
                "rows": len(data),
                "columns": ws.max_column
            })
        
        wb.close()
        return sheets_data
    
    @staticmethod
    def docx_extract_text(docx_path: str) -> Dict[str, Any]:
        doc = DocxDocument(docx_path)
        
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        
        tables_data = []
        for table in doc.tables:
            table_data = []
            for row in table.rows:
                row_data = [cell.text for cell in row.cells]
                table_data.append(row_data)
            tables_data.append(table_data)
        
        return {
            "paragraphs": paragraphs,
            "tables": tables_data,
            "paragraph_count": len(paragraphs),
            "table_count": len(tables_data)
        }
    
    @staticmethod
    def image_to_base64(image: Image.Image) -> str:
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
