import json
import re
import time

import scrapy


class VnExpressSpider(scrapy.Spider):
    name = 'vnexpress'

    def start_requests(self):
        self.site = 'https://vnexpress.net'
        try:
            getattr(self, 'date')
        except AttributeError:
            now = time.localtime()
            self.date = str(now.tm_mday) + '-' + str(now.tm_mon) + '-' + str(now.tm_year)
        url = self.site + "/tin-tuc-24h"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        list = response.xpath('//h3[@class="title-news"]/a')
        topics = [{'title': l.xpath('./@title').get(),
                   'url': l.xpath('./@href').get(),
                   } for l in list if not re.match(r'^https://video.*', l.xpath('./@href').get())]

        if topics:
            source = []
            try:
                with open('data/vnexpress-' + self.date + '.json', encoding='utf-8') as f:
                    data = json.load(f)
                    for sub in data:
                        source.append(sub['url'])
            except FileNotFoundError:
                pass

            stop = False
            count = 0
            for topic in topics:
                if topic['url'] in source:
                    count += 1
                    if count > 5:
                        stop = True
                        break
                    else:
                        continue
                yield scrapy.Request(topic['url'], callback=self.extract_json)
            if not stop:
                if response.url == (self.site + "/tin-tuc-24h"):
                    next_page = response.url + "-p2"
                else:
                    next_page = response.url[:35] + str(int(response.url[35:]) + 1)
                yield response.follow(next_page, callback=self.parse)

    def extract_json(self, response):
        def cv_link(url):
            url = url.split('/')
            url[2] = 'v' + url[2][2:]
            del url[4]
            del url[7]
            del url[-1]
            del url[-1]
            url[-1] = url[-1] + '.mp4'
            return '/'.join(url)

        data = {
            'site': self.site,
            'url': response.url,
            'category': response.xpath('//ul[@class = "breadcrumb"]//a/@title').get(),
            'title': response.xpath('//h1[@class="title-detail"]//text()').get(),
            'summary': response.xpath('//p[@class="description"]//text()').get(),
            "content": response.xpath(
                '//article[@class="fck_detail"]//p[@class="Normal" and not (@style="text-align:right;")]//text()').getall(),
            "author": ''.join(response.xpath('//p[@style="text-align:right;"]//text()').getall()).strip(),
            "images": [{'src:': img.xpath('./@data-src').get(),
                        'alt:': img.xpath('./@alt').get(), }
                       for img in
                       response.xpath('//div[@class="fig-picture"]//img')],
            'videos': [{'src:': cv_link(vid.xpath('//div[@class="videoContainter"]//@src').get()),
                        'desc:': vid.xpath('.//figcaption[@class="desc_cation"]//p//text()').getall(), }
                       for vid in
                       response.xpath('//figure[@class="item_slide_show clearfix"]')],
        }

        if data['content']:
            try:
                with open('data/vnexpress-' + self.date + '.json', encoding='utf-8') as f:
                    source = json.load(f)
            except FileNotFoundError:
                source = []
            with open('data/vnexpress-' + self.date + '.json', 'w', encoding='utf-8') as f:
                source.append(data)
                json.dump(source, f, ensure_ascii=False)
