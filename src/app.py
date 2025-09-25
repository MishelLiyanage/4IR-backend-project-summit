"""
Main application module for the 4IR Backend Project Summit.
Uses clean architecture with dependency injection.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from src.constants import AppConfig, Messages
from src.exceptions import ConfigurationError
from src.middlewares import (
    MiddlewareChain, LoggingMiddleware, ExceptionHandlingMiddleware,
    ValidationMiddleware, SecurityMiddleware, PerformanceMiddleware
)
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService
from src.services.llm_service import LLMService
from src.controllers.user_controller import UserController
from src.controllers.image_controller import ImageController
from src.models.user import User
from src.dto import UserCreateDTO, UserResponseDTO, PaginatedResponseDTO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ApplicationContainer:
    """Dependency injection container."""
    
    def __init__(self, config: AppConfig):
        """Initialize container with configuration."""
        self.config = config
        self._repositories = {}
        self._services = {}
        self._controllers = {}
        self._middleware_chain = None
        
        self._setup_dependencies()
    
    def _setup_dependencies(self):
        """Setup dependency injection."""
        # Repositories
        self._repositories['user'] = UserRepository()
        
        # Services
        self._services['user'] = UserService(self._repositories['user'])
        self._services['llm'] = LLMService(self.config)
        
        # Controllers
        self._controllers['user'] = UserController(self._services['user'])
        self._controllers['image'] = ImageController(self._services['llm'])
        
        # Middleware chain
        self._middleware_chain = MiddlewareChain()
        self._middleware_chain.add_middleware(LoggingMiddleware())
        self._middleware_chain.add_middleware(PerformanceMiddleware())
        self._middleware_chain.add_middleware(ValidationMiddleware())
        self._middleware_chain.add_middleware(SecurityMiddleware())
        self._middleware_chain.add_middleware(ExceptionHandlingMiddleware())
    
    def get_repository(self, name: str):
        """Get repository by name."""
        return self._repositories.get(name)
    
    def get_service(self, name: str):
        """Get service by name."""
        return self._services.get(name)
    
    def get_controller(self, name: str):
        """Get controller by name."""
        return self._controllers.get(name)
    
    def get_middleware_chain(self) -> MiddlewareChain:
        """Get middleware chain."""
        return self._middleware_chain


class Application:
    """Main application class using clean architecture."""
    
    def __init__(self):
        """Initialize the application."""
        self.config = AppConfig()
        self.container = ApplicationContainer(self.config)
        
        logger.info(f"Initializing {self.config.app_name} v{self.config.app_version}")
        logger.info(f"Environment: {self.config.environment.value}")
        logger.info(f"Debug mode: {self.config.debug}")
    
    def run(self):
        """Run the main application logic."""
        logger.info("Starting application...")
        
        try:
            self._setup()
            asyncio.run(self._main_loop())
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
            if self.config.debug:
                raise
        finally:
            self._cleanup()
    
    def _setup(self):
        """Setup application resources."""
        logger.info("Setting up application resources...")
        
        # Validate configuration
        if not self.config.secret_key or self.config.secret_key == 'your-secret-key-change-in-production':
            if self.config.is_production():
                raise ConfigurationError('secret_key', 'Secret key must be set in production')
            logger.warning("Using default secret key - change this in production!")
    
    async def _main_loop(self):
        """Main application logic with clean architecture demonstration."""
        logger.info("Running main application logic...")
        
        print(f"Welcome to {self.config.app_name}!")
        print("This application demonstrates clean architecture patterns.")
        print("=" * 60)
        
        # Demonstrate the clean architecture
        await self._demonstrate_architecture()
        
        # Demonstrate image processing functionality
        await self._demonstrate_image_processing()
        
        print("\nApplication ready for extension!")
        print("Add your business logic to services, controllers, and repositories.")
    
    async def _demonstrate_architecture(self):
        """Demonstrate the clean architecture with example operations."""
        user_controller = self.container.get_controller('user')
        middleware_chain = self.container.get_middleware_chain()
        
        try:
            print("\n🏗️  Clean Architecture Demonstration")
            print("-" * 40)
            
            # 1. Create a sample user
            print("1. Creating a sample user...")
            create_request = {
                'method': 'POST',
                'path': '/users',
                'body': {
                    'email': 'john.doe@example.com',
                    'name': 'John Doe',
                    'age': 30
                }
            }
            
            # Process through middleware chain
            processed_request = await middleware_chain.process_request(create_request)
            
            # Handle through controller
            create_response = await user_controller.create(processed_request['body'])
            processed_response = await middleware_chain.process_response(create_response)
            
            if processed_response['status'] == 'success':
                user_data = processed_response['data']
                user_id = user_data['id']
                print(f"   ✅ User created: {user_data['name']} ({user_data['email']})")
                
                # 2. Get the user by ID
                print("2. Retrieving user by ID...")
                get_response = await user_controller.get_by_id(user_id)
                print(f"   ✅ User retrieved: {get_response['data']['name']}")
                
                # 3. Get user by email
                print("3. Retrieving user by email...")
                email_response = await user_controller.get_by_email('john.doe@example.com')
                print(f"   ✅ User found by email: {email_response['data']['name']}")
                
                # 4. Update the user
                print("4. Updating user...")
                update_response = await user_controller.update(user_id, {'name': 'John Smith', 'age': 31})
                if update_response['status'] == 'success':
                    print(f"   ✅ User updated: {update_response['data']['name']}")
                
                # 5. Get all users
                print("5. Retrieving all users...")
                all_users_response = await user_controller.get_all()
                print(f"   ✅ Found {len(all_users_response['data']['items'])} users")
                
                # 6. Get active users
                print("6. Retrieving active users...")
                active_users_response = await user_controller.get_active_users()
                print(f"   ✅ Found {len(active_users_response['data']['items'])} active users")
                
                # 7. Deactivate user before deletion (business rule)
                print("7. Deactivating user...")
                deactivate_response = await user_controller.deactivate_user(user_id)
                if deactivate_response['status'] == 'success':
                    print("   ✅ User deactivated")
                
                # 8. Delete the user
                print("8. Deleting user...")
                delete_response = await user_controller.delete(user_id)
                if delete_response['status'] == 'success':
                    print("   ✅ User deleted successfully")
                
            else:
                print(f"   ❌ Failed to create user: {processed_response.get('error', {}).get('message', 'Unknown error')}")
            
            print("\n🎯 Architecture Components Demonstrated:")
            print("   • Models: User entity with business logic")
            print("   • Repositories: Data access layer with in-memory storage")
            print("   • Services: Business logic layer with validation")
            print("   • Controllers: Presentation layer with HTTP handling")
            print("   • DTOs: Data transfer objects for clean API contracts")
            print("   • Exceptions: Custom error handling")
            print("   • Middleware: Cross-cutting concerns (logging, validation, etc.)")
            print("   • Constants: Configuration and application constants")
            
        except Exception as e:
            logger.error(f"Error in architecture demonstration: {e}")
            # Handle through middleware
            error_response = await middleware_chain.process_exception(e)
            if error_response:
                print(f"   ❌ Error: {error_response['error']['message']}")
    
    async def _demonstrate_image_processing(self):
        """Demonstrate the image processing functionality."""
        image_controller = self.container.get_controller('image')
        
        try:
            print("\n🖼️  Image Processing Demonstration")
            print("-" * 40)
            
            # Health check
            print("1. Checking image processing service health...")
            health_response = await image_controller.health_check()
            
            if health_response['status'] == 'success':
                print("   ✅ Image processing service is healthy")
                llm_status = health_response['data']['llm_service']['status']
                print(f"   ✅ LLM service status: {llm_status}")
            else:
                print("   ❌ Image processing service health check failed")
            
            print("\n📝 Image Processing Features:")
            print("   • Base64 image upload and validation")
            print("   • Image size and format validation")
            print("   • Integration with Sysco Gen AI Platform")
            print("   • Text extraction from images")
            print("   • Comprehensive error handling")
            print("   • Request timeout and retry logic")
            
            print("\n🚀 Ready to process images from frontend!")
            print("   Endpoint: POST /images/extract-text")
            print("   Payload: { 'encoded_image': '<base64_data>', 'media_type': 'image/jpeg' }")
            
        except Exception as e:
            logger.error(f"Error in image processing demonstration: {e}")
            print(f"   ❌ Error: {e}")
    
    def _cleanup(self):
        """Cleanup application resources."""
        logger.info("Cleaning up application resources...")
        # Add cleanup logic here if needed