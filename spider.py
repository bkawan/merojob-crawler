import re

import requests
from lxml import html


class MerojobSpider(object):
    search_url = 'https://merojob.com/search/'
    host = 'https://merojob.com'
    all_company_url = 'https://merojob.com/company/'

    def __init__(self):
        self.headers = {"user-agent": "mozilla"}
        self.all_company_data_list = []

    def get_all_company_urls(self):
        response = requests.get(self.all_company_url, headers=self.headers)
        etree = html.fromstring(response.content)
        company_etree = etree.xpath("//div[@class='container mt-3 mb-3']")
        all_company_urls = company_etree[0].xpath(".//h6/a/@href")
        print(all_company_urls)
        all_company_urls = ["{}{}".format(self.host, x) for x in all_company_urls]
        return all_company_urls

    def get_company_detail(self, company_url):
        slug_match = re.findall(r'employer/(.*)/?', company_url)

        response = requests.get(company_url, self.headers)
        etree = html.fromstring(response.content)
        company_name_node = etree.xpath("//h1[@class='mb-0 h4']/text()")
        company_name = 'NoName'
        if company_name_node:
            company_name = company_name_node[0]

        about = etree.xpath("//h2[@class='h4']")
        if about:
            about = about[0].xpath("string()").strip()
        industry = etree.xpath("//span[@title='Industry']/text()")[0].strip()
        org_size_node = etree.xpath("//label[@title='Organization Size']/text()")
        org_size = None
        org_ownership_node = etree.xpath("//label[@title='Organization Ownership']/text()")
        org_ownership = None
        if org_ownership_node:
            org_ownership = org_ownership_node[0].strip()
        website_node = etree.xpath("//span[@data-toggle='tooltip']/a/@href")
        website = None
        if website_node:
            website = website_node[0]
        if org_size_node:
            org_size = org_size_node[0].strip()
        company_detail = {
            'company_name': company_name,
            'industry': industry,
            'org_size': org_size,
            'website': website,
            'org_ownership': org_ownership,
            'about': about,
        }
        if slug_match:
            company_detail.update({
                'slug': slug_match[0].strip("/")
            })

        return company_detail


if __name__ == "__main__":
    spider = MerojobSpider()
    all_company_url = spider.get_all_company_urls()

