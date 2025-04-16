from playwright.sync_api import sync_playwright

def launch_browser():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(accept_downloads=True)
    return playwright, browser, context
