"""
Test script to verify RAG integration with LLM service.
"""

import asyncio
import logging
from src.constants import AppConfig
from src.services.rag_service import RAGService
from src.services.query_formatter_service import QueryFormatterService
from src.controllers.rag_controller import RAGController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_rag_integration():
    """Test the RAG integration workflow."""
    try:
        logger.info("Starting RAG integration test")
        
        # Initialize services
        config = AppConfig()
        rag_service = RAGService(config)
        query_formatter_service = QueryFormatterService()
        rag_controller = RAGController(rag_service, query_formatter_service)
        
        # Test sample extracted text (simulating LLM response)
        sample_extracted_text = """
        Product: Organic Beef Jerky
        Ingredients: Beef, Sea Salt, Black Pepper, Garlic Powder
        Destination: Dubai, UAE
        Export License: Required
        Shelf Life: 12 months
        """
        
        logger.info("Testing query formatting...")
        
        # Test query formatting
        regulation_info = query_formatter_service.extract_regulation_info(sample_extracted_text)
        formatted_query = query_formatter_service.format_rag_query(regulation_info)
        
        print("\n" + "="*60)
        print("QUERY FORMATTING TEST RESULTS")
        print("="*60)
        print(f"Original Text: {sample_extracted_text.strip()}")
        print(f"Extracted Info: {regulation_info}")
        print(f"Formatted Query: {formatted_query}")
        print("="*60 + "\n")
        
        # Test full integration
        logger.info("Testing full RAG integration...")
        result = await rag_controller.process_extracted_text_for_regulations(sample_extracted_text)
        
        if result.get('success'):
            logger.info("RAG integration test completed successfully!")
        else:
            logger.error(f"RAG integration test failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    asyncio.run(test_rag_integration())