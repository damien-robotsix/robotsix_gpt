import unittest
from rsgpt.graphs.dispatcher import DispatcherState


class TestDispatcherState(unittest.TestCase):
    def test_initialization(self):
        state = DispatcherState()
        self.assertIsInstance(state, DispatcherState)

    # Add more tests related to its functions and data handling


if __name__ == '__main__':
    unittest.main()