import unittest
from rsgpt.utils.git import get_repo_root
from unittest.mock import patch
from setup_fake_git import setup_fake_git_directory
import shutil
from pathlib import Path

class TestGitUtils(unittest.TestCase):
    def setUp(self):
        # Set up a fake git directory before each test
        self.fake_git_dir = setup_fake_git_directory()

    def tearDown(self):
        # Clean up after each test
        shutil.rmtree(self.fake_git_dir)

    @patch('subprocess.check_output')
    def test_get_repo_root(self, mock_check_output):
        # Mock subprocess to return the path of the fake git directory
        mock_check_output.return_value = f'{self.fake_git_dir}\n'.encode('utf-8')
        self.assertEqual(get_repo_root(), Path(self.fake_git_dir))

if __name__ == '__main__':
    unittest.main()