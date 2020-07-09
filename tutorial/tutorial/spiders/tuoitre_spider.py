import json
import re
import time

import scrapy


class TuoiTreSpider(scrapy.Spider):
    name = 'tuoitre'

    def start_requests(self):
        self.site = 'https://tuoitre.vn'
        try:
            getattr(self, 'date')
        except AttributeError:
            now = time.localtime()
            self.date = str(now.tm_mday) + '-' + str(now.tm_mon) + '-' + str(now.tm_year)
        url = self.site + "/timeline-xem-theo-ngay/0/" + self.date + "/trang-1.htm"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        list = response.xpath('//h3[@class="title-news"]//a')
        topics = [{'title': l.xpath('./@title').get(),
                   'url': self.site + l.xpath('./@href').get(),
                   } for l in list if not re.match(r'^Video.*', l.xpath('./@title').get())]

        if topics:
            source = []
            try:
                with open('data/tuoitre-' + self.date + '.json', encoding='utf-8') as f:
                    data = json.load(f)
                    for sub in data:
                        source.append(sub['url'])
            except FileNotFoundError:
                pass

            stop = False
            for topic in topics:
                if topic['url'] in source:
                    stop = True
                    break
                yield scrapy.Request(topic['url'], callback=self.extract_json)
            if not stop:
                next_page = response.url[:-5] + str(int(response.url[-5]) + 1) + response.url[-4:]
                yield response.follow(next_page, callback=self.parse)

    def extract_json(self, response):
        data = {
            'site': self.site,
            'url': response.url,
            'category': response.xpath('//div[@class = "bread-crumbs fl"]//li[@class = "fl"]//a/@title').get(),
            'title': response.css('h1.article-title::text').get(),
            'summary': response.css('h2.sapo::text').get(),
            "content": response.css('div#main-detail-body p::text').getall(),
            "author": ''.join(response.css('.author::text').getall()).strip(),
            "images": [{'src:': img.xpath('./@src').get(),
                        'alt:': img.xpath('./@alt').get(), }
                       for img in
                       response.xpath('//div[@class="content fck"]//div[@type="Photo"]//img')],
            'videos': [{'src:': vid.xpath('./@data-src').get(),
                        'desc:': vid.xpath('.//div[@class="VideoCMS_Caption"]//p//text()').get(), }
                       for vid in
                       response.xpath('//div[@class="content fck"]//div[@type="VideoStream"]')],
        }

        try:
            with open('data/tuoitre-' + self.date + '.json', encoding='utf-8') as f:
                source = json.load(f)
        except FileNotFoundError:
            source = []
        with open('data/tuoitre-' + self.date + '.json', 'w', encoding='utf-8') as f:
            source.append(data)
            json.dump(source, f, ensure_ascii=False)
