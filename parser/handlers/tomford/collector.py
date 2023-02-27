import asyncio
import re
from csv import DictWriter

import aiocsv
import aiofiles
from aiohttp import ClientSession, TCPConnector
from bs4 import BeautifulSoup


class ParserTomford:

    def __init__(self, url: str, bar, create_csv=True):
        self.rate_sem = asyncio.BoundedSemaphore(30)
        self.product_list_links = []
        self.url = url
        self.bar = bar
        self.fieldnames = ['title', 'details', 'color', 'images']

        if create_csv:
            self.init_csv()

    def init_csv(self):
        with open(f'./parser/tomford/csv/{self.url.split("women/")[1]}.csv',
                  'w') as file:
            writer = DictWriter(file, fieldnames=self.fieldnames, delimiter=';')
            writer.writeheader()

    async def create_csv(self, title, details, color, images):
        async with aiofiles.open(
                f'./parser/tomford/csv/{self.url.split("women/")[1]}.csv',
                mode='a', encoding='utf-8') as file:
            writer = aiocsv.AsyncDictWriter(file, fieldnames=self.fieldnames, delimiter=';')
            await writer.writerow({
                "title": title,
                "details": details,
                "color": color,
                "images": images

            })
        self.bar()
        await asyncio.sleep(0.5)

    async def delay_wrapper(self, task):
        await self.rate_sem.acquire()
        return await task

    async def releaser(self):
        while True:
            await asyncio.sleep(0.05)
            try:
                self.rate_sem.release()
            except ValueError:
                pass

    async def main(self):
        await self.get_links()
        rt = asyncio.create_task(self.releaser())
        await asyncio.gather(
            *[self.delay_wrapper(self.collect(link)) for link in self.product_list_links])
        rt.cancel()

    async def get_links(self):
        async with ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
            async with session.get(self.url) as main_response:
                main_soup = BeautifulSoup(await main_response.text(), "lxml")
                self.product_list_links = main_soup.find_all('a', class_="overlay-link")
        self.product_list_links

    async def get_more_detail(self, soup, link):
        try:
            title = re.sub(" +", " ", soup.select_one("#collapseTwo > div").text.replace('\n\n', ''))
        except BaseException as e:
            title = "--"
        await asyncio.sleep(0.5)
        return title

    async def collect(self, link):
        async with ClientSession() as session:
            async with session.get(link.attrs['href']) as response:
                soup = BeautifulSoup(await response.text(), 'lxml')
        title = re.sub(" +", " ", soup.find('h1', class_="product-name").text)
        details = await self.get_more_detail(soup, link)
        color = re.sub(" +", " ", soup.find('span', class_="selected-value").text)
        # all_image = soup.find_all('img', class_="primary-image")
        # images = {'photos': []}
        images = [link.attrs['src'] for link in soup.find_all('img', class_="primary-image")]
        # images['photos'].extend(
            # [image.get('src').split("?")[0] if not "data:image" in image.get('src') else
             # image.get('data-src').split("?")[0] for image in
             # all_image])
        await self.create_csv(title, details, color, images)
