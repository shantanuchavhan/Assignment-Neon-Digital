# Requirements: pip install playwright && playwright install

import asyncio
from playwright.async_api import async_playwright
import json

import asyncio
from playwright.async_api import async_playwright
import json



# clean title
import re
import html

def clean_title(title):
    try:
        title = title.encode('utf-16', 'surrogatepass').decode('utf-16')  # decode emoji
    except:
        pass
    title = re.sub(r'[^\w\s.,!?()\-:]', '', title)  # remove emojis/symbols
    title = html.unescape(title)  # unescape HTML characters
    return title.strip()

# Reddit web scrapping
async def scrape_reddit():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36")
        await page.goto("https://www.reddit.com/r/Python/", timeout=60000)

   
        try:
            await page.click("button:has-text('Accept All')")
            await asyncio.sleep(1)
        except:
            pass

        print("🔄 Scrolling and collecting posts...")
        collected_urls = set()
        results = []

        previous_height = 0
        retries = 0

        while retries < 5 and len(results) < 100:
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await asyncio.sleep(2.5)

            posts = await page.query_selector_all("article")

            for post in posts:
                if len(results) >= 100:
                    break
                try:
                    # Get URL first to check uniqueness
                    link_el = await post.query_selector('a[slot="title"]')
                    url = await link_el.get_attribute("href") if link_el else None
                    if url and url.startswith("/"):
                        url = "https://www.reddit.com" + url
                    if not url or url in collected_urls:
                        continue
                    collected_urls.add(url)

                    # Title
                    raw_title = await link_el.inner_text() if link_el else None
                    title = clean_title(raw_title) if raw_title else None

                    # Author
                    author_el = await post.query_selector("a[href*='/user/']")
                    author = await author_el.inner_text() if author_el else None
                    author = author.replace("u/", "") if author else None


                    # Upvotes
                    upvote_el = await post.query_selector('span[data-post-click-location="vote"] faceplate-number')
                    upvotes = await upvote_el.inner_text() if upvote_el else "0"

                    # Comments
                    comments_el = await post.query_selector('a[data-post-click-location="comments-button"] faceplate-number')
                    comments = await comments_el.inner_text() if comments_el else "0 comments"

                    # Time
                    time_el = await post.query_selector("time")
                    time = await time_el.inner_text() if time_el else None

                    if title:
                        results.append({
                            "title": title,
                            "author": author,
                            "upvotes": upvotes,
                            "comments": comments,
                            "url": url,
                            "time": time
                        })

                except Exception as e:
                    print(f"❌ Error parsing post: {e}")
                    continue

            # Scroll logic
            current_height = await page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                retries += 1
            else:
                retries = 0
            previous_height = current_height

        await browser.close()

        with open("reddit_python_posts_playwright.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"✅ Scraped {len(results)} posts saved to reddit_python_posts_playwright.json")








import asyncio
from playwright.async_api import async_playwright
import json

import asyncio
from playwright.async_api import async_playwright
import json


# Youtube Web scraping
async def scrape_youtube():
    search_keywords = ["Python Tutorial", "AI", "Agents"]
    video_data = []

    async with async_playwright() as p:
        for keyword in search_keywords:
            browser = await p.chromium.launch(headless=False)  # Set to True for headless mode
            page = await browser.new_page()
            await page.goto("https://www.youtube.com")
            await asyncio.sleep(3)

            await page.fill('input[name="search_query"]', keyword)
            await page.press('input[name="search_query"]', "Enter")
            await asyncio.sleep(5)

            collected = []
            scroll_attempts = 0
            max_scrolls = 20

            while len(collected) < 50 and scroll_attempts < max_scrolls:
                videos = await page.query_selector_all("ytd-video-renderer")

                for video in videos:
                    if len(collected) >= 50:
                        break

                    try:
                        title_el = await video.query_selector("#video-title")
                        channel_el = await video.query_selector("#channel-info #text")
                        metadata_spans = await video.query_selector_all("#metadata span.inline-metadata-item")

                        raw_title = await title_el.inner_text() if title_el else None
                        title = clean_title(raw_title) if raw_title else None
                        url = await title_el.get_attribute("href") if title_el else None
                        if url and url.startswith("/"):
                            url = "https://www.youtube.com" + url

                        channel = await channel_el.inner_text() if channel_el else None
                        views = await metadata_spans[0].inner_text() if len(metadata_spans) > 0 else None
                        date = await metadata_spans[1].inner_text() if len(metadata_spans) > 1 else None

                        if title and url and channel and views and date:
                            if not any(v["url"] == url for v in collected):
                                collected.append({
                                    "search_term": keyword,
                                    "title": title,
                                    "url": url,
                                    "channel": channel,
                                    "views": views,
                                    "date": date
                                })
                    except Exception as e:
                        continue

                await page.mouse.wheel(0, 3000)
                await asyncio.sleep(2)
                scroll_attempts += 1

            print(f"✅ Collected {len(collected)} videos for '{keyword}'")
            video_data.extend(collected)
            await browser.close()

    with open("youtube_videos_playwright.json", "w", encoding="utf-8") as f:
        json.dump(video_data, f, indent=2)

    print("🎉 YouTube scraping complete. Saved to youtube_videos_playwright.json")








# Run both scrapers
if __name__ == "__main__":
    asyncio.run(scrape_reddit())
    asyncio.run(scrape_youtube())