from typing import Callable, Dict, Optional
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class ChunkingMethodRegistry:
    """Registry for mapping chunking method names to their implementation functions."""
    
    def __init__(self):
        self._methods: Dict[str, Callable] = {}
        
    def register(self, method_name: str) -> Callable:
        """Decorator to register a chunking method.
        
        Args:
            method_name: Name of the chunking method to register
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
                
            self._methods[method_name] = wrapper
            logger.info(f"Registered chunking method: {method_name}")
            return wrapper
            
        return decorator
        
    def get_method(self, method_name: str) -> Callable:
        """Get a registered chunking method by name.
        
        Args:
            method_name: Name of the chunking method to retrieve
            
        Returns:
            The chunking method function
            
        Raises:
            ValueError: If the requested chunking method is not registered
        """
        method = self._methods.get(method_name)
        if method is None:
            available_methods = ", ".join(sorted(self._methods.keys()))
            raise ValueError(
                f"Chunking method '{method_name}' not found. "
                f"Available methods: {available_methods}"
            )
        return method
        
    def list_methods(self) -> list[str]:
        """List all registered chunking method names.
        
        Returns:
            List of registered method names
        """
        return list(self._methods.keys())
        
    def log_registered_methods(self) -> None:
        """Log all registered chunking methods at startup."""
        methods = sorted(self._methods.keys())
        if methods:
            logger.info("Registered chunking methods:")
            for method in methods:
                logger.info(f"  - {method}")
        else:
            logger.warning("No chunking methods registered")

# Create global registry instance
registry = ChunkingMethodRegistry()

# Log registered methods at module import
registry.log_registered_methods() 