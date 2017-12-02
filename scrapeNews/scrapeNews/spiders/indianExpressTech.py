# -*- coding: utf-8 -*-
import scrapy
from scrapeNews.pipelines import InnerSpiderPipeline as pipeline
from scrapeNews.items import ScrapenewsItem
from scrapeNews.pipelines import loggerError


class IndianexpresstechSpider(scrapy.Spider):

    name = 'indianExpressTech'
    allowed_domains = ['indianexpress.com']


    def __init__(self, offset=0, pages=2, *args, **kwargs):
        self.postgres = pipeline()
        self.postgres.openConnection()
        super(IndianexpresstechSpider, self).__init__(*args, **kwargs)
        for count in range(int(offset), int(offset) + int(pages)):
            self.start_urls.append('http://indianexpress.com/section/technology/page/'+ str(count+1))


    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse)


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(IndianexpresstechSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, scrapy.signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        self.postgres.closeConnection()

    def parse(self, response):
        newsContainer = response.xpath('//div[@class="top-article"]/ul[@class="article-list"]/li')
        for newsBox in newsContainer:
            link = newsBox.xpath('figure/a/@href').extract_first()
            if not self.postgres.checkUrlExists(link):
                yield scrapy.Request(url=link, callback=self.parse_article)


    def parse_article(self, response):
        item = ScrapenewsItem()  # Scraper Items
        item['image'] = self.getPageImage(response)
        item['title'] = self.getPageTitle(response)
        item['content'] = self.getPageContent(response)
        item['newsDate'] = self.getPageDate(response)
        item['link'] = response.url
        item['source'] = 101
        if item['image'] is not 'Error' or item['title'] is not 'Error' or item['content'] is not 'Error' or item['newsDate'] is not 'Error':
            yield item

    def getPageContent(self, response):
        data = response.xpath('//h2[@class="synopsis"]/text()').extract_first()
        if (data is None):
            data = response.xpath("//div[@class='full-details']/p/text()").extract_first()
        if (data is None):
            data = ' '.join(' '.join(response.xpath("//div[@class='body-article']/p/text()").extract()).split()[:40])
        if (data is None):
            loggerError.error(response.url)
            data = 'Error'
        return data

    def getPageTitle(self, response):
        data = response.xpath('//h1[@itemprop="headline"]/text()').extract_first()
        if (data is None):
            loggerError.error(response.url)
            data = 'Error'
        return data


    def getPageImage(self, response):
        data = response.xpath('//span[@class="custom-caption"]/img/@data-lazy-src').extract_first()
        if (data is None):
            data = response.xpath("//span[@itemprop='image']/meta[@itemprop='url']/@content").extract_first()
        if (data is None):
            data = 'Error'
            try:
                data = ((response.xpath('//div[@class="lead-article"]/@style').extract_first()).split('url(',1)[1]).split(')',1)[0]
            except Exception as Error:
                loggerError.error(str(Error) + " occured at " + response.url)
        return data

    def getPageDate(self, response):
        try:
            # Relax, This line Will parse the date and remove unnecessary
            # details out of the string provided!
            data = ''.join((str(response.xpath('//span[@itemprop="dateModified"]/text()').extract_first()).split('Published:')[1]).split("'")[0].split('\t')[0].split(' ',1)[1])
        except IndexError:
            try:
                # Relax, This line Will parse the date and remove unnecessary
                # details out of the string provided!
                data = ''.join((str(response.xpath('//span[@itemprop="dateModified"]/text()').extract_first()).split('Updated: ')[1]).split("'")[0].split('\t')[0])
            except IndexError:
                loggerError.error(response.url)
                data = 'Error'
            except Exception as Error:
                loggerError.error(str(Error) + ' occured at: ' + response.url)
                data = 'Error'
        except Exception as Error:
            loggerError.error(str(Error) + ' occured at: ' + response.url)
            data = 'Error'
        finally:
            return data
