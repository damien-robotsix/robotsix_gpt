import unittest
from rsgpt.graphs.specialist_with_memory import SpecialistWithMemoryState


class TestSpecialistWithMemoryState(unittest.TestCase):
    def test_initialization(self):
        state = SpecialistWithMemoryState()
        self.assertIsInstance(state, SpecialistWithMemoryState)

    # Add more tests related to memory handling


if __name__ == '__main__':
    unittest.main()