#!/usr/bin/env python3
"""
Test script for the complete workflow with PDF generation.
This script simulates the complete workflow from image upload to PDF generation.
"""

import base64
import json
import logging
from src.app import Application

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_sample_base64_image():
    """Create a sample base64 encoded image for testing."""
    # Simple 1x1 pixel PNG image in base64
    sample_png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13'
        b'\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc```'
        b'\x00\x00\x00\x04\x00\x01\xdd\xcc\xdb\x1a\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return base64.b64encode(sample_png).decode('utf-8')

async def test_complete_workflow():
    """Test the complete workflow from image upload to PDF generation."""
    print("🧪 Testing Complete Workflow with PDF Generation")
    print("=" * 60)
    
    try:
        # Initialize application
        app = Application()
        image_controller = app.container.get_controller('image')
        
        # Create test data
        sample_image = create_sample_base64_image()
        
        test_request = {
            'encoded_image': sample_image,
            'media_type': 'image/png'
        }
        
        print("📤 1. Sending test image for processing...")
        logger.info("Test request created with sample PNG image")
        
        # Process the image through the complete workflow
        print("🔄 2. Processing through complete workflow...")
        result = await image_controller.extract_text(test_request)
        
        print("📋 3. Analyzing results...")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'success':
            data = result.get('data', {})
            print("✅ Image processing successful!")
            
            # Check if we have extracted text
            if data.get('extracted_text'):
                print(f"📝 Extracted text: {data['extracted_text'][:100]}...")
            
            # Check if we have RAG results
            if data.get('rag_result'):
                print("🤖 RAG processing completed")
                rag_data = data['rag_result']
                if rag_data.get('regulations'):
                    print(f"📚 Found {len(rag_data['regulations'])} regulations")
            
            # Check if we have validation results
            if data.get('validation_result'):
                print("✅ Validation processing completed")
                validation_data = data['validation_result']
                if validation_data.get('compliant') is not None:
                    print(f"⚖️ Compliance status: {validation_data['compliant']}")
            
            # Check if we have compliance result
            if data.get('compliance_result'):
                print("📊 Compliance analysis completed")
                compliance_data = data['compliance_result']
                
                # Check for PDF generation
                if compliance_data.get('pdf_report'):
                    print("📄 PDF report generated successfully!")
                    pdf_data = compliance_data['pdf_report']
                    print(f"   📎 Filename: {pdf_data.get('filename', 'unknown')}")
                    print(f"   📏 Size: {len(pdf_data.get('data', '')) // 4 * 3} bytes (estimated)")
                    print(f"   🏷️ Format: {pdf_data.get('format', 'unknown')}")
                elif compliance_data.get('pdf_error'):
                    print(f"❌ PDF generation failed: {compliance_data['pdf_error']}")
                else:
                    print("ℹ️ PDF generation not triggered (validation may have failed)")
                    
                # Check workflow completion
                if compliance_data.get('ready_for_pdf'):
                    print("🎯 Workflow ready for PDF generation")
                else:
                    print("⏳ Workflow not ready for PDF (may need validation success)")
            
        else:
            print(f"❌ Processing failed: {result.get('error', {}).get('message', 'Unknown error')}")
            
        print("\n" + "=" * 60)
        print("🏁 Test completed!")
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        print(f"💥 Test failed: {e}")
        return None

def test_pdf_generation_service():
    """Test the PDF generation service directly."""
    print("\n🧪 Testing PDF Generation Service Directly")
    print("=" * 60)
    
    try:
        from src.services.pdf_generation_service import PDFGenerationService
        
        pdf_service = PDFGenerationService()
        
        # Sample RAG response
        sample_rag_response = {
            'regulations': [
                {
                    'title': 'Sample Regulation',
                    'content': 'This is a sample regulation for testing.',
                    'compliance_status': 'COMPLIANT'
                }
            ],
            'country': 'US',
            'extracted_data': {
                'product_name': 'Test Product',
                'ingredients': ['Test Ingredient 1', 'Test Ingredient 2']
            }
        }
        
        # Sample validation result
        sample_validation_result = {
            'compliant': True,
            'confidence': 0.95,
            'reasoning': 'All ingredients comply with regulations.'
        }
        
        # Sample extracted text
        sample_extracted_text = "Test Product\nIngredients: Test Ingredient 1, Test Ingredient 2\nCountry: US"
        
        print("📄 Generating PDF report...")
        result = pdf_service.generate_compliance_report(sample_extracted_text, sample_rag_response, sample_validation_result)
        
        if result.get('success'):
            print("✅ PDF generation successful!")
            pdf_data = result.get('pdf_data', {})
            print(f"   📎 Filename: {pdf_data.get('filename')}")
            print(f"   📏 Size: {len(pdf_data.get('data', '')) // 4 * 3} bytes (estimated)")
            print(f"   🏷️ Format: {pdf_data.get('format')}")
        else:
            print(f"❌ PDF generation failed: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"PDF service test failed: {e}")
        print(f"💥 PDF service test failed: {e}")
        return None

async def main():
    """Main test runner."""
    print("🚀 Starting Complete Workflow Tests")
    print("=" * 60)
    
    # Test complete workflow
    workflow_result = await test_complete_workflow()
    
    # Test PDF service directly
    pdf_result = test_pdf_generation_service()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)
    
    if workflow_result and workflow_result.get('status') == 'success':
        print("✅ Complete workflow test: PASSED")
    else:
        print("❌ Complete workflow test: FAILED")
        
    if pdf_result and pdf_result.get('success'):
        print("✅ PDF generation test: PASSED")
    else:
        print("❌ PDF generation test: FAILED")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())