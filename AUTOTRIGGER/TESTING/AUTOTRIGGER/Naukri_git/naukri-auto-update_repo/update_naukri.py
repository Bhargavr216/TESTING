import asyncio
import sys
from pathlib import Path

# Add the project root to sys.path if running as a script
sys.path.append(str(Path(__file__).parent))

from src.naukri_bot import NaukriBot
from src.utils import log_info, log_error

async def main():
    """Standalone script to update Naukri profile using the project's bot class."""
    bot = NaukriBot(headless=False)
    try:
        await bot.start()
        if not await bot.login():
            log_error("Login failed. Check your config/profile.yaml and environment variables.")
            return
        
        success = await bot.update_profile()
        if success:
            log_info("Profile update completed successfully via standalone script.")
        else:
            log_error("Profile update failed.")
        
        # Also handle early access while we are at it
        await bot.handle_early_access()
            
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
