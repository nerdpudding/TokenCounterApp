"""Tests for the token counter package."""

import os
import tempfile
import pytest
from pathlib import Path
from codebase_token_counter.token_counter import (
    count_tokens,
    is_binary,
    format_number,
    FILE_EXTENSIONS
)

def test_token_counting():
    """Test token counting functionality."""
    # Test basic token counting
    assert count_tokens("Hello, world!") > 0
    
    # Test empty string
    assert count_tokens("") == 0
    
    # Test whitespace
    assert count_tokens("   ") > 0
    
    # Test code snippet
    code = """
    def hello_world():
        print("Hello, world!")
    """
    assert count_tokens(code) > 0

def test_binary_file_detection():
    """Test binary file detection."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        # Write some text
        f.write(b"Hello, world!")
        text_path = f.name
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        # Write some binary data
        f.write(bytes(range(256)))
        binary_path = f.name
    
    try:
        assert not is_binary(text_path)
        assert is_binary(binary_path)
    finally:
        # Clean up
        os.unlink(text_path)
        os.unlink(binary_path)

def test_number_formatting():
    """Test number formatting functionality."""
    assert format_number(1000) == "1,000"
    assert format_number(1000000) == "1.0M"
    assert format_number(1500000) == "1.5M"
    assert format_number(1000000000) == "1.0B"
    assert format_number(0) == "0"

def test_file_extensions():
    """Test file extension mappings."""
    # Test common extensions
    assert FILE_EXTENSIONS[".py"] == "Python"
    assert FILE_EXTENSIONS[".js"] == "JavaScript"
    assert FILE_EXTENSIONS[".md"] == "Markdown"
    
    # Test case sensitivity
    assert ".py" in FILE_EXTENSIONS
    assert ".PY" not in FILE_EXTENSIONS
    
    # Test extension completeness
    assert len(FILE_EXTENSIONS) > 10  # Should have many extensions
    assert all(ext.startswith(".") for ext in FILE_EXTENSIONS)  # All should start with dot

def test_total_only_mode(capsys):
    """Test the -total flag functionality."""
    import sys
    from codebase_token_counter.token_counter import process_repository
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"Hello, world!")
        test_path = f.name
    
    try:
        # Test with total_only=True
        total_tokens, _, _ = process_repository(os.path.dirname(test_path), total_only=True)
        assert total_tokens > 0
        
        # Test with total_only=False
        total_tokens, _, _ = process_repository(os.path.dirname(test_path), total_only=False)
        assert total_tokens > 0
    finally:
        # Clean up
        os.unlink(test_path)
