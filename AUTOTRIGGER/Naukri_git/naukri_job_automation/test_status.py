"""Quick test script to verify the application status scraper works."""
import asyncio
from src.naukri_bot import NaukriBot

async def test_status():
    print("Starting browser and logging in...")
    bot = NaukriBot(headless=False)
    await bot.start()
    
    try:
        logged_in = await bot.login()
        if not logged_in:
            print("❌ Login failed")
            return
        
        print("✅ Logged in successfully")
        print("\nScraping application status page...")
        print("This will take 30-60 seconds while scrolling through all applications...")
        
        apps = await bot.scrape_application_status_page()
        
        print(f"\n✅ Scraped {len(apps)} applications!")
        
        if apps:
            print("\n📊 Sample application:")
            sample = apps[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
            
            # Count by status
            status_counts = {}
            for app in apps:
                status = app.get("status", "applied")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print("\n📈 Status breakdown:")
            for status, count in sorted(status_counts.items()):
                print(f"  {status}: {count}")
        
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_status())
