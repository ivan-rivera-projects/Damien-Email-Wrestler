"""Tests for the DynamoDB service."""

import pytest
from unittest.mock import MagicMock, patch
import json
from decimal import Decimal
from app.services.dynamodb_service import (
    get_aioboto3_session,
    DecimalEncoder
)


def test_get_aioboto3_session():
    """Test get_aioboto3_session function."""
    with patch("app.services.dynamodb_service._aioboto3_session", new=None):
        with patch("app.services.dynamodb_service.aioboto3") as mock_aioboto3:
            mock_session = MagicMock()
            mock_aioboto3.Session.return_value = mock_session
            result = get_aioboto3_session()
            mock_aioboto3.Session.assert_called_once()
            assert result is mock_session


def test_decimal_encoder():
    """Test the DecimalEncoder class."""
    encoder = DecimalEncoder()
    
    # Test encoding Decimal
    assert encoder.default(Decimal("10.5")) == 10.5
    
    # Test encoding other types raises TypeError
    with pytest.raises(TypeError):
        encoder.default("not a decimal")
