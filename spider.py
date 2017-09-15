import re
from datetime import datetime

import requests
from lxml import html

search_link = 'https://merojob.com/search/'


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

    def get_all_job_urls(self, search_link=search_link):
        host = 'https://merojob.com'
        jobs = []
        response = requests.get(search_link)
        etree = html.fromstring(response.content)
        pagination_next = etree.xpath("//a[@class='pagination-next page-link']/@href")
        if pagination_next:
            pagination_next = '{}{}'.format(host, pagination_next[0])
            jobs += self.get_all_job_urls(pagination_next)
        job_links = etree.xpath("//h1[@itemprop='title']/a/@href")
        jobs += job_links
        return jobs

    def get_salary(self, offered_salary):
        minimum_salary = 0
        maximum_salary = None
        currency = None
        salary_unit = None

        if offered_salary:
            salary = re.sub(r'[\s\n,]+', "", offered_salary)
            if "Negotiable" not in salary:
                salary = re.sub(r'[\s\n,]+', "", salary)
                min_max = re.findall(r'[\d.]+', salary)
                curr_range = re.findall(r'[a-zA-Z]+', salary)
                minimum_salary = min_max[0].strip(".")
                maximum_salary = None
                if len(min_max) == 2:
                    maximum_salary = min_max[1]
                currency = curr_range[0]
                salary_unit = curr_range[1]
        return {
            "minimum_salary": minimum_salary,
            "maximum_salary": maximum_salary,
            "currency": currency,
            "salary_unit": salary_unit,
        }

    def get_job_data(self, job_url):
        job_data = {}
        response = requests.get(job_url)
        etree = html.fromstring(response.content)
        job_type = etree.xpath("//a[@class='ui right corner label']/i/@class")
        job_type = job_type[0].split(" ")[0].replace('icon-', '')
        title = etree.xpath("//h1[@itemprop='title']/text()")
        employment_node = etree.xpath("//td[@itemprop='employmentType']")
        employment_type = ['Full Time']
        if employment_node:
            employment_type = employment_node[0].xpath("string()")
            employment_type = re.sub(r'[\n\s]+', '', employment_type).split(",")
        date_posted_node = etree.xpath("//meta[@itemprop='datePosted']/@content")
        if date_posted_node:
            date_posted = date_posted_node[0].strip()
        else:
            date_posted = datetime.now()
        deadline = etree.xpath("//meta[@itemprop='validThrough']/@content")
        if deadline:
            deadline = deadline[0].strip()
        skills = etree.xpath("//span[@itemprop='skills']/span/text()")
        job_description = etree.xpath("//div[@itemprop='description']")
        if len(job_description) > 1:
            job_description = job_description[1].xpath('string()')
        else:
            if job_type == 'newspaper':
                job_description = job_description[0].xpath("string()")
            else:
                job_description = ""
        job_data.update({
            'title': title[0].strip(),
            'date_posted': date_posted,
            'deadine': deadline,
            'skills': skills,
            'job_description': job_description.strip(),
            'job_type': job_type
        })

        table_etree = etree.xpath("//table")
        for table in table_etree:
            tr_etree = table.xpath(".//tr")
            for tr in tr_etree:
                td = tr.xpath(".//td")
                key = td[0].xpath("string()").strip().lower().replace(" ", "_").strip(":")
                value = td[1].xpath("string()").strip()
                job_data.update({
                    key: value
                })
        specification_node = etree.xpath("//div[@class='card-group']")
        other_specification_node = None
        for n in specification_node:
            h6 = n.xpath(".//h6/text()")
            if h6:
                h6 = h6[0].strip()
                if "Other Specification" in h6:
                    other_specification_node = n
        if other_specification_node:
            other_specification = other_specification_node.xpath("string()").strip("Other Speficifation\n").strip()
            job_data.update({
                "other_specification": other_specification
            })

        job_category = job_data.get('job_category')
        if job_category:
            job_categories = job_category.split(">")
            parent_job_category = job_categories[0].strip()
            job_sub_category = None
            if len(job_categories) > 1:
                job_sub_category = job_categories[1].split(",")
            job_data.update({
                'employment_type': employment_type,
                'job_category': {
                    'parent': parent_job_category,
                    'child': job_sub_category
                },
                'salary': self.get_salary(job_data.get('offered_salary'))
            })

        vacancies = 0
        no_of_vacancy = job_data.get('no._of_vacancy/s')
        if no_of_vacancy:
            match = re.search(r'[\d]+', no_of_vacancy)
            if match:
                job_data.update({
                    'vacancies': match.group()})

        span_node = etree.xpath("//span/text()")
        # print(span_node)
        views = 0
        views_list = []
        for span in span_node:
            if "Views: " in span:
                span = span.strip()
                count = re.findall(r'[\d]+', span)
                if count:
                    views_list.append(count[0])
        views = views_list[0]
        job_data.update({
            'views': views
        })

        employer_name = etree.xpath("//span[@itemprop='name']/text()")
        employer_url = None
        if employer_name:
            employer_name = employer_name[0]
        else:
            employer_name = etree.xpath("//h3[@class='h6']/a/text()")
            if employer_name:
                employer_name = employer_name[0].strip()
        employer_url_node = etree.xpath("//h2[@class='ml-4 pl-5 pl-md-0 h5']/a/@href")
        if employer_url_node:
            employer_url = employer_url_node[0].strip()
            employer_url = re.findall(r'employer/(.*)/?', employer_url)
            if employer_url:
                employer_url = employer_url[0].strip("/")

        job_data.update({
            'client': {
                'employer_name': employer_name,
                'employer_url': employer_url
            }
        })
        slug_match = re.findall(r'com/(.*)/?', job_url)
        if slug_match:
            job_data.update({
                'slug': slug_match[0].strip("/")
            })

        return job_data
    
if __name__ == "__main__":
    spider = MerojobSpider()
    all_company_url = spider.get_all_company_urls()
    all_job_url = spider.get_all_job_urls()
    for job in all_job_url[0:2]:
        print(spider.get_job_data('{}{}'.format(spider.host, job)))

