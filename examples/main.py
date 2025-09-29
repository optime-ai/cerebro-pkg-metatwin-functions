"""Main entry point for running the function server with example functions."""

import sys
import os

# Add parent directory to path to import functions module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions_core import FunctionServer
from functions_core.logging import get_logger

# Import the example functions module to register them
import simple_function  # This import registers all decorated functions

# Setup logger
logger = get_logger(__name__)

# Create server instance at module level for uvicorn
server = FunctionServer()
app = server.app  # This is what uvicorn will use

def main():
    """Main function to start the server."""
        
    # Start the server with uvicorn using module-level app
    try:
        import uvicorn
        # Separate uvicorn log level from app log level
        uvicorn_log_level = os.getenv('CRBR_UVICORN_LOG_LEVEL', 'ERROR').lower()
        
        uvicorn.run(
            app,
            host=os.getenv('CRBR_FUNCTIONS_HOST', '0.0.0.0'),
            port=int(os.getenv('CRBR_FUNCTIONS_PORT', '8000')),
            log_level=uvicorn_log_level,
            reload=False
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


if __name__ == "__main__":
    main()