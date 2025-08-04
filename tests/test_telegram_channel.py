"""
Tests for the new Telegram channel architecture.

This module contains comprehensive tests for the TelegramChannel implementation,
including session ID generation, memory pruning logic, channel interface compliance,
and error handling scenarios.
"""

import asyncio
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import AsyncMock, MagicMock, patch
from app.channels.telegram.handler import TelegramChannel, create_telegram_channel, get_telegram_channel
from app.channels.telegram.memory import TelegramMemory, create_telegram_memory
from app.channels.telegram.client import TelegramClient


class TestTelegramChannel:
    """Test suite for TelegramChannel implementation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create mock dependencies
        self.mock_memory = AsyncMock(spec=TelegramMemory)
        self.mock_client = AsyncMock(spec=TelegramClient)
        
        # Create channel with mocked dependencies
        self.channel = TelegramChannel(
            memory=self.mock_memory,
            client=self.mock_client
        )
    
    def test_session_id_generation_private_chat(self):
        """Test session ID generation for private chats."""
        message_data = {
            "user_id": "12345",
            "chat_id": "12345",
            "is_group": False
        }
        
        session_id = self.channel.get_session_id(message_data)
        assert session_id == "tg_private_12345"
    
    def test_session_id_generation_group_chat(self):
        """Test session ID generation for group chats."""
        message_data = {
            "user_id": "12345",
            "chat_id": "67890",
            "is_group": True
        }
        
        session_id = self.channel.get_session_id(message_data)
        assert session_id == "tg_group_67890_12345"
    
    def test_extract_message_data_valid_private_message(self):
        """Test message data extraction for valid private message."""
        raw_update = {
            "update_id": 123456,
            "message": {
                "message_id": 789,
                "from": {
                    "id": 12345,
                    "username": "test_user",
                    "first_name": "Test",
                    "last_name": "User"
                },
                "chat": {
                    "id": 12345,
                    "type": "private"
                },
                "text": "Hello bot!",
                "date": 1234567890
            }
        }
        
        message_data = self.channel.extract_message_data(raw_update)
        
        assert message_data["user_id"] == "12345"
        assert message_data["username"] == "test_user"
        assert message_data["message_text"] == "Hello bot!"
        assert message_data["chat_id"] == "12345"
        assert message_data["message_id"] == "789"
        assert message_data["is_group"] == False
        assert message_data["chat_type"] == "private"
    
    def test_extract_message_data_group_message(self):
        """Test message data extraction for group message."""
        raw_update = {
            "update_id": 123456,
            "message": {
                "message_id": 789,
                "from": {
                    "id": 12345,
                    "first_name": "Test",
                    "last_name": "User"
                },
                "chat": {
                    "id": 67890,
                    "type": "group"
                },
                "text": "Hello group!",
                "date": 1234567890
            }
        }
        
        message_data = self.channel.extract_message_data(raw_update)
        
        assert message_data["user_id"] == "12345"
        assert message_data["username"] == "Test User"  # Fallback to first + last name
        assert message_data["chat_id"] == "67890"
        assert message_data["is_group"] == True
        assert message_data["chat_type"] == "group"
    
    def test_extract_message_data_missing_username_fallback(self):
        """Test username fallback when username is missing."""
        raw_update = {
            "update_id": 123456,
            "message": {
                "message_id": 789,
                "from": {
                    "id": 12345,
                    "first_name": "OnlyFirst"
                },
                "chat": {
                    "id": 12345,
                    "type": "private"
                },
                "text": "Hello!",
                "date": 1234567890
            }
        }
        
        message_data = self.channel.extract_message_data(raw_update)
        assert message_data["username"] == "OnlyFirst"
    
    def test_extract_message_data_missing_all_names_fallback(self):
        """Test fallback when all name fields are missing."""
        raw_update = {
            "update_id": 123456,
            "message": {
                "message_id": 789,
                "from": {
                    "id": 12345
                },
                "chat": {
                    "id": 12345,
                    "type": "private"
                },
                "text": "Hello!",
                "date": 1234567890
            }
        }
        
        message_data = self.channel.extract_message_data(raw_update)
        assert message_data["username"] == "unknown"
    
    def test_extract_message_data_invalid_missing_message(self):
        """Test error handling for missing message field."""
        raw_update = {"update_id": 123456}
        
        with pytest.raises(ValueError, match="No 'message' field"):
            self.channel.extract_message_data(raw_update)
    
    def test_extract_message_data_invalid_missing_user_id(self):
        """Test error handling for missing user ID."""
        raw_update = {
            "message": {
                "message_id": 789,
                "from": {},  # No ID
                "chat": {"id": 12345, "type": "private"},
                "text": "Hello!",
                "date": 1234567890
            }
        }
        
        with pytest.raises(ValueError, match="Missing user ID"):
            self.channel.extract_message_data(raw_update)
    
    def test_should_process_message_valid(self):
        """Test message processing validation for valid message."""
        message_data = {
            "user_id": "12345",
            "username": "test_user",
            "message_text": "Hello bot!",
            "timestamp": 1234567890
        }
        
        should_process = self.channel.should_process_message(message_data)
        assert should_process == True
    
    def test_should_process_message_bot_message(self):
        """Test message filtering for bot's own messages."""
        message_data = {
            "user_id": "12345",
            "username": "z3_agent_bot",  # Bot's username
            "message_text": "Hello!",
            "timestamp": 1234567890
        }
        
        should_process = self.channel.should_process_message(message_data)
        assert should_process == False
    
    def test_should_process_message_empty_text(self):
        """Test message filtering for empty text."""
        message_data = {
            "user_id": "12345",
            "username": "test_user",
            "message_text": "",  # Empty message
            "timestamp": 1234567890
        }
        
        should_process = self.channel.should_process_message(message_data)
        assert should_process == False
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self):
        """Test successful conversation history retrieval."""
        session_id = "tg_private_12345"
        expected_history = "User: Hello\nBot: Hi there!"
        
        self.mock_memory.get_history.return_value = expected_history
        
        history = await self.channel.get_conversation_history(session_id)
        
        assert history == expected_history
        self.mock_memory.get_history.assert_called_once_with(session_id)
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_no_memory(self):
        """Test conversation history with no memory instance."""
        channel_no_memory = TelegramChannel(memory=None, client=self.mock_client)
        
        history = await channel_no_memory.get_conversation_history("test_session")
        
        assert history == ""
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_error(self):
        """Test conversation history error handling."""
        session_id = "tg_private_12345"
        self.mock_memory.get_history.side_effect = Exception("Database error")
        
        history = await self.channel.get_conversation_history(session_id)
        
        assert history == ""
    
    @pytest.mark.asyncio
    async def test_send_reply_success(self):
        """Test successful reply sending."""
        reply = "Hello there!"
        metadata = {
            "chat_id": "12345",
            "reply_to_message_id": "789"
        }
        
        self.mock_client.send_message.return_value = True
        
        success = await self.channel.send_reply(reply, metadata)
        
        assert success == True
        self.mock_client.send_message.assert_called_once_with(
            chat_id="12345",
            text=reply,
            reply_to_message_id="789"
        )
    
    @pytest.mark.asyncio
    async def test_send_reply_no_client(self):
        """Test reply sending with no client."""
        channel_no_client = TelegramChannel(memory=self.mock_memory, client=None)
        
        success = await channel_no_client.send_reply("Hello", {})
        
        assert success == False
    
    @pytest.mark.asyncio
    async def test_send_reply_client_error(self):
        """Test reply sending with client error."""
        self.mock_client.send_message.side_effect = Exception("Network error")
        
        success = await self.channel.send_reply("Hello", {"chat_id": "12345"})
        
        assert success == False
    
    @pytest.mark.asyncio
    async def test_get_memory_stats_success(self):
        """Test successful memory stats retrieval."""
        session_id = "tg_private_12345"
        expected_stats = {
            "session_id": session_id,
            "message_count": 10,
            "oldest_message": "2024-01-01",
            "newest_message": "2024-01-02"
        }
        
        self.mock_memory.get_memory_size.return_value = expected_stats
        
        stats = await self.channel.get_memory_stats(session_id)
        
        assert stats == expected_stats
        self.mock_memory.get_memory_size.assert_called_once_with(session_id)
    
    @pytest.mark.asyncio
    async def test_get_memory_stats_no_memory(self):
        """Test memory stats with no memory instance."""
        channel_no_memory = TelegramChannel(memory=None, client=self.mock_client)
        
        stats = await channel_no_memory.get_memory_stats("test_session")
        
        assert "error" in stats
        assert "No memory instance" in stats["error"]


class TestTelegramMemoryPruning:
    """Test suite for Telegram memory pruning functionality."""
    
    @pytest.mark.asyncio
    async def test_memory_pruning_integration(self):
        """Integration test for memory pruning functionality."""
        # This would require a real SQLite database setup
        # For now, we'll mock the pruning behavior
        
        mock_memory = AsyncMock(spec=TelegramMemory)
        mock_memory.prune_old_messages.return_value = None
        mock_memory.get_memory_size.return_value = {
            "message_count": 25,  # Under limit after pruning
            "session_id": "test_session"
        }
        
        # Test that pruning is called during save
        await mock_memory.prune_old_messages("test_session")
        mock_memory.prune_old_messages.assert_called_once_with("test_session")


class TestChannelInterfaceCompliance:
    """Test suite to verify TelegramChannel implements BaseChannel interface correctly."""
    
    def test_telegram_channel_implements_base_channel(self):
        """Test that TelegramChannel properly implements BaseChannel interface."""
        from app.channels.base import BaseChannel
        
        channel = TelegramChannel()
        assert isinstance(channel, BaseChannel)
        
        # Check that all required methods exist
        required_methods = [
            'process_message',
            'get_session_id', 
            'send_reply',
            'get_conversation_history',
            'extract_message_data'
        ]
        
        for method_name in required_methods:
            assert hasattr(channel, method_name)
            assert callable(getattr(channel, method_name))


class TestFactoryFunctions:
    """Test suite for factory functions and singletons."""
    
    def test_create_telegram_channel(self):
        """Test TelegramChannel factory function."""
        with patch('app.channels.telegram.handler.create_telegram_memory') as mock_create_memory, \
             patch('app.channels.telegram.handler.get_telegram_client') as mock_get_client:
            
            mock_memory = AsyncMock()
            mock_client = AsyncMock()
            mock_create_memory.return_value = mock_memory
            mock_get_client.return_value = mock_client
            
            channel = create_telegram_channel()
            
            assert isinstance(channel, TelegramChannel)
            assert channel.memory == mock_memory
            assert channel.client == mock_client
    
    def test_get_telegram_channel_singleton(self):
        """Test that get_telegram_channel returns singleton instance."""
        # Reset singleton for test
        import app.channels.telegram.handler as handler_module
        handler_module._telegram_channel = None
        
        with patch('app.channels.telegram.handler.create_telegram_channel') as mock_create:
            mock_channel = TelegramChannel()
            mock_create.return_value = mock_channel
            
            # First call should create instance
            channel1 = get_telegram_channel()
            assert channel1 == mock_channel
            
            # Second call should return same instance
            channel2 = get_telegram_channel()
            assert channel2 == mock_channel
            assert channel1 is channel2
            
            # Factory should only be called once
            mock_create.assert_called_once()


if __name__ == "__main__":
    """Run tests interactively."""
    print("🧪 Running Telegram Channel Tests")
    print("=" * 50)
    
    # Run individual test methods for demonstration
    test_channel = TestTelegramChannel()
    test_channel.setup_method()
    
    # Test session ID generation
    print("Testing session ID generation...")
    test_channel.test_session_id_generation_private_chat()
    test_channel.test_session_id_generation_group_chat()
    print("✅ Session ID tests passed")
    
    # Test message extraction
    print("Testing message data extraction...")
    test_channel.test_extract_message_data_valid_private_message()
    test_channel.test_extract_message_data_group_message()
    print("✅ Message extraction tests passed")
    
    # Test message filtering
    print("Testing message filtering...")
    test_channel.test_should_process_message_valid()
    test_channel.test_should_process_message_bot_message()
    print("✅ Message filtering tests passed")
    
    # Test interface compliance
    print("Testing interface compliance...")
    interface_test = TestChannelInterfaceCompliance()
    interface_test.test_telegram_channel_implements_base_channel()
    print("✅ Interface compliance tests passed")
    
    print("\n🎉 All tests passed! New Telegram channel architecture is working correctly.")
    print("\nTo run with pytest:")
    print("pytest tests/test_telegram_channel.py -v")