import os
from typing import Tuple

def validate_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate a file for processing.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if file exists
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
        
    # Check file extension
    if not file_path.lower().endswith('.txt'):
        return False, "Only .txt files are supported"
        
    # Check file size (5MB limit)
    file_size = os.path.getsize(file_path)
    if file_size > 5 * 1024 * 1024:  # 5MB in bytes
        return False, "File size exceeds 5MB limit"
        
    # Check if file is readable
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # Try reading first 1KB
    except UnicodeDecodeError:
        return False, "File must be UTF-8 encoded"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
        
    return True, ""

