import unittest
from rsgpt.graphs.worker_tool import repo_worker_g, specialist_on_langchain_g


class TestWorkerTool(unittest.TestCase):
    def test_repo_worker_tool_setup(self):
        self.assertIsNotNone(repo_worker_g)

    def test_specialist_on_langchain_tool_setup(self):
        self.assertIsNotNone(specialist_on_langchain_g)

    # Add more tool tests as needed


if __name__ == '__main__':
    unittest.main()