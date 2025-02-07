import unittest
from rsgpt.tools import Document


class TestTools(unittest.TestCase):
    def test_document_initialization(self):
        doc = Document()
        self.assertIsInstance(doc, Document)

    # Add more tests for tool functions and their outputs


if __name__ == '__main__':
    unittest.main()