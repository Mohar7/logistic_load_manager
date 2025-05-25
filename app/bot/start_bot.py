# app/bot/start_bot.py - Startup script
#!/usr/bin/env python3
import asyncio
import logging
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bot.main import main

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting Logistics Telegram Bot...")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)
