import unittest
from rsgpt.utils.git import get_repo_root
from unittest.mock import patch


class TestGitUtils(unittest.TestCase):
    @patch('subprocess.check_output')
    def test_get_repo_root(self, mock_check_output):
        mock_check_output.return_value = b'/path/to/repo\n'
        self.assertEqual(get_repo_root(), '/path/to/repo')

    # Add more tests for exception handling


if __name__ == '__main__':
    unittest.main()