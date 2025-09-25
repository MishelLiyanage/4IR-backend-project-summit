"""
Simple test script for image processing functionality without pytest dependency.
Run this script to test basic functionality.
"""

import asyncio
import base64
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

from src.controllers.image_controller import ImageController
from src.services.llm_service import LLMService
from src.constants import AppConfig
from src.dto import ImageUploadRequestDTO


def create_sample_image():
    """Create a small sample JPEG image in base64."""
    # Small 1x1 JPEG image
    jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    return base64.b64encode(jpeg_data).decode('utf-8')


def test_dto_creation():
    """Test DTO creation and serialization."""
    print("Testing DTO creation...")
    
    sample_image = create_sample_image()
    data = {
        'encoded_image': sample_image,
        'media_type': 'image/jpeg'
    }
    
    # Test ImageUploadRequestDTO
    dto = ImageUploadRequestDTO.from_dict(data)
    assert dto.encoded_image == sample_image
    assert dto.media_type == 'image/jpeg'
    
    # Test serialization
    serialized = dto.to_dict()
    assert serialized['encoded_image'] == sample_image
    assert serialized['media_type'] == 'image/jpeg'
    
    print("✅ DTO creation test passed")


def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    
    # Test AppConfig LLM configuration
    config = AppConfig()
    llm_config = config.get_llm_config()
    
    assert 'api_url' in llm_config
    assert 'ai_agent_id' in llm_config
    assert 'configuration_environment' in llm_config
    
    print("✅ Configuration test passed")


async def test_controller_validation():
    """Test controller input validation."""
    print("Testing controller validation...")
    
    # Mock config and service
    mock_config = MagicMock(spec=AppConfig)
    mock_config.get_llm_config.return_value = {
        'api_url': 'https://test.com',
        'ai_agent_id': 'test-id',
        'user_agent': 'test/1.0',
        'timeout': 30,
        'max_retries': 3,
        'configuration_environment': 'TEST'
    }
    
    llm_service = LLMService(mock_config)
    controller = ImageController(llm_service)
    
    # Test missing image data
    response = await controller.extract_text({})
    assert response['status'] == 'error'
    assert response['status_code'] == 400
    assert 'encoded_image' in response['error']['message']
    
    print("✅ Controller validation test passed")


async def test_health_check():
    """Test health check endpoint."""
    print("Testing health check...")
    
    mock_config = MagicMock(spec=AppConfig)
    mock_config.get_llm_config.return_value = {
        'api_url': 'https://test.com',
        'ai_agent_id': 'test-id',
        'user_agent': 'test/1.0',
        'timeout': 30,
        'max_retries': 3,
        'configuration_environment': 'TEST'
    }
    
    llm_service = LLMService(mock_config)
    controller = ImageController(llm_service)
    
    response = await controller.health_check()
    assert response['status'] == 'success'
    assert response['status_code'] == 200
    assert 'service' in response['data']
    assert response['data']['service'] == 'image-processing'
    
    print("✅ Health check test passed")


async def test_mocked_text_extraction():
    """Test text extraction with mocked LLM service."""
    print("Testing mocked text extraction...")
    
    mock_config = MagicMock(spec=AppConfig)
    mock_config.get_llm_config.return_value = {
        'api_url': 'https://test.com',
        'ai_agent_id': 'test-id',
        'user_agent': 'test/1.0',
        'timeout': 30,
        'max_retries': 3,
        'configuration_environment': 'TEST'
    }
    
    llm_service = LLMService(mock_config)
    controller = ImageController(llm_service)
    
    # Mock successful extraction
    with patch.object(llm_service, 'extract_text_from_image') as mock_extract:
        from src.dto import TextExtractionResponseDTO
        mock_extract.return_value = TextExtractionResponseDTO(
            extracted_text="Sample extracted text",
            processing_time_ms=1000
        )
        
        request_data = {
            'encoded_image': create_sample_image(),
            'media_type': 'image/jpeg'
        }
        
        response = await controller.extract_text(request_data)
        
        assert response['status'] == 'success'
        assert response['status_code'] == 200
        assert response['data']['extracted_text'] == 'Sample extracted text'
    
    print("✅ Mocked text extraction test passed")


async def run_all_tests():
    """Run all tests."""
    print("Running image processing tests...\n")
    
    try:
        test_dto_creation()
        test_config()
        await test_controller_validation()
        await test_health_check()
        await test_mocked_text_extraction()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())