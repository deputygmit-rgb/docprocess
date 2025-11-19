from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

def create_test_pdf():
    os.makedirs("uploads", exist_ok=True)
    filename = "uploads/test_document.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30
    )
    
    title = Paragraph("Quarterly Business Report - Q1 2024", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))
    
    intro_text = """
    This report provides a comprehensive overview of our business performance 
    during the first quarter of 2024. We have seen significant growth across 
    multiple key metrics including revenue, customer acquisition, and market expansion.
    """
    story.append(Paragraph(intro_text, styles['BodyText']))
    story.append(Spacer(1, 0.3 * inch))
    
    section_title = Paragraph("Financial Performance", styles['Heading2'])
    story.append(section_title)
    story.append(Spacer(1, 0.1 * inch))
    
    data = [
        ['Metric', 'Q1 2023', 'Q1 2024', 'Growth %'],
        ['Revenue', '$2.5M', '$3.1M', '25%'],
        ['Net Profit', '$450K', '$620K', '38%'],
        ['Customers', '1,200', '1,650', '37%'],
        ['Market Share', '12%', '15%', '25%']
    ]
    
    table = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))
    
    analysis_text = """
    <b>Key Highlights:</b><br/>
    • Revenue grew by 25% year-over-year, driven by strong customer acquisition<br/>
    • Net profit margins improved significantly due to operational efficiency<br/>
    • Market share expanded by 3 percentage points in our core markets<br/>
    • Customer base increased by 37%, with high retention rates
    """
    story.append(Paragraph(analysis_text, styles['BodyText']))
    story.append(Spacer(1, 0.3 * inch))
    
    section_title2 = Paragraph("Strategic Initiatives", styles['Heading2'])
    story.append(section_title2)
    story.append(Spacer(1, 0.1 * inch))
    
    initiatives_text = """
    In Q1 2024, we launched three major strategic initiatives:<br/><br/>
    
    <b>1. Product Innovation:</b> Introduced AI-powered features that increased 
    user engagement by 40%.<br/><br/>
    
    <b>2. Market Expansion:</b> Successfully entered two new geographical markets, 
    contributing to 15% of total revenue.<br/><br/>
    
    <b>3. Customer Success Program:</b> Implemented a dedicated customer success 
    team, resulting in 92% customer satisfaction scores.
    """
    story.append(Paragraph(initiatives_text, styles['BodyText']))
    
    doc.build(story)
    print(f"Test PDF created: {filename}")
    return filename

if __name__ == "__main__":
    try:
        create_test_pdf()
    except ImportError:
        print("reportlab not installed. Creating simple test PDF with PyMuPDF instead...")
        import fitz
        
        os.makedirs("uploads", exist_ok=True)
        filename = "uploads/test_document.pdf"
        
        doc = fitz.open()
        page = doc.new_page()
        
        text = """Quarterly Business Report - Q1 2024

This is a test document for the document processing pipeline.

Financial Performance:
- Revenue: $3.1M (up 25%)
- Net Profit: $620K (up 38%)
- Customers: 1,650 (up 37%)

Key Highlights:
• Strong revenue growth driven by customer acquisition
• Improved profit margins from operational efficiency
• Market share expansion in core markets
• High customer retention rates"""
        
        page.insert_text((72, 72), text, fontsize=11)
        doc.save(filename)
        doc.close()
        print(f"Simple test PDF created: {filename}")
