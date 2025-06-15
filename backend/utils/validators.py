import os
import logging
from pathlib import Path
from typing import Union, List

# Configure logging
logger = logging.getLogger(__name__)

# Maximum file sizes (in bytes)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PDF_SIZE = 5 * 1024 * 1024    # 5MB
MAX_TXT_SIZE = 1 * 1024 * 1024    # 1MB

# Allowed file types
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.csv'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'text/plain',
    'text/csv'
}

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    logger.warning("python-magic not available. MIME type validation will be skipped.")
    MAGIC_AVAILABLE = False

def validate_file(file_path: Union[str, Path]) -> bool:
    """Validate a file for ingestion.
    
    Args:
        file_path: Path to the file to validate.
        
    Returns:
        bool: True if file is valid, False otherwise.
    """
    file_path = Path(file_path)
    
    try:
    # Check if file exists
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return False
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large ({file_size} bytes): {file_path}")
            return False
        
    # Check file extension
        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            logger.warning(f"Invalid file extension: {file_path}")
            return False
        
        # Check MIME type if magic is available
        if MAGIC_AVAILABLE:
            try:
                mime = magic.Magic(mime=True)
                file_mime = mime.from_file(str(file_path))
                if file_mime not in ALLOWED_MIME_TYPES:
                    logger.warning(f"Invalid MIME type {file_mime}: {file_path}")
                    return False
            except Exception as e:
                logger.warning(f"Error checking MIME type for {file_path}: {str(e)}")
                return False
        
        # Check specific file type size limits
        if file_path.suffix.lower() == '.pdf' and file_size > MAX_PDF_SIZE:
            logger.warning(f"PDF file too large ({file_size} bytes): {file_path}")
            return False
        if file_path.suffix.lower() == '.txt' and file_size > MAX_TXT_SIZE:
            logger.warning(f"Text file too large ({file_size} bytes): {file_path}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating file {file_path}: {str(e)}")
        return False

def validate_directory(directory: Union[str, Path]) -> List[Path]:
    """Validate all files in a directory.
    
    Args:
        directory: Path to the directory to validate.
        
    Returns:
        List of valid file paths.
    """
    directory = Path(directory)
    valid_files = []
    
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return valid_files
    
    try:
        for file_path in directory.glob("**/*"):
            if file_path.is_file() and validate_file(file_path):
                valid_files.append(file_path)
    except Exception as e:
        logger.error(f"Error validating directory {directory}: {str(e)}")
        
    return valid_files

