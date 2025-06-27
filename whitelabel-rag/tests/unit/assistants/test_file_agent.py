"""
Tests for the FileAgent
"""
import pytest
import os
from unittest.mock import patch, MagicMock, mock_open

try:
    from app.services.file_agent import FileAgent
except ImportError as e:
    pytest.skip(f"Could not import app.services.file_agent: {e}")

class TestFileAgent:
    """Tests for the FileAgent"""
    
    def test_initialization(self):
        """Test basic initialization of FileAgent."""
        file_agent = FileAgent()
        assert file_agent.name == "FileAgent"
        assert hasattr(file_agent, "uploads_path")
    
    def test_list_files(self):
        """Test _list_files method."""
        file_agent = FileAgent()
        
        # Mock os.listdir and os.path.isfile
        mock_files = ["file1.pdf", "file2.docx", "file3.txt"]
        
        with patch('os.listdir', return_value=mock_files):
            with patch('os.path.isfile', return_value=True):
                # Call the method
                with patch.object(file_agent, 'report_success') as mock_success:
                    file_agent._list_files()
                    
                    # Verify report_success was called with the right content
                    mock_success.assert_called_once()
                    text = mock_success.call_args[0][0]
                    
                    # Check that all files are mentioned
                    for file in mock_files:
                        assert file in text
    
    def test_list_files_empty(self):
        """Test _list_files method with no files."""
        file_agent = FileAgent()
        
        # Mock os.listdir to return empty list
        with patch('os.listdir', return_value=[]):
            # Call the method
            with patch.object(file_agent, 'report_success') as mock_success:
                file_agent._list_files()
                
                # Verify report_success was called with the right content
                mock_success.assert_called_once()
                text = mock_success.call_args[0][0]
                
                # Check that "no files" message is returned
                assert "no files" in text.lower()
    
    def test_extract_file_path(self):
        """Test _extract_file_path method."""
        file_agent = FileAgent()
        
        # Test with no file mentioned
        no_file_msg = "What can you do?"
        assert file_agent._extract_file_path(no_file_msg) is None
        
        # Test with file mentioned
        file_msg = "Process the file document.pdf"
        
        # Mock os.path.exists and os.path.join
        with patch('os.path.exists', return_value=True):
            with patch('os.path.join', return_value="/path/to/document.pdf"):
                path = file_agent._extract_file_path(file_msg)
                assert path == "/path/to/document.pdf"
    
    def test_process_file(self):
        """Test _process_file method."""
        file_agent = FileAgent()
        
        # Create a mock file path
        file_path = "/path/to/document.pdf"
        message = "Extract text from document.pdf"
        
        # Mock file reading
        mock_file_content = "This is the content of the PDF file."
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            # Mock os.path.exists and os.path.getsize
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=1024):  # 1KB file
                    # Call the method
                    with patch.object(file_agent, 'report_success') as mock_success:
                        file_agent._process_file(file_path, message)
                        
                        # Verify report_success was called
                        mock_success.assert_called_once()
    
    def test_handle_message_list_files(self):
        """Test handle_message with a file listing request."""
        file_agent = FileAgent()
        
        # Mock the _list_files method
        with patch.object(file_agent, '_list_files') as mock_list:
            mock_list.return_value = {"text": "Here are your files: file1.pdf, file2.docx"}
            
            # Test handle_message
            result = file_agent.handle_message("List my files")
            
            # Verify _list_files was called
            mock_list.assert_called_once()
            
            # Verify result
            assert result["text"] == "Here are your files: file1.pdf, file2.docx"
    
    def test_handle_message_process_file(self):
        """Test handle_message with a file processing request."""
        file_agent = FileAgent()
        
        # Mock the _extract_file_path method
        with patch.object(file_agent, '_extract_file_path') as mock_extract:
            mock_extract.return_value = "/path/to/document.pdf"
            
            # Mock the _process_file method
            with patch.object(file_agent, '_process_file') as mock_process:
                mock_process.return_value = {"text": "Processed document.pdf"}
                
                # Test handle_message
                result = file_agent.handle_message("Process document.pdf")
                
                # Verify _extract_file_path was called
                mock_extract.assert_called_once_with("Process document.pdf")
                
                # Verify _process_file was called
                mock_process.assert_called_once_with("/path/to/document.pdf", "Process document.pdf")
    
    def test_handle_message_unknown_request(self):
        """Test handle_message with an unknown request."""
        file_agent = FileAgent()
        
        # Mock the _extract_file_path method to return None
        with patch.object(file_agent, '_extract_file_path', return_value=None):
            # Mock the report_failure method
            with patch.object(file_agent, 'report_failure') as mock_failure:
                mock_failure.return_value = {"text": "I'm not sure what file operation you want me to perform."}
                
                # Test handle_message
                result = file_agent.handle_message("Do something with files")
                
                # Verify report_failure was called
                mock_failure.assert_called_once()
                
                # Verify result
                assert "I'm not sure" in result["text"]
