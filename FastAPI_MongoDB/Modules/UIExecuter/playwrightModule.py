from playwright.async_api import Page, async_playwright, expect
from FastAPI_MongoDB.SRC.Util import JsonOperations,GeneralFunctions
import os


class BaseFunctions:
    def __init__(self, page: Page):
        self.page = page

    async def PerformElementClick(self, Element):
        await self.page.locator(Element).click()

    async def PerformElelentSendKeys(self, Element, value):
        await self.page.locator(Element).fill(value)

    async def GetElementText(self, Element):
        text = await self.page.locator(Element).inner_text()
        return text.strip()

    async def IsElementvisible(self, locator):
        return await self.page.locator(locator).is_visible()

    async def FillElementText(self, Element, value):
        await self.page.locator(Element).fill(value)

    async def PageWait(self, value):
        await self.page.wait_for_timeout(value)

class BasePage:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def setup(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)

        self.page = await self.browser.new_page()
        await self.page.goto(self.GetBaseURL())
        await self.page.wait_for_timeout(5000)

    async def teardown(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def GetBaseURL(self):
        JIP = JsonOperations(GeneralFunctions.get_path("assets/Input.json"))
        JIPData = JIP.read_file()
        Product = JIPData['UIChecks']['UI_Product']
        Category = JIPData['UIChecks']['UI_Category']
        URL = None
        if Product and Category:
            if Product == "MPP":
                if Category == "TPT":
                    URL = JIPData['UIChecks']['MPP_TPT_URL']
                elif Category == "TPR":
                    URL = JIPData['UIChecks']['MPP_TPR_URL']
        return URL