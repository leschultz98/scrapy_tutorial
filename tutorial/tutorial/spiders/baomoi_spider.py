import json
import time

import scrapy


class BaoMoiSpider(scrapy.Spider):
    name = 'baomoi'

    def start_requests(self):
        self.site = 'https://baomoi.com'
        try:
            getattr(self, 'date')
        except AttributeError:
            now = time.localtime()
            self.date = str(now.tm_mday) + '-' + str(now.tm_mon) + '-' + str(now.tm_year)
            self.hour = now.tm_hour
        url = self.site + "/tin-moi/trang1.epi"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        list = response.xpath(
            '//div[@class="timeline loadmore"]/div[not(contains(@class, "wait-render") or contains(@class, "video"))]')
        topics = [{'title': l.xpath('.//a[@class="cache"]/@title').get(),
                   'url': self.site + l.xpath('.//a[@class="cache"]/@href').get(),
                   } for l in list if self.hour - int(l.xpath('.//time/@datetime').get()[11:13]) <= 3]
        # str(int(l.xpath('.//time/@datetime').get()[8:10])) in self.date[:2]
        if topics:
            source = []
            try:
                with open('data/baomoi-' + self.date + '.json', encoding='utf-8') as f:
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
                next_page = response.url[:32] + str(int(response.url[32:-4]) + 1) + response.url[-4:]
                yield response.follow(next_page, callback=self.parse)

    def extract_json(self, response):
        data = {
            'site': self.site,
            'url': response.url,
            'category': response.xpath('//div[@class = "breadcrumb"]/a[1]//text()').get(),
            'title': response.xpath('//h1[@class="article__header"]//text()').get(),
            'summary': response.xpath('//div[@class="article__sapo"]//text()').get(),
            "content": response.xpath('//p[@class="body-text"]//text()').getall(),
            "author": response.xpath('//p[@class="body-text body-author"]//text()').get(),
            "images": [],
            # 'videos': [{'src:': vid.xpath('//div[@class="videoContainter"]//@src').get(),
            #             'desc:': vid.xpath('.//figcaption[@class="desc_cation"]//p/text()').getall(), }
            #            for vid in
            #            response.xpath('//figure[@class="item_slide_show clearfix"]')],
        }
        images = response.xpath('//p[@class="body-image" or @class="body-text media-caption"]')
        x = 0
        while x < len(images):
            dict = {'src:': images[x].xpath('.//img/@src').get(), }
            x += 1
            if x < len(images):
                if images[x].xpath('./@class').get() == "body-text media-caption":
                    dict['desc:'] = images[x].xpath('./em/text()').get()
                    x += 1
            data['images'].append(dict)

        if data['content']:
            try:
                with open('data/baomoi-' + self.date + '.json', encoding='utf-8') as f:
                    source = json.load(f)
            except FileNotFoundError:
                source = []
            with open('data/baomoi-' + self.date + '.json', 'w', encoding='utf-8') as f:
                source.append(data)
                json.dump(source, f, ensure_ascii=False)
