"""Trendyol API endpoint keşfi."""
import asyncio
import json
from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth


async def debug():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    ctx = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="tr-TR",
        timezone_id="Europe/Istanbul",
    )
    page = await ctx.new_page()
    stealth = Stealth()
    await stealth.apply_stealth_async(page)

    # Listen for all API requests
    api_responses = []

    async def on_response(response):
        url = response.url
        if "product" in url.lower() or "sfint" in url.lower() or "detail" in url.lower():
            try:
                body = await response.text()
                api_responses.append({
                    "url": url[:200],
                    "status": response.status,
                    "body_preview": body[:500] if body else None,
                })
            except:
                api_responses.append({"url": url[:200], "status": response.status, "body_preview": "FAILED"})

    page.on("response", on_response)

    print("Navigating...")
    await page.goto(
        "https://www.trendyol.com/apple/iphone-15-128-gb-p-782425137",
        wait_until="load",
        timeout=30000,
    )
    await asyncio.sleep(5)

    # Also try the API directly via page.context.request
    print("Trying API endpoints...")
    api_urls = [
        "https://public.trendyol.com/discovery-sfint-productgw-service/api/productDetail/782425137",
        "https://public-mdc.trendyol.com/discovery-sfint-productgw-service/api/productDetail/782425137",
        "https://apigw.trendyol.com/discovery-sfint-productgw-service/api/productDetail/782425137",
    ]

    for api_url in api_urls:
        try:
            resp = await ctx.request.get(api_url, headers={
                "Accept": "application/json",
                "storefrontId": "1",
                "culture": "tr-TR",
                "Referer": "https://www.trendyol.com/",
                "Origin": "https://www.trendyol.com",
            })
            body = await resp.text()
            api_responses.append({
                "url": api_url,
                "status": resp.status,
                "body_preview": body[:500],
            })
            print(f"  {resp.status}: {api_url}")
        except Exception as e:
            print(f"  ERROR: {api_url} → {e}")

    # Also try fetching from page JS with same origin
    try:
        js_result = await page.evaluate("""async () => {
            const urls = [
                '/api/productDetail/782425137',
                'https://public.trendyol.com/discovery-sfint-productgw-service/api/productDetail/782425137',
            ];
            const results = [];
            for (const url of urls) {
                try {
                    const r = await fetch(url, { headers: { 'storefrontId': '1', 'culture': 'tr-TR' }});
                    const text = await r.text();
                    results.push({ url, status: r.status, body: text.substring(0, 300) });
                } catch(e) {
                    results.push({ url, error: e.message });
                }
            }
            return results;
        }""")
        api_responses.append({"source": "page_fetch", "results": js_result})
    except Exception as e:
        print(f"  JS fetch error: {e}")

    with open("api_debug.json", "w", encoding="utf-8") as f:
        json.dump(api_responses, f, ensure_ascii=False, indent=2)

    print(f"Done! Found {len(api_responses)} API responses. Check api_debug.json")

    await browser.close()
    await pw.stop()


asyncio.run(debug())
