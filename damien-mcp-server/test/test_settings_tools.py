import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.tools import settings_tools

@pytest.mark.asyncio
@patch("app.tools.settings_tools.DamienAdapter")
async def test_get_vacation_settings_handler(mock_damien_adapter_class):
    mock_actual_gmail_service = AsyncMock()
    mock_adapter_instance = mock_damien_adapter_class.return_value
    mock_adapter_instance.get_gmail_service = AsyncMock(return_value=mock_actual_gmail_service)
    
    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.get_vacation_settings") as mock_get_vacation:
        mock_get_vacation.return_value = {"enableAutoReply": True}
        
        params = {}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.get_vacation_settings_handler(params, context)
        
        assert result["enableAutoReply"] is True
        assert "retrieved_at" in result
        assert "user_context" in result
        mock_get_vacation.assert_called_once_with(gmail_service=mock_actual_gmail_service)

@pytest.mark.asyncio
@patch("app.tools.settings_tools.DamienAdapter")
async def test_update_vacation_settings_handler(mock_damien_adapter_class):
    mock_actual_gmail_service = AsyncMock()
    mock_adapter_instance = mock_damien_adapter_class.return_value
    mock_adapter_instance.get_gmail_service = AsyncMock(return_value=mock_actual_gmail_service)

    vacation_settings_response = {"enableAutoReply": True}
    
    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.update_vacation_settings") as mock_update_vacation:
        mock_update_vacation.return_value = vacation_settings_response
        
        params = {"enabled": True, "subject": "Test Subject", "body": "Test Body"}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.update_vacation_settings_handler(params, context)
        
        assert result == vacation_settings_response
        mock_update_vacation.assert_called_once()

@pytest.mark.asyncio 
@patch("app.tools.settings_tools.DamienAdapter")
async def test_update_vacation_settings_handler_validation_error(mock_damien_adapter_class):
    """Test that enabling vacation responder without subject/body raises validation error."""
    mock_actual_gmail_service = AsyncMock()
    mock_adapter_instance = mock_damien_adapter_class.return_value
    mock_adapter_instance.get_gmail_service = AsyncMock(return_value=mock_actual_gmail_service)
    
    params = {"enabled": True}  # Missing subject and body
    context = {"session_id": "test_session", "user_id": "test_user"}
    
    with pytest.raises(Exception) as exc_info:
        await settings_tools.update_vacation_settings_handler(params, context)
    
    assert "Subject and body are required" in str(exc_info.value)

@pytest.mark.asyncio
@patch("app.tools.settings_tools.DamienAdapter")
async def test_get_imap_settings_handler(mock_damien_adapter_class):
    mock_actual_gmail_service = AsyncMock()
    mock_adapter_instance = mock_damien_adapter_class.return_value
    mock_adapter_instance.get_gmail_service = AsyncMock(return_value=mock_actual_gmail_service)

    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.get_imap_settings") as mock_get_imap:
        mock_get_imap.return_value = {"enabled": True}
        
        params = {}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.get_imap_settings_handler(params, context)
        
        assert result["enabled"] is True
        mock_get_imap.assert_called_once_with(gmail_service=mock_actual_gmail_service)

@pytest.mark.asyncio
@patch("app.tools.settings_tools.DamienAdapter")
async def test_update_imap_settings_handler(mock_damien_adapter_class):
    mock_actual_gmail_service = AsyncMock()
    mock_adapter_instance = mock_damien_adapter_class.return_value
    mock_adapter_instance.get_gmail_service = AsyncMock(return_value=mock_actual_gmail_service)

    imap_settings_response = {"enabled": True}
    
    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.update_imap_settings") as mock_update_imap:
        mock_update_imap.return_value = imap_settings_response
        
        params = {"enabled": True, "auto_expunge": False, "expunge_behavior": "archive"}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.update_imap_settings_handler(params, context)
        
        assert result == imap_settings_response
        mock_update_imap.assert_called_once()

@pytest.mark.asyncio
@patch("app.tools.settings_tools.DamienAdapter")
async def test_get_pop_settings_handler(mock_damien_adapter_class):
    mock_actual_gmail_service = AsyncMock()
    mock_adapter_instance = mock_damien_adapter_class.return_value
    mock_adapter_instance.get_gmail_service = AsyncMock(return_value=mock_actual_gmail_service)

    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.get_pop_settings") as mock_get_pop:
        mock_get_pop.return_value = {"accessWindow": "all_mail"}
        
        params = {}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.get_pop_settings_handler(params, context)
        
        assert result["accessWindow"] == "all_mail"
        mock_get_pop.assert_called_once_with(gmail_service=mock_actual_gmail_service)

@pytest.mark.asyncio
@patch("app.tools.settings_tools.DamienAdapter")
async def test_update_pop_settings_handler(mock_damien_adapter_class):
    mock_actual_gmail_service = AsyncMock()
    mock_adapter_instance = mock_damien_adapter_class.return_value
    mock_adapter_instance.get_gmail_service = AsyncMock(return_value=mock_actual_gmail_service)

    pop_settings_response = {"accessWindow": "all_mail", "disposition": "leaveInInbox"}
    
    # Mock the gmail_api_service function
    with patch("app.tools.settings_tools.gmail_api_service.update_pop_settings") as mock_update_pop:
        mock_update_pop.return_value = pop_settings_response
        
        params = {"access_window": "allMail", "disposition": "leaveInInbox"}
        context = {"session_id": "test_session", "user_id": "test_user"}
        result = await settings_tools.update_pop_settings_handler(params, context)
        
        assert result == pop_settings_response
        mock_update_pop.assert_called_once()
