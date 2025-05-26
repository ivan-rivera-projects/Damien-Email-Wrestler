import unittest
from unittest.mock import MagicMock, patch
from damien_cli.core_api import gmail_api_service

class TestGmailApiServiceSettings(unittest.TestCase):

    def setUp(self):
        self.mock_service = MagicMock()

    def test_get_vacation_settings_success(self):
        expected_response = {"enableAutoReply": True}
        self.mock_service.users().settings().getVacation().execute.return_value = expected_response
        result = gmail_api_service.get_vacation_settings(self.mock_service)
        self.assertEqual(result, expected_response)

    def test_update_vacation_settings_success(self):
        vacation_settings = {"enableAutoReply": True}
        self.mock_service.users().settings().updateVacation().execute.return_value = vacation_settings
        result = gmail_api_service.update_vacation_settings(self.mock_service, vacation_settings)
        self.assertEqual(result, vacation_settings)

    def test_enable_vacation_responder_success(self):
        current_settings = {"enableAutoReply": False}
        self.mock_service.users().settings().getVacation().execute.return_value = current_settings
        self.mock_service.users().settings().updateVacation().execute.return_value = {"enableAutoReply": True}
        result = gmail_api_service.enable_vacation_responder(self.mock_service)
        self.assertTrue(result["enableAutoReply"])

    def test_disable_vacation_responder_success(self):
        current_settings = {"enableAutoReply": True}
        self.mock_service.users().settings().getVacation().execute.return_value = current_settings
        self.mock_service.users().settings().updateVacation().execute.return_value = {"enableAutoReply": False}
        result = gmail_api_service.disable_vacation_responder(self.mock_service)
        self.assertFalse(result["enableAutoReply"])

    def test_get_imap_settings_success(self):
        expected_response = {"enabled": True}
        self.mock_service.users().settings().getImap().execute.return_value = expected_response
        result = gmail_api_service.get_imap_settings(self.mock_service)
        self.assertEqual(result, expected_response)

    def test_update_imap_settings_success(self):
        imap_settings = {"enabled": True}
        self.mock_service.users().settings().updateImap().execute.return_value = imap_settings
        result = gmail_api_service.update_imap_settings(self.mock_service, imap_settings)
        self.assertEqual(result, imap_settings)

    def test_get_pop_settings_success(self):
        expected_response = {"accessWindow": "all_mail"}
        self.mock_service.users().settings().getPop().execute.return_value = expected_response
        result = gmail_api_service.get_pop_settings(self.mock_service)
        self.assertEqual(result, expected_response)

    def test_update_pop_settings_success(self):
        pop_settings = {"accessWindow": "all_mail"}
        self.mock_service.users().settings().updatePop().execute.return_value = pop_settings
        result = gmail_api_service.update_pop_settings(self.mock_service, pop_settings)
        self.assertEqual(result, pop_settings)

if __name__ == "__main__":
    unittest.main()