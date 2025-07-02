import os
from dotenv import load_dotenv
import uvicorn

# Load environment variables first, before importing logger
load_dotenv()

from src.lib.logger import logger  # noqa: E402


def main():
    logger.info("initializing healthcare-agent server")

    uvicorn.run(
        "src.app.server:app",
        host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=bool(os.getenv("RELOAD_ON_STARTUP", False)))


if __name__ == "__main__":
    main()
