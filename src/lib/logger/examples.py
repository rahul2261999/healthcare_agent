"""
Example usage of the configured loguru logger.
"""

from . import logger

def demonstrate_logger():
    """Demonstrate different logging methods."""
    
    # Basic logging examples
    logger.info("This is an info message")
    logger.error("This is an error message")
    logger.warning("This is a warning message")
    logger.debug("This is a debug message")
    logger.success("This is a success message")
    logger.critical("This is a critical message")
    
    # Exception logging example
    try:
        1/0
    except Exception as e:
        logger.exception("An error occurred while dividing by zero")

if __name__ == "__main__":
    demonstrate_logger() 