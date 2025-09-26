"""
PDF generation service for creating compliance reports.
"""

import logging
import base64
from datetime import datetime
from typing import Dict, Any, Optional
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)


class PDFGenerationService:
    """Service for generating PDF compliance reports."""
    
    def __init__(self):
        """Initialize PDF generation service."""
        logger.info("PDF Generation Service initialized")
    
    def generate_compliance_report(self, 
                                 extracted_text: str,
                                 rag_response: Dict[str, Any],
                                 validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive compliance PDF report.
        
        Args:
            extracted_text: Original text extracted from image
            rag_response: RAG agent response with regulations
            validation_result: Validation agent results
            
        Returns:
            Dictionary with PDF data and metadata
        """
        try:
            logger.info("📋 PDF GENERATION: Starting compliance report generation")
            
            # Create PDF buffer
            buffer = BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Build content
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
                textColor=colors.darkblue,
                alignment=1  # Center alignment
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.darkblue
            )
            
            # Extract compliance data
            compliance_data = validation_result.get('validation_result', {}).get('compliance', {})
            issues_data = validation_result.get('validation_result', {}).get('issues', {})
            evidence_data = validation_result.get('validation_result', {}).get('evidence', {})
            notes = validation_result.get('validation_result', {}).get('notes', '')
            
            is_compliant = compliance_data.get('is_compliant', False)
            coverage_percent = compliance_data.get('coverage_percent', 0)
            
            # Title
            story.append(Paragraph("Food Export Compliance Report", title_style))
            story.append(Spacer(1, 20))
            
            # Report metadata
            report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            story.append(Paragraph(f"<b>Report Generated:</b> {report_date}", styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Compliance Status
            compliance_color = colors.green if is_compliant else colors.red
            compliance_text = "COMPLIANT" if is_compliant else "NON-COMPLIANT"
            
            compliance_style = ParagraphStyle(
                'ComplianceStatus',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=compliance_color,
                alignment=1,
                spaceAfter=20
            )
            
            story.append(Paragraph(f"<b>COMPLIANCE STATUS: {compliance_text}</b>", compliance_style))
            story.append(Paragraph(f"<b>Coverage: {coverage_percent}%</b>", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Product Information
            story.append(Paragraph("Product Information", heading_style))
            
            # Extract product info from extracted text
            product_info = self._extract_product_summary(extracted_text)
            
            product_data = [
                ['Product Name', product_info.get('product_name', 'Not specified')],
                ['Destination', product_info.get('destination', 'Not specified')],
                ['Ingredients', product_info.get('ingredients', 'Not specified')],
                ['Net Weight', product_info.get('weight', 'Not specified')],
                ['Manufacturer', product_info.get('manufacturer', 'Not specified')]
            ]
            
            product_table = Table(product_data, colWidths=[2*inch, 4*inch])
            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(product_table)
            story.append(Spacer(1, 20))
            
            # Compliance Summary
            story.append(Paragraph("Compliance Summary", heading_style))
            
            summary_data = [
                ['Total Requirements', str(compliance_data.get('total_required', 0))],
                ['Requirements Met', str(compliance_data.get('matched_count', 0))],
                ['Partial Matches', str(compliance_data.get('partial_count', 0))],
                ['Coverage Percentage', f"{coverage_percent}%"],
                ['Overall Status', compliance_text]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Issues and Recommendations
            if issues_data.get('missing_items') or issues_data.get('partial_matches') or issues_data.get('conflicts'):
                story.append(Paragraph("Issues and Recommendations", heading_style))
                
                # Missing items
                if issues_data.get('missing_items'):
                    story.append(Paragraph("<b>Missing Requirements:</b>", styles['Normal']))
                    for item in issues_data['missing_items']:
                        story.append(Paragraph(f"• {item.get('key', 'N/A')}: {item.get('requirement_text', 'N/A')}", styles['Normal']))
                    story.append(Spacer(1, 10))
                
                # Partial matches
                if issues_data.get('partial_matches'):
                    story.append(Paragraph("<b>Partial Matches (Need Correction):</b>", styles['Normal']))
                    for item in issues_data['partial_matches']:
                        story.append(Paragraph(f"• {item.get('key', 'N/A')}: {item.get('requirement_text', 'N/A')}", styles['Normal']))
                        story.append(Paragraph(f"  Current: {item.get('observed', 'N/A')}", styles['Normal']))
                    story.append(Spacer(1, 10))
                
                # Conflicts
                if issues_data.get('conflicts'):
                    story.append(Paragraph("<b>Conflicts (Must Fix):</b>", styles['Normal']))
                    for conflict in issues_data['conflicts']:
                        story.append(Paragraph(f"• {conflict.get('type', 'N/A')}: {conflict.get('detail', 'N/A')}", styles['Normal']))
                        story.append(Paragraph(f"  Found: {conflict.get('observed', 'N/A')}", styles['Normal']))
                    story.append(Spacer(1, 10))
            
            # Evidence Found
            if evidence_data:
                story.append(Paragraph("Evidence Found on Label", heading_style))
                evidence_items = []
                for key, value in evidence_data.items():
                    if value and str(value).strip() not in ['None', 'null', '']:
                        evidence_items.append([key.replace('_', ' ').title(), str(value)])
                
                if evidence_items:
                    evidence_table = Table(evidence_items, colWidths=[2*inch, 4*inch])
                    evidence_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    story.append(evidence_table)
                    story.append(Spacer(1, 20))
            
            # Notes
            if notes:
                story.append(Paragraph("Analysis Notes", heading_style))
                story.append(Paragraph(notes, styles['Normal']))
                story.append(Spacer(1, 20))
            
            # Regulations Reference
            rag_answer = rag_response.get('answer', 'No regulations retrieved')
            story.append(Paragraph("Applicable Regulations", heading_style))
            story.append(Paragraph(rag_answer, styles['Normal']))
            story.append(Spacer(1, 10))
            
            # References
            sources = rag_response.get('sources', [])
            if sources:
                story.append(Paragraph("<b>References:</b>", styles['Normal']))
                for source in sources:
                    story.append(Paragraph(f"• {source}", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF data
            buffer.seek(0)
            pdf_data = buffer.getvalue()
            buffer.close()
            
            # Encode to base64 for frontend
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            logger.info("✅ PDF GENERATION: Compliance report generated successfully")
            logger.info(f"📊 PDF size: {len(pdf_data)} bytes")
            
            return {
                "success": True,
                "pdf_base64": pdf_base64,
                "pdf_size": len(pdf_data),
                "filename": f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "compliance_status": is_compliant,
                "coverage_percent": coverage_percent,
                "generated_at": report_date
            }
            
        except Exception as e:
            logger.error(f"💥 PDF generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_product_summary(self, extracted_text: str) -> Dict[str, str]:
        """Extract key product information from extracted text for PDF."""
        import re
        
        info = {
            'product_name': '',
            'destination': '',
            'ingredients': '',
            'weight': '',
            'manufacturer': ''
        }
        
        try:
            # Product name
            product_patterns = [
                r'Product\s*(?:Name)?:\s*([^\n\r]+)',
                r'Product:\s*([^\n\r]+)',
                r'Name:\s*([^\n\r]+)',
            ]
            
            for pattern in product_patterns:
                match = re.search(pattern, extracted_text, re.IGNORECASE)
                if match:
                    info['product_name'] = match.group(1).strip()
                    break
            
            # Destination
            dest_patterns = [
                r'Destination\s*(?:Country)?:\s*([^\n\r]+)',
                r'Export\s*(?:to|Country):\s*([^\n\r]+)',
                r'Country:\s*([^\n\r]+)',
            ]
            
            for pattern in dest_patterns:
                match = re.search(pattern, extracted_text, re.IGNORECASE)
                if match:
                    info['destination'] = match.group(1).strip()
                    break
            
            # Ingredients
            ingredients_match = re.search(r'Ingredients?:\s*([^\n\r]+(?:\n\s*[-•]\s*[^\n\r]+)*)', extracted_text, re.IGNORECASE)
            if ingredients_match:
                info['ingredients'] = ingredients_match.group(1).strip()
            
            # Weight
            weight_patterns = [
                r'Net\s*(?:Weight|Quantity)?:\s*([^\n\r]+)',
                r'Weight:\s*([^\n\r]+)',
                r'(\d+\s*(?:oz|g|kg|lb|lbs))',
            ]
            
            for pattern in weight_patterns:
                match = re.search(pattern, extracted_text, re.IGNORECASE)
                if match:
                    info['weight'] = match.group(1).strip()
                    break
            
            # Manufacturer
            manufacturer_patterns = [
                r'Manufacturer:\s*([^\n\r]+)',
                r'Manufactured\s*by:\s*([^\n\r]+)',
                r'Made\s*by:\s*([^\n\r]+)',
            ]
            
            for pattern in manufacturer_patterns:
                match = re.search(pattern, extracted_text, re.IGNORECASE)
                if match:
                    info['manufacturer'] = match.group(1).strip()
                    break
            
        except Exception as e:
            logger.warning(f"Error extracting product summary: {e}")
        
        return info