import re

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# while True:
#     date = input('Let empty to get current day or enter date in short form (d-m-yyyy): ')
#     if (not date) or re.match(r'^([1-9]|[12][0-9]|3[01])[-]([1-9]|1[012])[-]\d{4}$', date):
#         break
#     print("Please try again")
#
process = CrawlerProcess(get_project_settings())
# if date:
#     process.crawl('tuoitrepost', date='1123')
# else:
#     process.crawl('tuoitrepost')
process.crawl('tuoitre')
process.crawl('vnexpress')
process.crawl('baomoi')
process.start()
