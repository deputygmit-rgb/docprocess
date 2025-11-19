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
