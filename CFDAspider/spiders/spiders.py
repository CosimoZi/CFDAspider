# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
from scrapy import FormRequest, Request
from scrapy.spiders import Spider
from bs4 import BeautifulSoup
from CFDAspider.items import CFDAItem


class CFDASpider(Spider):
    allowed_domains = ['app1.sfda.gov.cn']
    front_part_url = 'http://app1.sfda.gov.cn/datasearch/face3/'
    start_urls = ['http://app1.sfda.gov.cn/datasearch/face3/dir.html']
    name = 'CFDA'
    targets = [
         '国产保健食品', '进口保健食品', '国产药品', '进口药品', '国产器械', '进口器械', '国产化妆品',
        '进口化妆品',
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse_start_url)

    def parse_start_url(self, response):
        soup = BeautifulSoup(response.body, 'html5lib', from_encoding='gb2312')
        for target in self.targets:
            yield Request(self.front_part_url + soup.find(text=target).parent['href'].replace('amp;', ''),
                          callback=self.parse_first_toc)

    def parse_first_toc(self, response):
        soup = BeautifulSoup(response.body, 'html5lib', from_encoding='gb2312')
        form = soup.find('form',id='pageForm')
        page_info=soup.find(id='content').find('td',text=re.compile(r'共[0-9]+页')).text
        pages=page_info.split('共')[1].split('页')[0]
        for i in range(int(pages)):
            formdata={}
            formdata['State']='1'
            formdata['tableId']=form.find(attrs={"name": "tableId"})['value']
            formdata['bcId'] = form.find(attrs={"name": "bcId"})['value']
            formdata['tableName'] = form.find(attrs={"name": "tableName"})['value']
            formdata['viewtitleName'] = form.find(attrs={"name": "viewtitleName"})['value']
            formdata['viewsubTitleName'] = form.find(attrs={"name": "viewsubTitleName"})['value']
            formdata['tableView'] = form.find(attrs={"name": "tableView"})['value']
            formdata['curstart']=unicode(i+1)
            yield FormRequest('http://app1.sfda.gov.cn/datasearch/face3/search.jsp',formdata=formdata,callback=self.parse_toc)

    def parse_toc(self, response):
        # with open(str(time.time())+'.html','wb')as f:
        #     f.write(response.body)
        soup = BeautifulSoup(response.body, 'html5lib', from_encoding='gb2312')
        links=soup.find_all('a')
        url_list = [url['href'].split("'")[1] for url in links]
        for url in url_list:
            yield Request(self.front_part_url + url, callback=self.parse_item)

    def parse_item(self, response):

        soup = BeautifulSoup(response.body, 'html5lib',from_encoding='utf-8')
        couples = soup.find('table', width='100%', align='center').find_all('tr', bgcolor=None)
        dic = {}
        for couple in couples:
            dic[couple.find_all('td')[0].text] = couple.find_all('td')[1].text
        item = CFDAItem(data=dic)
        yield item
