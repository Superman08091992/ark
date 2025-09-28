import os
from playwright.sync_api import sync_playwright
from selenium import webdriver

class KyleAgent:
    def __init__(self):
        self.polygon_key = os.getenv("POLYGON_KEY")

    def ingest_data(self, sources):
        print(f"Kyle ingesting from: {sources}")
        if "market" in sources and self.polygon_key:
            return {"data": "pulled from Polygon"}
        return {"data": "no sources"}

    def scrape_with_playwright(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            content = page.content()
            browser.close()
        return content

    def scrape_with_selenium(self, url):
        driver = webdriver.Chrome(os.getenv("SELENIUM_DRIVER_PATH"))
        driver.get(url)
        content = driver.page_source
        driver.quit()
        return content

    def package_for_joey(self, request):
        return {"package": f"data_and_request for {request}"}
