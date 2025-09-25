"""
Tests for clean architecture implementation.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService
from src.controllers.user_controller import UserController
from src.exceptions import ValidationException, NotFoundError
from src.constants import AppConfig


class TestCleanArchitecture:
    """Test cases for clean architecture implementation."""
    
    @pytest.fixture
    def user_repository(self):
        """Create user repository fixture."""
        return UserRepository()
    
    @pytest.fixture
    def user_service(self, user_repository):
        """Create user service fixture."""
        return UserService(user_repository)
    
    @pytest.fixture
    def user_controller(self, user_service):
        """Create user controller fixture."""
        return UserController(user_service)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing."""
        return {
            'email': 'test@example.com',
            'name': 'Test User',
            'age': 25,
            'is_active': True
        }
    
    @pytest.mark.asyncio
    async def test_user_repository_crud(self, user_repository, sample_user_data):
        """Test repository CRUD operations."""
        # Create user
        user = User(**sample_user_data)
        created_user = await user_repository.create(user)
        
        assert created_user.email == sample_user_data['email']
        assert created_user.name == sample_user_data['name']
        assert created_user.id is not None
        
        # Get by ID
        retrieved_user = await user_repository.get_by_id(created_user.id)
        assert retrieved_user is not None
        assert retrieved_user.email == sample_user_data['email']
        
        # Get by email
        user_by_email = await user_repository.get_by_email(sample_user_data['email'])
        assert user_by_email is not None
        assert user_by_email.id == created_user.id
        
        # Update user
        updated_user = User(
            email=sample_user_data['email'],
            name='Updated Name',
            age=26,
            id=created_user.id
        )
        result = await user_repository.update(created_user.id, updated_user)
        assert result.name == 'Updated Name'
        assert result.age == 26
        
        # Get all users
        all_users = await user_repository.get_all()
        assert len(all_users) == 1
        
        # Delete user
        deleted = await user_repository.delete(created_user.id)
        assert deleted is True
        
        # Verify deletion
        deleted_user = await user_repository.get_by_id(created_user.id)
        assert deleted_user is None
    
    @pytest.mark.asyncio
    async def test_user_service_validation(self, user_service, sample_user_data):
        """Test service layer validation."""
        # Test successful creation
        created_user = await user_service.create(sample_user_data)
        assert created_user.email == sample_user_data['email']
        
        # Test duplicate email validation
        with pytest.raises(ValueError, match="Email already exists"):
            await user_service.create(sample_user_data)
        
        # Test invalid email validation
        invalid_data = sample_user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        with pytest.raises(ValueError, match="Invalid email format"):
            await user_service.create(invalid_data)
        
        # Test invalid age validation
        invalid_data = sample_user_data.copy()
        invalid_data['email'] = 'different@example.com'
        invalid_data['age'] = -1
        
        with pytest.raises(ValueError, match="Age must be between"):
            await user_service.create(invalid_data)
        
        # Test empty name validation
        invalid_data = sample_user_data.copy()
        invalid_data['email'] = 'another@example.com'
        invalid_data['name'] = 'A'
        
        with pytest.raises(ValueError, match="Name must be at least"):
            await user_service.create(invalid_data)
    
    @pytest.mark.asyncio
    async def test_user_service_business_logic(self, user_service, sample_user_data):
        """Test service layer business logic."""
        # Create user
        created_user = await user_service.create(sample_user_data)
        user_id = created_user.id
        
        # Test get by email
        user_by_email = await user_service.get_by_email(sample_user_data['email'])
        assert user_by_email is not None
        assert user_by_email.id == user_id
        
        # Test activate/deactivate
        deactivated_user = await user_service.deactivate_user(user_id)
        assert deactivated_user.is_active is False
        
        activated_user = await user_service.activate_user(user_id)
        assert activated_user.is_active is True
        
        # Test deletion business rule (can only delete inactive users)
        success = await user_service.delete(user_id)
        assert success is False  # Should fail because user is active
        
        # Deactivate and try again
        await user_service.deactivate_user(user_id)
        success = await user_service.delete(user_id)
        assert success is True
    
    @pytest.mark.asyncio
    async def test_user_controller_responses(self, user_controller, sample_user_data):
        """Test controller response formatting."""
        # Test successful creation
        response = await user_controller.create(sample_user_data)
        
        assert response['status'] == 'success'
        assert response['status_code'] == 201
        assert 'data' in response
        assert response['data']['email'] == sample_user_data['email']
        
        user_id = response['data']['id']
        
        # Test get by ID
        get_response = await user_controller.get_by_id(user_id)
        assert get_response['status'] == 'success'
        assert get_response['status_code'] == 200
        assert get_response['data']['id'] == user_id
        
        # Test get all
        all_response = await user_controller.get_all()
        assert all_response['status'] == 'success'
        assert 'items' in all_response['data']
        assert len(all_response['data']['items']) > 0
        
        # Test update
        update_data = {'name': 'Updated Name'}
        update_response = await user_controller.update(user_id, update_data)
        assert update_response['status'] == 'success'
        assert update_response['data']['name'] == 'Updated Name'
        
        # Test not found
        not_found_response = await user_controller.get_by_id('nonexistent-id')
        assert not_found_response['status'] == 'error'
        assert not_found_response['status_code'] == 404
    
    @pytest.mark.asyncio
    async def test_user_controller_validation_errors(self, user_controller):
        """Test controller validation error handling."""
        # Test invalid data
        invalid_data = {'name': 'Test'}  # Missing email
        
        response = await user_controller.create(invalid_data)
        assert response['status'] == 'error'
        assert response['status_code'] == 400
        assert 'Email is required' in response['error']['message']
    
    def test_app_config(self):
        """Test application configuration."""
        config = AppConfig()
        
        assert config.app_name == '4IR Backend Project Summit'
        assert config.app_version == '1.0.0'
        assert hasattr(config, 'environment')
        assert hasattr(config, 'debug')
        
        # Test configuration methods
        assert isinstance(config.is_development(), bool)
        assert isinstance(config.is_production(), bool)
        assert isinstance(config.get_database_config(), dict)
        assert isinstance(config.to_dict(), dict)
    
    @pytest.mark.asyncio
    async def test_integration_flow(self, user_controller, sample_user_data):
        """Test complete integration flow."""
        # 1. Create user
        create_response = await user_controller.create(sample_user_data)
        assert create_response['status'] == 'success'
        user_id = create_response['data']['id']
        
        # 2. Get user by email
        email_response = await user_controller.get_by_email(sample_user_data['email'])
        assert email_response['status'] == 'success'
        assert email_response['data']['id'] == user_id
        
        # 3. Get active users
        active_response = await user_controller.get_active_users()
        assert active_response['status'] == 'success'
        assert len(active_response['data']['items']) > 0
        
        # 4. Deactivate user
        deactivate_response = await user_controller.deactivate_user(user_id)
        assert deactivate_response['status'] == 'success'
        assert deactivate_response['data']['is_active'] is False
        
        # 5. Verify user is not in active users list
        active_response2 = await user_controller.get_active_users()
        active_user_ids = [user['id'] for user in active_response2['data']['items']]
        assert user_id not in active_user_ids
        
        # 6. Delete user (should work now that it's inactive)
        delete_response = await user_controller.delete(user_id)
        assert delete_response['status'] == 'success'
        assert delete_response['status_code'] == 204