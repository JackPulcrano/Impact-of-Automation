""" 
This script uses Playwright to scrape web pages for PDF download links.
It leverages OpenAI's GPT model to suggest selectors for downloading PDFs.
"""

import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import openai
import asyncio
from openai import OpenAI
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # Load secrets from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Get the path to the current notebook
notebook_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
# Navigate to the file: one level up, then into datasets
CSV_PATH = notebook_dir.parent / "datasets" / "open_access_enriched.csv"

# === CONFIGURATION ===
PDF_DIR = "papers_6"
os.makedirs(PDF_DIR, exist_ok=True)
openai.api_key = OPENAI_API_KEY 
client = OpenAI(api_key=OPENAI_API_KEY)


# === GPT INSTRUCTION TEMPLATE ===
GPT_PROMPT_TEMPLATE = """
You are a web-scraping agent trying to find the PDF download button or link on an HTML page.

Here is the raw HTML content of a web page. Based on this HTML, identify the most likely selector I should use to click a button or link that would trigger the download of a PDF of a scientific paper.

Respond with the Playwright selector I should click to view or download pdf, such as:
  - text="Download"
  - a[href*="pdf"]
  - button:has-text("View PDF")
If no clear PDF download link is visible, respond with: NONE

HTML:
----------------
{html_snippet}
"""


async def gpt_suggest_selector(html):
    prompt = GPT_PROMPT_TEMPLATE.format(html_snippet=html[:5000]) 
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or gpt-4 if available
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        selector = response.choices[0].message.content.strip()
        return selector if selector and selector != "NONE" else None
    except Exception as e:
        print("❌ GPT error:", e)
        return None


async def download_with_playwright():
    df = pd.read_csv(CSV_PATH)
    success, fail = 0, 0
    failed_rows = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        for idx, row in df.iterrows():
            doi = row["DOI"]
            url = row.get("Open Access URL", None)
            filename = os.path.join(PDF_DIR, doi.replace("/", "_") + ".pdf")

            if not isinstance(url, str) or not url.startswith("http"):
                fail += 1
                failed_rows.append((doi, url, "Invalid URL"))
                continue

            try:
                await page.goto(url, timeout=20000, wait_until="networkidle")
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(1500)  # Add a 1.5s buffer for late JS

                html = await page.content()
                selector = await gpt_suggest_selector(html)
                if selector:
                    try:
                        with page.expect_download(timeout=15000) as download_info:
                            await page.click(selector)
                        download = await download_info.value
                        await download.save_as(filename)
                        print(f"✅ {idx}: Downloaded PDF for {doi}")
                        success += 1
                    except Exception as click_error:
                        print(f"⚠️ {idx}: Selector failed for {doi}: {click_error}")
                        failed_rows.append((doi, url, "Selector error"))
                        fail += 1
                else:
                    print(f"❌ {idx}: GPT couldn't find selector for {doi}")
                    failed_rows.append((doi, url, "No selector"))
                    fail += 1
            except Exception as e:
                print(f"❌ {idx}: Page error for {doi}: {e}")
                failed_rows.append((doi, url, "Page load error"))
                fail += 1

            if idx % 10 == 0:
                print(f"\n📊 Progress: {idx}/{len(df)} | ✅ {success} | ❌ {fail}")

        await browser.close()

    # Save failures
    fail_df = pd.DataFrame(failed_rows, columns=["DOI", "URL", "Reason"])
    # fail_df.to_csv("failed_downloads.csv", index=False)
    print(f"\n📥 Download complete: {success} success, {fail} failed.")
    print("Failures saved to datasets/failed_downloads.csv")

# Run
if __name__ == "__main__":
    asyncio.run(download_with_playwright())
