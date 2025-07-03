import asyncio
import json
from playwright.async_api import async_playwright

URL = "https://www.gucci.com/us/en/ca/women/handbags-c-women-handbags"

async def scrape_gucci_handbags():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
        )
        page = await context.new_page()
        await asyncio.sleep(2)
        await page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        print("Page loaded.")

        # Scroll and click "Load More" button until all products are loaded
        print("Starting JS scroll and Load More script...")
        await page.evaluate("""
        (async () => {
            let scrollCount = 0;
            let maxScrolls = 100; // Safety limit to prevent infinite loops
            let loadMoreSelector = '.cta.is-primary.ajax-loader-link.product-tiles-grid-load';

            function sleep(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
            }

            while (scrollCount < maxScrolls) {
                let loadMoreBtn = document.querySelector(loadMoreSelector);

                if (loadMoreBtn && !loadMoreBtn.disabled && loadMoreBtn.offsetParent !== null) { // Button is visible
                    console.log(`Clicking Load More button... [Scroll ${scrollCount + 1}]`);
                    loadMoreBtn.click();
                    await sleep(3000); // Wait for items to load
                } else {
                    console.log(`Scrolling... [Scroll ${scrollCount + 1}]`);
                    window.scrollBy(0, 5000);
                    await sleep(1000);
                    scrollCount++;
                }
            }

            console.log('Finished scrolling. Either maximum scrolls reached or no more Load More button.');
        })();
        """)
        await asyncio.sleep(10)
        print("Finished scrolling and loading more. Starting data extraction...")

        # Wait for all products to be loaded
        await page.wait_for_selector('div.product-tiles-grid-item-info', state="attached", timeout=60000)

        items = await page.query_selector_all('div.product-tiles-grid-item-info')
        print(f"Found {len(items)} items.")

        results = []
        for item in items:
            try:
                # Product name in h2 inside product-tiles-grid-item-info
                name_el = await item.query_selector('h2')
                name = (await name_el.inner_text()).strip() if name_el else ""

                # Price in .price .sale (if not found, try just .price)
                price_el = await item.query_selector('.price .sale') or await item.query_selector('.price')
                price = (await price_el.inner_text()).strip() if price_el else ""

                # Product link in a tag inside product-tiles-grid-item-info
                link_el = await item.query_selector('a')
                link = await link_el.get_attribute("href") if link_el else ""
                if link and not link.startswith("http"):
                    link = "https://www.gucci.com" + link

                results.append({
                    "name": name,
                    "price": price,
                    "product_url": link
                })
            except Exception as e:
                print("Error extracting item:", e)

        # Save to JSON
        with open("gucci.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(results)} items to gucci.json.")
        await browser.close()

async def main():
    await scrape_gucci_handbags()

if __name__ == "__main__":
    asyncio.run(main())