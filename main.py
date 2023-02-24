import asyncio

from alive_progress import alive_bar

from parser.handlers.tomford.collector import ParserTomford


class TotalParse:

    def __init__(self):
        self.total_links = 0
        self.zilli_tasks = []
        self.dior_tasks = []
        self.links_tomford = ["https://www.tomford.com/women/handbags", "https://www.tomford.com/women/shoes",
                              "https://www.tomford.com/women/accessories"]

    async def start_zilli(self, bar):
        for link_tomford in self.links_tomford:
            task_tomford = ParserTomford(link_tomford, bar)
            self.zilli_tasks.append(asyncio.create_task(task_tomford.main()))
        await asyncio.gather(*self.zilli_tasks)

    async def total_start(self, site):
        for link in self.links_tomford:
            task_tomford = ParserTomford(link, None, False)
            await task_tomford.get_links()
            self.total_links += len(task_tomford.product_list_links)
            del task_tomford
        with alive_bar(self.total_links, title='Процесс сбора с сайта \"Tomford\"', theme='smooth') as bar:
            main_task = [asyncio.create_task(self.start_zilli(bar))]
            await asyncio.gather(*main_task)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    total_parser = TotalParse()
    loop.run_until_complete(total_parser.total_start("tomford"))
    loop.close()
