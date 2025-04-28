import unittest
import os
import sys
from unittest.mock import Mock, patch
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_document_processor import DocumentProcessor

class TestDocumentProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.processor = DocumentProcessor()
        
    def test_process_document(self):
        """Test basic document processing functionality."""
        test_doc = "This is a test document"
        with patch('enhanced_document_processor.process_text') as mock_process:
            mock_process.return_value = {"processed": "test result"}
            result = self.processor.process_document(test_doc)
            self.assertIsNotNone(result)
            mock_process.assert_called_once_with(test_doc)
            
    def test_document_validation(self):
        """Test document validation checks."""
        with self.assertRaises(ValueError):
            self.processor.process_document(None)
        with self.assertRaises(ValueError):
            self.processor.process_document("")
            
    def test_data_processing(self):
        """Test data processing and transformation."""
        test_data = {"key": "value"}
        with patch('enhanced_document_processor.transform_data') as mock_transform:
            mock_transform.return_value = {"transformed": "data"}
            result = self.processor.process_data(test_data)
            self.assertIsNotNone(result)
            self.assertIn("transformed", result)

if __name__ == '__main__':
    unittest.main() 