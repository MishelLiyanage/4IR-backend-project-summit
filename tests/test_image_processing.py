"""
Tests for image processing functionality.
"""

import pytest
import base64
import json
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.controllers.image_controller import ImageController
from src.services.llm_service import LLMService
from src.constants import AppConfig
from src.dto import ImageUploadRequestDTO, TextExtractionResponseDTO, LLMResponseDTO
from src.exceptions import (
    Base64ValidationError, ImageSizeError, UnsupportedImageTypeError,
    LLMServiceError, LLMServiceTimeoutError, TextExtractionError
)


class TestImageProcessing:
    """Test cases for image processing functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock(spec=AppConfig)
        config.get_llm_config.return_value = {
            'api_url': 'https://test-llm-api.com/extract',
            'ai_agent_id': 'test-agent-id',
            'user_agent': 'test-agent/1.0',
            'timeout': 30,
            'max_retries': 3,
            'configuration_environment': 'TEST'
        }
        return config
    
    @pytest.fixture
    def llm_service(self, mock_config):
        """Create LLM service fixture."""
        return LLMService(mock_config)
    
    @pytest.fixture
    def image_controller(self, llm_service):
        """Create image controller fixture."""
        return ImageController(llm_service)
    
    @pytest.fixture
    def sample_base64_image(self):
        """Create sample base64 image data."""
        # Small 1x1 JPEG image
        jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        return base64.b64encode(jpeg_data).decode('utf-8')
    
    @pytest.fixture
    def sample_request_data(self, sample_base64_image):
        """Create sample request data."""
        return {
            'encoded_image': sample_base64_image,
            'media_type': 'image/jpeg'
        }
    
    # DTO Tests
    def test_image_upload_request_dto_creation(self, sample_base64_image):
        """Test ImageUploadRequestDTO creation."""
        data = {
            'encoded_image': sample_base64_image,
            'media_type': 'image/jpeg'
        }
        
        dto = ImageUploadRequestDTO.from_dict(data)
        
        assert dto.encoded_image == sample_base64_image
        assert dto.media_type == 'image/jpeg'
        
        dict_output = dto.to_dict()
        assert dict_output['encoded_image'] == sample_base64_image
        assert dict_output['media_type'] == 'image/jpeg'
    
    def test_text_extraction_response_dto(self):
        """Test TextExtractionResponseDTO."""
        data = {
            'extracted_text': 'Sample extracted text',
            'confidence': 0.95,
            'processing_time_ms': 1500
        }
        
        dto = TextExtractionResponseDTO.from_dict(data)
        
        assert dto.extracted_text == 'Sample extracted text'
        assert dto.confidence == 0.95
        assert dto.processing_time_ms == 1500
    
    # Validation Tests
    def test_base64_validation_error(self, llm_service):
        """Test base64 validation error."""
        invalid_request = ImageUploadRequestDTO(
            encoded_image="invalid_base64_data",
            media_type="image/jpeg"
        )
        
        with pytest.raises(Base64ValidationError):
            llm_service._validate_image_data(invalid_request)
    
    def test_empty_image_validation(self, llm_service):
        """Test empty image validation."""
        empty_request = ImageUploadRequestDTO(
            encoded_image="",
            media_type="image/jpeg"
        )
        
        with pytest.raises(Base64ValidationError):
            llm_service._validate_image_data(empty_request)
    
    @patch('src.services.llm_service.imghdr.what')
    def test_unsupported_image_type(self, mock_imghdr, llm_service, sample_base64_image):
        """Test unsupported image type validation."""
        mock_imghdr.return_value = 'bmp'  # Unsupported type
        
        request = ImageUploadRequestDTO(
            encoded_image=sample_base64_image,
            media_type="image/bmp"
        )
        
        with pytest.raises(UnsupportedImageTypeError):
            llm_service._validate_image_data(request)
    
    # LLM Service Tests
    @patch('src.services.llm_service.requests.Session.post')
    @pytest.mark.asyncio
    async def test_successful_llm_call(self, mock_post, llm_service, sample_request_data):
        """Test successful LLM service call."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {
                'text': 'Extracted text from image'
            }
        }
        mock_post.return_value = mock_response
        
        request_dto = ImageUploadRequestDTO.from_dict(sample_request_data)
        
        with patch.object(llm_service, '_validate_image_data'):
            result = await llm_service.extract_text_from_image(request_dto)
        
        assert isinstance(result, TextExtractionResponseDTO)
        assert result.extracted_text == 'Extracted text from image'
        assert result.processing_time_ms is not None
    
    @patch('src.services.llm_service.requests.Session.post')
    @pytest.mark.asyncio
    async def test_llm_service_timeout(self, mock_post, llm_service, sample_request_data):
        """Test LLM service timeout handling."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        request_dto = ImageUploadRequestDTO.from_dict(sample_request_data)
        
        with patch.object(llm_service, '_validate_image_data'):
            with pytest.raises(LLMServiceTimeoutError):
                await llm_service.extract_text_from_image(request_dto)
    
    @patch('src.services.llm_service.requests.Session.post')
    @pytest.mark.asyncio
    async def test_llm_service_error_response(self, mock_post, llm_service, sample_request_data):
        """Test LLM service error response handling."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.json.return_value = {
            'error': 'Internal server error'
        }
        mock_post.return_value = mock_response
        
        request_dto = ImageUploadRequestDTO.from_dict(sample_request_data)
        
        with patch.object(llm_service, '_validate_image_data'):
            with pytest.raises(LLMServiceError):
                await llm_service.extract_text_from_image(request_dto)
    
    # Controller Tests
    @pytest.mark.asyncio
    async def test_extract_text_success(self, image_controller, sample_request_data):
        """Test successful text extraction through controller."""
        mock_result = TextExtractionResponseDTO(
            extracted_text="Sample text",
            processing_time_ms=1000
        )
        
        with patch.object(image_controller._llm_service, 'extract_text_from_image', return_value=mock_result):
            response = await image_controller.extract_text(sample_request_data)
        
        assert response['status'] == 'success'
        assert response['status_code'] == 200
        assert response['data']['extracted_text'] == 'Sample text'
    
    @pytest.mark.asyncio
    async def test_extract_text_missing_image(self, image_controller):
        """Test text extraction with missing image data."""
        request_data = {}  # Missing encoded_image
        
        response = await image_controller.extract_text(request_data)
        
        assert response['status'] == 'error'
        assert response['status_code'] == 400
        assert 'encoded_image' in response['error']['message']
    
    @pytest.mark.asyncio
    async def test_extract_text_validation_error(self, image_controller):
        """Test text extraction with validation error."""
        request_data = {
            'encoded_image': 'invalid_base64'
        }
        
        # Mock the service to raise validation error
        with patch.object(image_controller._llm_service, 'extract_text_from_image', 
                         side_effect=Base64ValidationError("Invalid base64")):
            response = await image_controller.extract_text(request_data)
        
        assert response['status'] == 'error'
        assert response['status_code'] == 400
    
    @pytest.mark.asyncio
    async def test_extract_text_llm_service_error(self, image_controller, sample_request_data):
        """Test text extraction with LLM service error."""
        # Mock the service to raise LLM error
        with patch.object(image_controller._llm_service, 'extract_text_from_image',
                         side_effect=LLMServiceError("Service unavailable", 503)):
            response = await image_controller.extract_text(sample_request_data)
        
        assert response['status'] == 'error'
        assert response['status_code'] == 503
    
    @pytest.mark.asyncio
    async def test_health_check(self, image_controller):
        """Test health check endpoint."""
        with patch.object(image_controller._llm_service, 'get_service_health',
                         return_value={'status': 'healthy'}):
            response = await image_controller.health_check()
        
        assert response['status'] == 'success'
        assert response['status_code'] == 200
        assert response['data']['service'] == 'image-processing'
    
    # Integration Tests
    @pytest.mark.asyncio
    async def test_end_to_end_text_extraction(self, sample_base64_image):
        """Test end-to-end text extraction flow."""
        # This would be an integration test with actual LLM service
        # For now, we'll mock the external service
        
        config = MagicMock(spec=AppConfig)
        config.get_llm_config.return_value = {
            'api_url': 'https://test-api.com',
            'ai_agent_id': 'test-agent',
            'user_agent': 'test/1.0',
            'timeout': 30,
            'max_retries': 3,
            'configuration_environment': 'TEST'
        }
        
        llm_service = LLMService(config)
        controller = ImageController(llm_service)
        
        request_data = {
            'encoded_image': sample_base64_image,
            'media_type': 'image/jpeg'
        }
        
        # Mock the HTTP call
        with patch('src.services.llm_service.requests.Session.post') as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'status': 'success',
                'data': {'text': 'Test extracted text'}
            }
            mock_post.return_value = mock_response
            
            response = await controller.extract_text(request_data)
        
        assert response['status'] == 'success'
        assert 'extracted_text' in response['data']
    
    def test_llm_request_preparation(self, llm_service, sample_request_data):
        """Test LLM request preparation."""
        request_dto = ImageUploadRequestDTO.from_dict(sample_request_data)
        llm_request = llm_service._prepare_llm_request(request_dto)
        
        assert llm_request.ai_agent_id == 'test-agent-id'
        assert llm_request.user_query == "Extract the text in the image"
        assert llm_request.configuration_environment == 'TEST'
        assert len(llm_request.media_data) == 1
        assert llm_request.media_data[0].media_type == 'image/jpeg'
    
    def test_text_extraction_from_various_response_formats(self, llm_service):
        """Test text extraction from different LLM response formats."""
        # Test format 1: direct text field
        response1 = LLMResponseDTO(
            status='success',
            data={'text': 'Extracted text 1'}
        )
        text1 = llm_service._extract_text_from_response(response1)
        assert text1 == 'Extracted text 1'
        
        # Test format 2: content field
        response2 = LLMResponseDTO(
            status='success',
            data={'content': 'Extracted text 2'}
        )
        text2 = llm_service._extract_text_from_response(response2)
        assert text2 == 'Extracted text 2'
        
        # Test format 3: nested results
        response3 = LLMResponseDTO(
            status='success',
            data={'results': [{'answer': 'Extracted text 3'}]}
        )
        text3 = llm_service._extract_text_from_response(response3)
        assert text3 == 'Extracted text 3'
        
        # Test error case
        error_response = LLMResponseDTO(
            status='error',
            error={'message': 'Processing failed'}
        )
        with pytest.raises(TextExtractionError):
            llm_service._extract_text_from_response(error_response)