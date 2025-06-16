import unittest
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def run_tests():
    """Run all vector service tests in the correct order."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add tests in order of dependencies
    test_files = [
        'test_chunkers.py',      # Test chunking first as it's the first step
        'test_embedders.py',     # Test embedding next
        'test_storage.py',       # Test storage functionality
        'test_summarizer.py',    # Test summarization
        'test_evaluator.py',     # Test evaluation
        'test_pipeline.py'       # Test full pipeline last
    ]
    
    # Get the directory containing this script
    test_dir = Path(__file__).parent
    
    # Load and add tests from each file
    for test_file in test_files:
        logger.info(f"Loading tests from {test_file}")
        try:
            # Load tests from file
            loader = unittest.TestLoader()
            tests = loader.discover(test_dir, pattern=test_file)
            suite.addTest(tests)
        except Exception as e:
            logger.error(f"Failed to load tests from {test_file}: {e}")
            raise
    
    # Run tests
    logger.info("Starting test suite")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Report results
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    # Return non-zero exit code if tests failed
    return len(result.failures) + len(result.errors)

if __name__ == '__main__':
    sys.exit(run_tests()) 