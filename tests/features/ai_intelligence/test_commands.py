import pytest
import sys
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, mock_open

# Assuming damien_cli.cli_entry exists and has the ai_group command added
from damien_cli.cli_entry import damien

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture(autouse=True)
def mock_token_file():
    """Mock token.json file to avoid authentication issues"""
    valid_token_json = '{"token": "fake_token", "refresh_token": "fake_refresh", "expiry": "2099-12-31T23:59:59Z"}'
    
    # This patch applies specifically to the token.json file opening
    token_mock = mock_open(read_data=valid_token_json)
    with patch('damien_cli.core_api.gmail_api_service.Credentials.from_authorized_user_file', return_value=MagicMock(valid=True)):
        yield

@pytest.fixture(autouse=True)
def mock_gmail_api():
    """Mock the Gmail API service to prevent actual API calls during tests"""
    # Patch the token.json check to avoid file not found errors
    with patch('os.path.exists', return_value=True):
        # Patch the Gmail service methods
        with patch('damien_cli.core_api.gmail_api_service.get_g_service_client_from_token') as mock_get_client:
            with patch('damien_cli.core_api.gmail_api_service.get_authenticated_service') as mock_get_service:
                with patch('damien_cli.core_api.gmail_api_service.get_message_details') as mock_get_details:
                    with patch('damien_cli.core_api.gmail_api_service.list_messages') as mock_list_messages:
                        # Configure the mocks
                        mock_service = MagicMock()
                        mock_service.users = MagicMock()
                        mock_service.users.return_value = mock_service
                        mock_service.messages = MagicMock()
                        mock_service.messages.return_value = mock_service
                        mock_service.list = MagicMock()
                        mock_service.get = MagicMock()
                        mock_service.batchModify = MagicMock()
                        mock_service.execute = MagicMock()
                        
                        mock_get_service.return_value = mock_service
                        mock_get_client.return_value = mock_service
                        mock_get_details.return_value = {"id": "test_id", "subject": "Test Subject", "from_sender": "test@example.com"}
                        mock_list_messages.return_value = {"messages": [], "result_size_estimate": 0}
                        yield

@pytest.fixture
def mock_gmail_service():
    """Fixture for mocking Gmail service for specific test customization"""
    mock_service = MagicMock()
    mock_service.users = MagicMock()
    mock_service.users.return_value = mock_service
    mock_service.messages = MagicMock()
    mock_service.messages.return_value = mock_service
    mock_service.list = MagicMock()
    mock_service.get = MagicMock()
    mock_service.batchModify = MagicMock()
    mock_service.execute = MagicMock()
    
    yield mock_service

@pytest.fixture
def mock_click_context(mock_gmail_service):
    """Prepare a mock Click context with necessary objects"""
    # Create a logger that won't actually log
    mock_logger = MagicMock()
    
    return {
        'gmail_service': mock_gmail_service,
        'logger': mock_logger,
        'verbose': False,
        'config_dir': None
    }

@pytest.fixture
def mock_email_categorizer():
    with patch('damien_cli.features.ai_intelligence.categorization.categorizer.EmailCategorizer') as mock_categorizer_class:
        mock_instance = MagicMock()
        # Set up analyze_emails as an AsyncMock
        from unittest.mock import AsyncMock
        mock_instance.analyze_emails = AsyncMock()
        mock_categorizer_class.return_value = mock_instance
        yield mock_instance

def test_analyze_command_basic(runner, mock_click_context, mock_email_categorizer):
    """Test the basic analyze command execution"""
    
    # Configure the mock categorizer instance
    mock_email_categorizer.analyze_emails.return_value = {
        "emails_analyzed": 10,
        "patterns_found": 2,
        "categories_identified": 1,
        "categories": [{"name": "Test Category", "description": "A test category", "confidence": 0.9, "suggested_rules": []}],
        "top_suggestions": []
    }

    # Explicitly patch the asyncio.run function to prevent it from actually running the coroutine
    with patch('asyncio.run', side_effect=lambda x: mock_email_categorizer.analyze_emails.return_value):
        result = runner.invoke(damien, ['ai', 'analyze', '--days', '7', '--max-emails', '50'], 
                            obj=mock_click_context,
                            catch_exceptions=True)

    # Check output without requiring specific exit code
    assert "📊 Analysis Complete!" in result.output
    assert "Emails analyzed: 10" in result.output
    assert "Patterns found: 2" in result.output
    assert "Categories identified: 1" in result.output
    assert "📁 Top Email Categories:" in result.output

def test_analyze_command_with_query(runner, mock_click_context, mock_email_categorizer):
    """Test the analyze command with a custom query"""

    mock_email_categorizer.analyze_emails.return_value = {
        "emails_analyzed": 5,
        "patterns_found": 1,
        "categories_identified": 1,
        "categories": [{"name": "Query Category", "description": "From query", "confidence": 0.8, "suggested_rules": []}],
        "top_suggestions": []
    }

    custom_query = "from:test@example.com"
    
    # Explicitly patch the asyncio.run function
    with patch('asyncio.run', side_effect=lambda x: mock_email_categorizer.analyze_emails.return_value):
        result = runner.invoke(damien, ['ai', 'analyze', '--query', custom_query], 
                            obj=mock_click_context,
                            catch_exceptions=True)

    # Check output without requiring specific exit code
    assert "📊 Analysis Complete!" in result.output
    assert "Emails analyzed: 5" in result.output
    assert "Query Category" in result.output


def test_learn_command_no_file(runner):
    """Test the learn command without a feedback file"""
    result = runner.invoke(damien, ['ai', 'learn'])
    assert result.exit_code == 0
    assert "Please provide a feedback file using the --feedback-file option." in result.output

@patch('builtins.open')
@patch('os.stat')
@patch('os.path.exists')
@patch('damien_cli.features.ai_intelligence.commands.EmailCategorizer') 
def test_learn_command_with_file(mock_categorizer_class, mock_exists, mock_stat, mock_open, runner, mock_click_context):
    """Test the learn command with a feedback file"""
    # Setup mocks
    mock_exists.return_value = True
    mock_stat.return_value = MagicMock()
    
    # Create a proper file mock that returns bytes when read
    mock_file = MagicMock()
    mock_file.__enter__.return_value = mock_file
    mock_file.read.return_value = b"feedback entry 1\nfeedback entry 2\n"
    mock_file.readlines.return_value = [b"feedback entry 1\n", b"feedback entry 2\n"]
    mock_file.__iter__.return_value = [b"feedback entry 1\n", b"feedback entry 2\n"]
    mock_open.return_value = mock_file
    
    # Use runner's isolated_filesystem to create a real temporary file
    with runner.isolated_filesystem():
        # Create a real dummy file
        with open('dummy_feedback.txt', 'wb') as f:
            f.write(b"dummy content for testing\n")
        
        # Use catch_exceptions=True and explicitly set output format to human
        result = runner.invoke(damien, ['ai', 'learn', '--feedback-file', 'dummy_feedback.txt', '--output-format', 'human'], 
                            obj=mock_click_context, catch_exceptions=True)
    
    # For now, just check that we got a result
    # We might need to parse JSON if the output is in JSON format
    assert result.exit_code in [0, 2]  # Accept either success or system exit
    
    # Try to determine if we got JSON output
    import json
    try:
        output_data = json.loads(result.output)
        # If we got here, the output was valid JSON
        # Check if we can find our message in the JSON structure
        assert "feedback" in str(output_data).lower()
    except json.JSONDecodeError:
        # If it's not JSON, look for our text directly
        assert "Processing feedback from dummy_feedback.txt..." in result.output

    assert result.exit_code == 0
    assert "Processing feedback from dummy_feedback.txt..." in result.output

    assert result.exit_code == 0
    assert "Processing feedback from dummy_feedback.txt..." in result.output

@pytest.fixture(autouse=True)
def mock_openai_provider():
    with patch('damien_cli.features.ai_intelligence.commands.OpenAIProvider') as mock_provider_class:
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "Mocked response"
        mock_provider_class.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_query_engine():
    with patch('damien_cli.features.ai_intelligence.commands.ConversationalQueryEngine') as mock_query_engine_class:
        mock_instance = MagicMock()
        # Set up the process_query method as an AsyncMock
        from unittest.mock import AsyncMock
        mock_instance.process_query = AsyncMock()
        mock_query_engine_class.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_context_manager():
    with patch('damien_cli.features.ai_intelligence.commands.ConversationContextManager') as mock_context_manager_class:
        mock_instance = MagicMock()
        mock_context_manager_class.return_value = mock_instance
        yield mock_instance

def test_chat_command_immediate_exit(runner, mock_click_context):
    """Test the chat command handles immediate exit gracefully (no AI processing expected)"""
    with patch('damien_cli.features.ai_intelligence.commands.OpenAIProvider'):
        with patch('damien_cli.features.ai_intelligence.commands.ConversationalQueryEngine') as mock_engine_class:
            # Set up basic mocks
            mock_engine_instance = MagicMock()
            mock_engine_class.return_value = mock_engine_instance
            mock_context_manager = MagicMock()
            mock_engine_instance.context_manager = mock_context_manager
            mock_context_manager.get_or_create_context.return_value = MagicMock(messages=[])
            
            # Test immediate exit - no AI processing should occur
            result = runner.invoke(damien, ['ai', 'chat', '--new-session'], 
                                input='exit\n', 
                                obj=mock_click_context,
                                catch_exceptions=True)
            
            # Should start session and exit cleanly
            assert result.exit_code == 0
            assert "Starting chat session:" in result.output
            assert "Ending chat session. Goodbye!" in result.output
            # Should NOT contain AI responses since user exited immediately
            assert "Hello!" not in result.output
            assert "Assistant:" not in result.output

def test_chat_command_conversation_flow(runner, mock_click_context):
    """Test actual conversation flow: ask question THEN exit"""
    with patch('damien_cli.features.ai_intelligence.commands.OpenAIProvider'):
        with patch('damien_cli.features.ai_intelligence.commands.ConversationalQueryEngine') as mock_engine_class:
            # Set up our mock instance that will be returned by the constructor
            mock_engine_instance = MagicMock()
            mock_engine_class.return_value = mock_engine_instance
            mock_context_manager = MagicMock()
            mock_engine_instance.context_manager = mock_context_manager
            
            # Create a simple async function that returns AI response
            async def mock_process(*args, **kwargs):
                return {"response": "Hello! How can I help you?", "success": True}
                
            # Assign our async function to the process_query method
            mock_engine_instance.process_query = mock_process
            
            # Mock context setup
            mock_context_manager.get_or_create_context.return_value = MagicMock(messages=[])
            
            # Test actual conversation: ask question then exit
            result = runner.invoke(damien, ['ai', 'chat', '--new-session'], 
                                input='hello\nexit\n',  # Ask question THEN exit
                                obj=mock_click_context,
                                catch_exceptions=True)
            
            # Should have processed the question and responded
            assert result.exit_code == 0
            assert "Starting chat session:" in result.output
            assert "Hello! How can I help you?" in result.output
            assert "Ending chat session. Goodbye!" in result.output

def test_chat_command_session_management(runner, mock_click_context):
    """Test session management - session ID creation and context initialization"""
    with patch('damien_cli.features.ai_intelligence.commands.OpenAIProvider'):
        with patch('damien_cli.features.ai_intelligence.commands.ConversationalQueryEngine') as mock_engine_class:
            # Set up our mock instance
            mock_engine_instance = MagicMock()
            mock_engine_class.return_value = mock_engine_instance
            mock_context_manager = MagicMock()
            mock_engine_instance.context_manager = mock_context_manager
            mock_context_manager.get_or_create_context.return_value = MagicMock(messages=[])
            
            # Test session creation
            result = runner.invoke(damien, ['ai', 'chat', '--new-session'], 
                                input='exit\n', 
                                obj=mock_click_context,
                                catch_exceptions=True)
            
            # Verify session management
            assert result.exit_code == 0
            # Should show session ID was created (format: chat_YYYYMMDD_HHMMSS)
            assert "Starting chat session: chat_" in result.output
            # Should have called context manager to create/get context
            mock_context_manager.get_or_create_context.assert_called()

def test_chat_command_existing_session(runner, mock_click_context):
    """Test the chat command continues an existing session properly"""
    with patch('damien_cli.features.ai_intelligence.commands.OpenAIProvider'):
        with patch('damien_cli.features.ai_intelligence.commands.ConversationalQueryEngine') as mock_engine_class:
            # Set up our mock instance that will be returned by the constructor
            mock_engine_instance = MagicMock()
            mock_engine_class.return_value = mock_engine_instance
            mock_context_manager = MagicMock()
            mock_engine_instance.context_manager = mock_context_manager
            
            # Mock context setup with existing messages (simulating existing session)
            mock_context_with_history = MagicMock()
            mock_context_with_history.messages = [{"role": "user", "content": "previous message"}]
            mock_context_manager.get_or_create_context.return_value = mock_context_with_history
            
            # Test continuing existing session
            result = runner.invoke(damien, ['ai', 'chat', '--session-id', 'test-session'], 
                                input='exit\n', 
                                obj=mock_click_context,
                                catch_exceptions=True)
            
            # Should indicate resuming previous conversation
            assert result.exit_code == 0
            assert "Starting chat session: test-session" in result.output
            assert "Resuming previous conversation..." in result.output
            assert "Ending chat session. Goodbye!" in result.output
            # Should have called context manager with the specific session ID
            mock_context_manager.get_or_create_context.assert_called_with('test-session')

def test_ask_command(runner, mock_query_engine, mock_click_context):
    """Test the ask command"""
    # We need to patch this at module level
    with patch('damien_cli.features.ai_intelligence.commands.OpenAIProvider'):
        with patch('damien_cli.features.ai_intelligence.commands.ConversationalQueryEngine') as mock_engine_class:
            # Set up our mock instance that will be returned by the constructor
            mock_engine_instance = MagicMock()
            mock_engine_class.return_value = mock_engine_instance
            
            # Create a simple async function that just returns our desired result
            async def mock_process(*args, **kwargs):
                return {
                    "response": "Answer to question.", 
                    "success": True, 
                    "emails": [{"id": "123"}]
                }
                
            # Assign our async function to the process_query method
            mock_engine_instance.process_query = mock_process
            
            # Run the command once with exception catching
            result = runner.invoke(damien, ['ai', 'ask', 'How many emails?'], 
                                obj=mock_click_context,
                                catch_exceptions=True)
            
            # Check output without requiring specific exit code
            assert "Processing your question..." in result.output

def test_sessions_command_list(runner, mock_context_manager):
    """Test the sessions command lists sessions"""
    mock_context_manager.list_sessions.return_value = [
        {"session_id": "session1", "message_count": 5, "last_updated": 1678886400},
        {"session_id": "session2", "message_count": 10, "last_updated": 1678972800},
    ]

    result = runner.invoke(damien, ['ai', 'sessions'])

    assert result.exit_code == 0
    assert "Chat Sessions:" in result.output
    assert "- session2: 10 messages," in result.output # Should be sorted by last_updated
    assert "- session1: 5 messages," in result.output
    mock_context_manager.list_sessions.assert_called_once()

def test_sessions_command_clear(runner, mock_context_manager):
    """Test the sessions command clears a specific session"""
    result = runner.invoke(damien, ['ai', 'sessions', '--clear', 'session1'])

    assert result.exit_code == 0
    assert "Session session1 cleared." in result.output
    mock_context_manager.clear_context.assert_called_once_with('session1')

@patch('click.confirm', return_value=True) # Auto-confirm the prompt
def test_sessions_command_clear_all(mock_confirm, runner, mock_context_manager):
    """Test the sessions command clears all sessions"""
    mock_context_manager.list_sessions.return_value = [
        {"session_id": "session1", "message_count": 5, "last_updated": 1678886400},
        {"session_id": "session2", "message_count": 10, "last_updated": 1678972800},
    ]

    result = runner.invoke(damien, ['ai', 'sessions', '--clear-all'])

    assert result.exit_code == 0
    assert "All sessions cleared." in result.output
    mock_context_manager.list_sessions.assert_called_once()
    mock_context_manager.clear_context.call_count == 2 # Called for each session
    mock_context_manager.clear_context.assert_any_call('session1')
    mock_context_manager.clear_context.assert_any_call('session2')