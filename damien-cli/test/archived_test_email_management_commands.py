import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from damien_cli import cli_entry # Changed import

class TestEmailManagementCommands(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    @patch("damien_cli.core_api.gmail_api_service.get_authenticated_service")
    @patch("damien_cli.core_api.gmail_api_service.get_vacation_settings")
    def test_get_vacation_settings_cmd(self, mock_get_vacation, mock_get_service):
        mock_get_service.return_value = MagicMock() # This mock might need to be associated with the context if get_authenticated_service is called within the CLI flow
        mock_get_vacation.return_value = {"enableAutoReply": True}
        # Changed invocation to use cli_entry
        result = self.runner.invoke(cli_entry.damien, ["emails", "email-settings", "get-vacation-settings"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"enableAutoReply": true', result.output)

    @patch("damien_cli.core_api.gmail_api_service.get_authenticated_service")
    @patch("damien_cli.core_api.gmail_api_service.update_vacation_settings")
    def test_update_vacation_settings_cmd(self, mock_update_vacation, mock_get_service):
        mock_get_service.return_value = MagicMock()
        mock_update_vacation.return_value = {"enableAutoReply": True}
        with self.runner.isolated_filesystem():
            with open("vacation.json", "w") as f:
                f.write('{"enableAutoReply": true}')
            result = self.runner.invoke(commands.update_vacation_settings_cmd, ["vacation.json"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"enableAutoReply": true', result.output)

    @patch("damien_cli.core_api.gmail_api_service.get_authenticated_service")
    @patch("damien_cli.core_api.gmail_api_service.enable_vacation_responder")
    def test_enable_vacation_responder_cmd(self, mock_enable_vacation, mock_get_service):
        mock_get_service.return_value = MagicMock()
        mock_enable_vacation.return_value = {"enableAutoReply": True}
        result = self.runner.invoke(commands.enable_vacation_responder_cmd)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"enableAutoReply": true', result.output)

    @patch("damien_cli.core_api.gmail_api_service.get_authenticated_service")
    @patch("damien_cli.core_api.gmail_api_service.disable_vacation_responder")
    def test_disable_vacation_responder_cmd(self, mock_disable_vacation, mock_get_service):
        mock_get_service.return_value = MagicMock()
        mock_disable_vacation.return_value = {"enableAutoReply": False}
        result = self.runner.invoke(commands.disable_vacation_responder_cmd)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"enableAutoReply": false', result.output)

    @patch("damien_cli.core_api.gmail_api_service.get_authenticated_service")
    @patch("damien_cli.core_api.gmail_api_service.get_imap_settings")
    def test_get_imap_settings_cmd(self, mock_get_imap, mock_get_service):
        mock_get_service.return_value = MagicMock()
        mock_get_imap.return_value = {"enabled": True}
        result = self.runner.invoke(commands.get_imap_settings_cmd)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"enabled": true', result.output)

    @patch("damien_cli.core_api.gmail_api_service.get_authenticated_service")
    @patch("damien_cli.core_api.gmail_api_service.update_imap_settings")
    def test_update_imap_settings_cmd(self, mock_update_imap, mock_get_service):
        mock_get_service.return_value = MagicMock()
        mock_update_imap.return_value = {"enabled": True}
        with self.runner.isolated_filesystem():
            with open("imap.json", "w") as f:
                f.write('{"enabled": true}')
            result = self.runner.invoke(commands.update_imap_settings_cmd, ["imap.json"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"enabled": true', result.output)

    @patch("damien_cli.core_api.gmail_api_service.get_authenticated_service")
    @patch("damien_cli.core_api.gmail_api_service.get_pop_settings")
    def test_get_pop_settings_cmd(self, mock_get_pop, mock_get_service):
        mock_get_service.return_value = MagicMock()
        mock_get_pop.return_value = {"accessWindow": "all_mail"}
        result = self.runner.invoke(commands.get_pop_settings_cmd)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"accessWindow": "all_mail"', result.output)

    @patch("damien_cli.core_api.gmail_api_service.get_authenticated_service")
    @patch("damien_cli.core_api.gmail_api_service.update_pop_settings")
    def test_update_pop_settings_cmd(self, mock_update_pop, mock_get_service):
        mock_get_service.return_value = MagicMock()
        mock_update_pop.return_value = {"accessWindow": "all_mail"}
        with self.runner.isolated_filesystem():
            with open("pop.json", "w") as f:
                f.write('{"accessWindow": "all_mail"}')
            result = self.runner.invoke(commands.update_pop_settings_cmd, ["pop.json"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"accessWindow": "all_mail"', result.output)

if __name__ == "__main__":
    unittest.main()