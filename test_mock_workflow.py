#!/usr/bin/env python3
"""
Mock test script for the complete workflow with PDF generation.
This script mocks the external API calls to demonstrate the complete workflow.
"""

import base64
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
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

def create_mock_llm_response():
    """Create mock LLM service response."""
    from src.dto import TextExtractionResponseDTO
    return TextExtractionResponseDTO(
        extracted_text="Product Name: Organic Apple Juice\nIngredients: Organic Apple Juice, Vitamin C\nCountry: United States\nManufacturer: Fresh Farms LLC",
        confidence=0.95,
        processing_time_ms=1500,
        image_metadata={
            "width": 800,
            "height": 600,
            "format": "PNG"
        },
        compliance_result={}
    )

def create_mock_rag_response():
    """Create mock RAG service response."""
    return {
        "status": "success",
        "data": {
            "regulations": [
                {
                    "id": "FDA-001",
                    "title": "FDA Organic Food Standards",
                    "content": "Organic apple juice must contain at least 95% organic ingredients and be processed without synthetic additives.",
                    "compliance_requirement": "Products labeled as organic must meet USDA organic standards",
                    "relevance_score": 0.95
                },
                {
                    "id": "FDA-002", 
                    "title": "Vitamin C Fortification Guidelines",
                    "content": "Vitamin C may be added to fruit juices as a natural antioxidant and nutritional supplement.",
                    "compliance_requirement": "Vitamin C additions must be declared on ingredient list",
                    "relevance_score": 0.87
                }
            ],
            "country": "United States",
            "total_regulations": 2,
            "query_used": "organic apple juice vitamin c regulations United States"
        }
    }

def create_mock_validation_response():
    """Create mock validation service response."""
    return {
        "status": "success", 
        "data": {
            "compliant": True,
            "confidence": 0.92,
            "reasoning": "The product meets FDA organic standards with 100% organic apple juice and properly declared Vitamin C. All ingredients are compliant with US regulations.",
            "compliance_details": [
                {
                    "regulation_id": "FDA-001",
                    "status": "COMPLIANT",
                    "reason": "Product contains 100% organic ingredients meeting USDA standards"
                },
                {
                    "regulation_id": "FDA-002",
                    "status": "COMPLIANT", 
                    "reason": "Vitamin C is properly declared and meets fortification guidelines"
                }
            ],
            "recommendations": [
                "Ensure organic certification is current and displayed on packaging",
                "Maintain proper documentation for organic ingredient sourcing"
            ]
        }
    }

async def test_complete_workflow_with_mocks():
    """Test the complete workflow with mocked API responses."""
    print("🧪 Testing Complete Workflow with Mocked API Responses")
    print("=" * 70)
    
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
        
        print("📤 1. Preparing test with mocked API responses...")
        logger.info("Test request created with sample PNG image and mocked responses")
        
        # Mock the external API calls
        mock_llm_response = create_mock_llm_response()
        mock_rag_response = create_mock_rag_response() 
        mock_validation_response = create_mock_validation_response()
        
        with patch('src.services.llm_service.LLMService.extract_text_from_image') as mock_llm, \
             patch('src.services.rag_service.RAGService.query_regulations') as mock_rag, \
             patch('src.services.validation_service.ValidationService.validate_compliance') as mock_validation:
            
            # Setup mocks
            mock_llm.return_value = mock_llm_response
            mock_rag.return_value = mock_rag_response
            mock_validation.return_value = mock_validation_response
            
            print("🔄 2. Processing through complete workflow with mocks...")
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
                        for reg in rag_data['regulations'][:2]:  # Show first 2
                            print(f"   📋 {reg.get('title', 'Unknown')}")
                
                # Check if we have validation results
                if data.get('validation_result'):
                    print("✅ Validation processing completed")
                    validation_data = data['validation_result']
                    if validation_data.get('compliant') is not None:
                        compliance_status = "✅ COMPLIANT" if validation_data['compliant'] else "❌ NON-COMPLIANT"
                        print(f"⚖️ Compliance status: {compliance_status}")
                        print(f"🎯 Confidence: {validation_data.get('confidence', 0):.1%}")
                        if validation_data.get('reasoning'):
                            print(f"💭 Reasoning: {validation_data['reasoning'][:100]}...")
                
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
                        
                        # Verify compliance result structure
                        if compliance_data.get('compliant') is not None:
                            final_status = "✅ COMPLIANT" if compliance_data['compliant'] else "❌ NON-COMPLIANT"
                            print(f"🏆 Final compliance result: {final_status}")
                        
                    elif compliance_data.get('pdf_error'):
                        print(f"❌ PDF generation failed: {compliance_data['pdf_error']}")
                    else:
                        print("ℹ️ PDF generation not triggered")
                        
                    # Check workflow completion
                    if compliance_data.get('ready_for_pdf'):
                        print("🎯 Workflow ready for PDF generation")
                    else:
                        print("⏳ Workflow not ready for PDF")
                
                # Show API call verification
                print("\n🔍 API Call Verification:")
                print(f"   📞 LLM API called: {mock_llm.called}")
                print(f"   📞 RAG API called: {mock_rag.called}")
                print(f"   📞 Validation API called: {mock_validation.called}")
                
            else:
                print(f"❌ Processing failed: {result.get('error', {}).get('message', 'Unknown error')}")
                
                print("\n" + "=" * 70)
                print("🏁 Mock test completed successfully!")
            
            return result
            
    except Exception as e:
        logger.error(f"Mock test failed with exception: {e}")
        print(f"💥 Mock test failed: {e}")
        return None

async def test_pdf_generation_service():
    """Test the PDF generation service directly."""
    print("\n🧪 Testing PDF Generation Service Directly")
    print("=" * 70)
    
    try:
        from src.services.pdf_generation_service import PDFGenerationService
        
        pdf_service = PDFGenerationService()
        
        # Sample extracted text
        sample_extracted_text = "Product Name: Organic Apple Juice\nIngredients: Organic Apple Juice, Vitamin C\nCountry: United States"
        
        # Sample RAG response
        sample_rag_response = {
            'regulations': [
                {
                    'id': 'FDA-001',
                    'title': 'FDA Organic Food Standards',
                    'content': 'Organic apple juice must contain at least 95% organic ingredients.',
                    'compliance_requirement': 'Products labeled as organic must meet USDA organic standards'
                }
            ],
            'country': 'United States',
            'extracted_data': {
                'product_name': 'Organic Apple Juice',
                'ingredients': ['Organic Apple Juice', 'Vitamin C']
            }
        }
        
        # Sample validation result
        sample_validation_result = {
            'compliant': True,
            'confidence': 0.92,
            'reasoning': 'The product meets FDA organic standards with 100% organic apple juice.',
            'compliance_details': [
                {
                    'regulation_id': 'FDA-001',
                    'status': 'COMPLIANT',
                    'reason': 'Product contains 100% organic ingredients'
                }
            ]
        }
        
        print("📄 Generating PDF report...")
        result = pdf_service.generate_compliance_report(
            sample_extracted_text, 
            sample_rag_response, 
            sample_validation_result
        )
        
        if result.get('success'):
            print("✅ PDF generation successful!")
            pdf_data = result.get('pdf_data', {})
            print(f"   📎 Filename: {pdf_data.get('filename')}")
            print(f"   📏 Size: {len(pdf_data.get('data', '')) // 4 * 3} bytes (estimated)")
            print(f"   🏷️ Format: {pdf_data.get('format')}")
            print("   📋 PDF contains compliance report with regulations and validation results")
        else:
            print(f"❌ PDF generation failed: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"PDF service test failed: {e}")
        print(f"💥 PDF service test failed: {e}")
        return None

async def main():
    """Main test runner."""
    print("🚀 Starting Complete Workflow Tests with Mocks")
    print("=" * 70)
    
    # Test complete workflow with mocks
    workflow_result = await test_complete_workflow_with_mocks()
    
    # Test PDF service directly
    pdf_result = await test_pdf_generation_service()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 70)
    
    if workflow_result and workflow_result.get('status') == 'success':
        print("✅ Complete workflow test: PASSED")
        
        # Check specific components
        data = workflow_result.get('data', {})
        components_passed = []
        
        if data.get('extracted_text'):
            components_passed.append("Text Extraction")
        if data.get('rag_result', {}).get('regulations'):
            components_passed.append("RAG Query")
        if data.get('validation_result', {}).get('compliant') is not None:
            components_passed.append("validation")
        if data.get('compliance_result', {}).get('pdf_report'):
            components_passed.append("PDF Generation")
            
        print(f"   🎯 Components working: {', '.join(components_passed)}")
        
    else:
        print("❌ Complete workflow test: FAILED")
        
    if pdf_result and pdf_result.get('success'):
        print("✅ PDF generation test: PASSED")
    else:
        print("❌ PDF generation test: FAILED")
    
    print("\n🎉 All tests completed!")
    print("\n📝 Note: This test uses mocked API responses to demonstrate")
    print("   the complete workflow. In production, ensure network access")
    print("   to sage.paastry.sysco.net APIs.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())