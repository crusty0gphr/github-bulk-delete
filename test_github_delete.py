import unittest
import io
from unittest.mock import MagicMock, patch
from main import GitHubClient, GitHubError, parse_indices, confirm_deletion, run

class TestGitHubDelete(unittest.TestCase):

    def test_confirm_deletion_true(self):
        repos = [{"name": "repo1", "owner": {"login": "user1"}}]
        with patch('builtins.input', return_value='DELETE'):
            self.assertTrue(confirm_deletion(repos))
        
        # Test with spaces
        with patch('builtins.input', return_value='  DELETE  '):
            self.assertTrue(confirm_deletion(repos))

    def test_confirm_deletion_false(self):
        repos = [{"name": "repo1", "owner": {"login": "user1"}}]
        with patch('builtins.input', return_value='no'):
            self.assertFalse(confirm_deletion(repos))
        
        with patch('builtins.input', return_value='delete'): # Case sensitive
            self.assertFalse(confirm_deletion(repos))

    def test_parse_indices_valid(self):
        self.assertEqual(parse_indices("1,3,5-8", 10), [0, 2, 4, 5, 6, 7])
        self.assertEqual(parse_indices(" 1 , 3 , 5-8 ", 10), [0, 2, 4, 5, 6, 7])
        self.assertEqual(parse_indices("1,1,1", 10), [0])
        self.assertEqual(parse_indices("10,1", 10), [0, 9])
        self.assertEqual(parse_indices("1-3,2-4", 10), [0, 1, 2, 3])

    def test_parse_indices_out_of_range(self):
        self.assertEqual(parse_indices("11,12", 10), [])
        self.assertEqual(parse_indices("0,1,11", 10), [0])

    def test_parse_indices_invalid_format(self):
        self.assertIsNone(parse_indices("invalid", 10))
        self.assertIsNone(parse_indices("1,invalid", 10))
        self.assertIsNone(parse_indices("1-", 10))

    @patch('requests.Session')
    def test_github_client_get_repositories_success(self, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [[{"name": "repo1", "owner": {"login": "user1"}}], []]
        
        instance = mock_session.return_value
        instance.get.return_value = mock_response
        
        client = GitHubClient("fake_token")
        repos = client.get_repositories()
        
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]["name"], "repo1")
        instance.get.assert_called()

    @patch('requests.Session')
    def test_github_client_get_repositories_error(self, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Bad credentials"}
        
        instance = mock_session.return_value
        instance.get.return_value = mock_response
        
        client = GitHubClient("fake_token")
        with self.assertRaises(GitHubError) as cm:
            client.get_repositories()
        self.assertIn("401", str(cm.exception))
        self.assertIn("Bad credentials", str(cm.exception))

    @patch('requests.Session')
    def test_github_client_delete_repository_success(self, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 204
        
        instance = mock_session.return_value
        instance.delete.return_value = mock_response
        
        client = GitHubClient("fake_token")
        result = client.delete_repository("owner", "repo")
        self.assertTrue(result)
        instance.delete.assert_called_with("https://api.github.com/repos/owner/repo", timeout=10)

    @patch('requests.Session')
    def test_github_client_delete_repository_failure(self, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        instance = mock_session.return_value
        instance.delete.return_value = mock_response
        
        client = GitHubClient("fake_token")
        result = client.delete_repository("owner", "repo")
        self.assertFalse(result)

    def test_run_keyboard_interrupt(self):
        with patch('main.main', side_effect=KeyboardInterrupt):
            with patch('sys.exit') as mock_exit:
                with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                    run()
                    self.assertIn("Operation cancelled by user", mock_stdout.getvalue())
                    mock_exit.assert_called_with(0)

if __name__ == '__main__':
    unittest.main()
