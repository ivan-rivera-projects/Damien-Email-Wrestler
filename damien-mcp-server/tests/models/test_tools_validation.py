import pytest
from pydantic import ValidationError
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../app")))

from models.tools import ListEmailsParams, GetEmailDetailsParams

def test_list_emails_params_include_headers_valid_list():
    params = ListEmailsParams(
        query="is:unread",
        max_results=10,
        include_headers=["From", "Subject"]
    )
    assert params.include_headers == ["From", "Subject"]

def test_list_emails_params_include_headers_stringified_json():
    params = ListEmailsParams(
        query="is:unread",
        max_results=10,
        include_headers='["From", "Subject"]'
    )
    assert params.include_headers == ["From", "Subject"]

def test_list_emails_params_include_headers_invalid_string():
    with pytest.raises(ValidationError) as exc_info:
        ListEmailsParams(
            query="is:unread",
            max_results=10,
            include_headers='invalid string'
        )
    assert "include_headers parsing error" in str(exc_info.value)

def test_get_email_details_params_include_headers_valid_list():
    params = GetEmailDetailsParams(
        message_id="12345",
        include_headers=["From", "Date"]
    )
    assert params.include_headers == ["From", "Date"]

def test_get_email_details_params_include_headers_stringified_json():
    params = GetEmailDetailsParams(
        message_id="12345",
        include_headers='["From", "Date"]'
    )
    assert params.include_headers == ["From", "Date"]

def test_get_email_details_params_include_headers_invalid_string():
    with pytest.raises(ValidationError) as exc_info:
        GetEmailDetailsParams(
            message_id="12345",
            include_headers='not a json array'
        )
    assert "include_headers parsing error" in str(exc_info.value)