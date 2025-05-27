import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.tools import settings_tools

@pytest.mark.asyncio
@patch("damien_cli.integrations.gmail_integration.get_gmail_service")
async def test_get_vacation_settings_handler(mock_get_gmail_service_original):
    mock_actual_gmail_service = AsyncMock()
    mock_get_gmail_service_original.return_value = mock_actual_gmail_service
    
    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.get_vacation_settings") as mock_get_vacation:
        mock_get_vacation.return_value = {"enableAutoReply": True}
        
        params = {}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.get_vacation_settings_handler(params, context)
        
        assert result["success"] is True
        assert result["data"]["enableAutoReply"] is True
        assert "retrieved_at" in result["data"]
        assert "user_context" in result["data"]
        mock_get_vacation.assert_called_once_with(gmail_service=mock_actual_gmail_service)

@pytest.mark.asyncio
@patch("damien_cli.integrations.gmail_integration.get_gmail_service")
async def test_update_vacation_settings_handler(mock_get_gmail_service_original):
    mock_actual_gmail_service = AsyncMock()
    mock_get_gmail_service_original.return_value = mock_actual_gmail_service

    vacation_settings_response = {"enableAutoReply": True}
    
    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.update_vacation_settings") as mock_update_vacation:
        mock_update_vacation.return_value = vacation_settings_response
        
        params = {"enabled": True, "subject": "Test Subject", "body": "Test Body"}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.update_vacation_settings_handler(params, context)
        
        assert result["success"] is True
        assert result["data"]["enableAutoReply"] == vacation_settings_response["enableAutoReply"]
        assert "updated_at" in result["data"]
        assert "user_context" in result["data"]
        assert "settings_updated" in result["data"]
        mock_update_vacation.assert_called_once()

@pytest.mark.asyncio 
@patch("damien_cli.integrations.gmail_integration.get_gmail_service")
async def test_update_vacation_settings_handler_validation_error(mock_get_gmail_service_original):
    """Test that enabling vacation responder without subject/body returns an error."""
    mock_actual_gmail_service = AsyncMock()
    mock_get_gmail_service_original.return_value = mock_actual_gmail_service
    
    params = {"enabled": True}  # Missing subject and body
    context = {"session_id": "test_session", "user_id": "test_user"}
    
    result = await settings_tools.update_vacation_settings_handler(params, context)
    
    assert result["success"] is False
    assert "Subject and body are required" in result["error_message"]

@pytest.mark.asyncio
@patch("damien_cli.integrations.gmail_integration.get_gmail_service")
async def test_get_imap_settings_handler(mock_get_gmail_service_original):
    mock_actual_gmail_service = AsyncMock()
    mock_get_gmail_service_original.return_value = mock_actual_gmail_service

    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.get_imap_settings") as mock_get_imap:
        mock_get_imap.return_value = {"enabled": True}
        
        params = {}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.get_imap_settings_handler(params, context)
        
        assert result["success"] is True
        assert result["data"]["enabled"] is True
        mock_get_imap.assert_called_once_with(gmail_service=mock_actual_gmail_service)

@pytest.mark.asyncio
@patch("damien_cli.integrations.gmail_integration.get_gmail_service")
async def test_update_imap_settings_handler(mock_get_gmail_service_original):
    mock_actual_gmail_service = AsyncMock()
    mock_get_gmail_service_original.return_value = mock_actual_gmail_service

    imap_settings_response = {"enabled": True}
    
    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.update_imap_settings") as mock_update_imap:
        mock_update_imap.return_value = imap_settings_response
        
        params = {"enabled": True, "auto_expunge": False, "expunge_behavior": "archive"}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.update_imap_settings_handler(params, context)
        
        assert result["success"] is True
        assert result["data"]["enabled"] == imap_settings_response["enabled"]
        mock_update_imap.assert_called_once()

@pytest.mark.asyncio
@patch("damien_cli.integrations.gmail_integration.get_gmail_service")
async def test_get_pop_settings_handler(mock_get_gmail_service_original):
    mock_actual_gmail_service = AsyncMock()
    mock_get_gmail_service_original.return_value = mock_actual_gmail_service

    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.get_pop_settings") as mock_get_pop:
        mock_get_pop.return_value = {"accessWindow": "all_mail"}
        
        params = {}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.get_pop_settings_handler(params, context)
        
        assert result["success"] is True
        assert result["data"]["accessWindow"] == "all_mail"
        mock_get_pop.assert_called_once_with(gmail_service=mock_actual_gmail_service)

@pytest.mark.asyncio
@patch("damien_cli.integrations.gmail_integration.get_gmail_service")
async def test_update_pop_settings_handler(mock_get_gmail_service_original):
    mock_actual_gmail_service = AsyncMock()
    mock_get_gmail_service_original.return_value = mock_actual_gmail_service

    pop_settings_response = {"accessWindow": "all_mail", "disposition": "leaveInInbox"}
    
    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.update_pop_settings") as mock_update_pop:
        mock_update_pop.return_value = pop_settings_response
        
        params = {"access_window": "allMail", "disposition": "leaveInInbox"}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.update_pop_settings_handler(params, context)
        
        assert result["success"] is True
        assert result["data"]["accessWindow"] == pop_settings_response["accessWindow"]
        assert result["data"]["disposition"] == pop_settings_response["disposition"]
        mock_update_pop.assert_called_once()
