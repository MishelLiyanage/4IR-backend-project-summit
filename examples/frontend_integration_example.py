"""
Example demonstrating how to use the image processing API.
This simulates what the frontend would send to the backend.
"""

import asyncio
import base64
import json
import sys
import os

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

from src.controllers.image_controller import ImageController
from src.services.llm_service import LLMService
from src.constants import AppConfig
from src.middlewares import MiddlewareChain, LoggingMiddleware, ValidationMiddleware


def create_sample_base64_image():
    """Create a minimal valid JPEG base64 string for testing."""
    # This is a minimal 1x1 pixel JPEG image in base64
    # In real usage, this would come from the frontend camera/gallery
    minimal_jpeg = (
        "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB"
        "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEB"
        "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIA"
        "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEB"
        "AQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwBGgA//"
    )
    return minimal_jpeg


async def simulate_frontend_request():
    """Simulate a request from the frontend to extract text from an image."""
    print("🚀 Simulating Frontend Image Upload Request")
    print("=" * 50)
    
    # Create application components
    config = AppConfig()
    llm_service = LLMService(config)
    image_controller = ImageController(llm_service)
    
    # Create middleware chain
    middleware_chain = MiddlewareChain()
    middleware_chain.add_middleware(LoggingMiddleware())
    middleware_chain.add_middleware(ValidationMiddleware())
    
    # Simulate frontend request payload
    frontend_request = {
        'method': 'POST',
        'path': '/images/extract-text',
        'body': {
            'encoded_image': create_sample_base64_image(),
            'media_type': 'image/jpeg'
        }
    }
    
    print("📤 Frontend Request:")
    print(f"   Method: {frontend_request['method']}")
    print(f"   Endpoint: {frontend_request['path']}")
    print(f"   Content Type: {frontend_request['body']['media_type']}")
    print(f"   Image Size: {len(frontend_request['body']['encoded_image'])} characters (base64)")
    
    try:
        # Process request through middleware
        print("\n🔄 Processing through middleware...")
        processed_request = await middleware_chain.process_request(frontend_request)
        
        # Handle the request with the controller
        print("📝 Extracting text from image...")
        response = await image_controller.extract_text(processed_request['body'])
        
        # Process response through middleware
        processed_response = await middleware_chain.process_response(response)
        
        print("\n📨 Backend Response:")
        print(f"   Status: {processed_response['status']}")
        print(f"   Status Code: {processed_response['status_code']}")
        
        if processed_response['status'] == 'success':
            print("   ✅ Text extraction successful!")
            data = processed_response['data']
            print(f"   📄 Extracted Text: '{data['extracted_text']}'")
            print(f"   ⏱️  Processing Time: {data.get('processing_time_ms', 'N/A')}ms")
        else:
            print("   ❌ Text extraction failed!")
            error = processed_response.get('error', {})
            print(f"   Error: {error.get('message', 'Unknown error')}")
            print(f"   Type: {error.get('type', 'Unknown')}")
    
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        
        # Handle exception through middleware
        error_response = await middleware_chain.process_exception(e)
        if error_response:
            print("🛠️  Handled by middleware:")
            print(f"   Error Type: {error_response['error']['type']}")
            print(f"   Message: {error_response['error']['message']}")


async def demonstrate_api_contract():
    """Demonstrate the API contract for frontend developers."""
    print("\n📋 API Contract for Frontend Integration")
    print("=" * 50)
    
    print("🌐 Endpoint: POST /images/extract-text")
    print("\n📥 Request Format:")
    request_example = {
        "encoded_image": "data:image/jpeg;base64,/9j/4AAQ...[base64 image data]",
        "media_type": "image/jpeg"  # Optional, defaults to image/jpeg
    }
    print(json.dumps(request_example, indent=2))
    
    print("\n📤 Success Response (200):")
    success_response = {
        "status": "success",
        "status_code": 200,
        "data": {
            "extracted_text": "Sample extracted text from the image",
            "processing_time_ms": 1250,
            "image_metadata": {
                "media_type": "image/jpeg",
                "size_estimate": 12345
            }
        }
    }
    print(json.dumps(success_response, indent=2))
    
    print("\n❌ Error Response (400/422/503):")
    error_response = {
        "status": "error",
        "status_code": 400,
        "error": {
            "message": "Invalid base64 image data",
            "type": "BadRequest"
        }
    }
    print(json.dumps(error_response, indent=2))
    
    print("\n📝 Frontend Integration Notes:")
    print("• Convert captured image to base64 before sending")
    print("• Include proper media_type (image/jpeg, image/png)")
    print("• Handle various HTTP status codes (200, 400, 408, 422, 503)")
    print("• Implement retry logic for 503 Service Unavailable")
    print("• Show loading state during processing (can take 5-60 seconds)")
    print("• Maximum image size: 5MB")
    print("• Supported formats: JPEG, PNG")


async def main():
    """Main function to run the demonstration."""
    print("🖼️  4IR Image Processing API Demonstration")
    print("=" * 60)
    
    # Run the simulation
    await simulate_frontend_request()
    
    # Show API contract
    await demonstrate_api_contract()
    
    print("\n🎉 Demonstration complete!")
    print("The backend is ready to receive image processing requests from the frontend.")


if __name__ == "__main__":
    asyncio.run(main())