import unittest
from rsgpt.graphs.repo_worker import RepoWorker


class TestRepoWorker(unittest.TestCase):
    def test_integration(self):
        worker = RepoWorker()
        self.assertIsNotNone(worker)

    # Add more tests focusing on Repo interaction, error handling


if __name__ == '__main__':
    unittest.main()