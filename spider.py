import json
import requests
from bs4 import BeautifulSoup


class DoubanSpider:

    # 定制用户请求头，避免被反爬
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }

    def __init__(self, people_id, max_level=2, output='out.json'):
        """

        :param people_id: 中心用户的 ID，也就是我们抓取的第一个用户的 ID，
                          可通过 https://www.douban.com/people/<ID>/ 查看此人的主页
        :param max_level: 获取的关注层数
        :param output: 输出文件路径
        """
        self.people_id = people_id
        self.max_level = max_level
        self.output = output

    def run(self):
        out = []
        # 起始 URL
        url = 'https://www.douban.com/people/{}/'.format(self.people_id)
        # 递归爬取
        for item in self.parse_people(*self.request_people(url, self.people_id, 0)):
            if item:
                out.append(item)
        # 输出到文件
        with open(self.output, 'w') as fp:
            json.dump(out, fp, ensure_ascii=False)

    def request_people(self, url, pid, level):
        """
        发起请求

        :param url: 请求的 URL
        :param pid: 用户的 ID
        :param level: 和起始用户相隔的层数
        :return:
        """
        res = requests.get(url, headers=self.headers)
        if res.status_code < 300:
            return res, pid, level
        else:
            # 返回状态码不是 200，可能是被封
            print('Failed to get people page for {}'.format(url))
            return None, pid, level

    def parse_people(self, response, pid, level):
        """
        解析返回的网页

        :param response: 请求返回的相应
        :param pid: 用户的 ID
        :param level: 和起始用户相隔的层数
        :return:
        """
        if response is None:
            yield None
        else:
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
            info = soup.find('div', class_='info')
            if info:
                # 获取当前的用户名
                name = info.find('h1').contents[0].strip()
                yield {'name': name, 'id': pid, 'level': level}
                # 如果层数小于最大层数，则继续获取关注的用户列表
                if level < self.max_level:
                    links = soup.find(id='friend').find_all('a', class_='nbg')
                    for link in links:
                        u = link['href'].strip('/')
                        pid = u[u.rindex('/') + 1:]
                        # 递归解析所有关注的用户
                        for item in self.parse_people(*self.request_people(link['href'], pid, level + 1)):
                            yield item
