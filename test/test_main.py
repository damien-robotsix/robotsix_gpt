import unittest
from unittest.mock import patch
from rsgpt.main import main


class TestMain(unittest.TestCase):
    @patch('builtins.input', side_effect=['exit'])
    def test_main_execution(self, mock_input):
        with self.assertRaises(SystemExit):
            main()

    # More tests can invoke parts of the main method logic


if __name__ == '__main__':
    unittest.main()