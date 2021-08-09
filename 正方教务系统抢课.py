import requests
import time
from bs4 import BeautifulSoup
from PIL import Image
import linecache
import os
from threading import Thread


#   设置url
class Set_Base_url(object):

    def __init__(self, base_url, headers):
        self._base_url = base_url
        self._headers = headers

    def request(self):
        resp = requests.get(self._base_url, headers=self._headers)
        return resp.url


#   保存课程信息并显示
class Lesson(object):

    def __init__(self, number, lesson_text, lesson_number, lesson_credit, lesson_last):
        self.number = number
        self.lesson_text = lesson_text
        self.lesson_number = lesson_number
        self.lesson_credit = lesson_credit
        self.lesson_last = lesson_last

    def show(self):
        return self.number + ' 课程名字：' + self.lesson_text + ' , 课程代码：' + self.lesson_number + \
               ' , 学分：' + self.lesson_credit + ' , 剩余名额：' + self.lesson_last

#   抢课程序
class Spider(object):

    def __init__(self, base_url, headers, uid, password):
        self._url = base_url
        self._headers = headers
        self._uid = uid
        self._password = password
        self.session = requests.session()
        self.soup = ''
        self.data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '',
            'ddl_kcxz': '',
            'ddl_ywyl': '',
            'ddl_kcgs': '',
            'ddl_xqbs': '1',
            'ddl_sksj': '',
            'TextBox1': '',
            'dpkcmcGrid:txtChoosePage': '1',
            'dpkcmcGrid:txtPageSize': '100'
        }
        self.select_data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '',
            'ddl_kcxz': '',
            'ddl_ywyl': '',
            'ddl_kcgs': '',
            'ddl_xqbs': '1',
            'ddl_sksj': '',
            'TextBox1': '',
            'dpkcmcGrid:txtChoosePage': '1',
            'dpkcmcGrid:txtPageSize': '100',
            'Button1': ''
        }

    #   获取验证码
    def __get_code(self):
        resp = self.session.get(self._url + 'CheckCode.aspx', timeout=5)
        with open('code.jpg', 'wb')as f:
            f.write(resp.content)
        img = Image.open('code.jpg')
        img.show()
        code = input('请输入验证码： ')
        return code

    #   获取登录数据
    def __login_data(self):
        resp = self.session.get(self._url + 'default2.aspx', headers=self._headers, timeout=5)
        soup = BeautifulSoup(resp.text, 'lxml')
        form_tag = soup.find('input')
        __VIEWSTATE = form_tag.get('value')
        data = {
            '__VIEWSTATE': __VIEWSTATE,
            'txtUserName': self._uid,
            'Textbox1: ': '',
            'TextBox2': self._password,
            'txtSecretCode': self.__get_code(),
            'RadioButtonList1': '%D1%A7%C9%FA',
            'Button1': '',
            'lbLanguage': '',
            'hidPdrs': '',
            'hidsc': '',
        }
        return data

    #   登录
    def login(self):
        while True:
            resp = self.session.post(self._url + 'default2.aspx', headers=self._headers,
                                     data=self.__login_data(), timeout=5)
            soup = BeautifulSoup(resp.text, 'lxml')
            if resp.status_code != requests.codes.ok:
                print('4XX or 5XX Error,try to login again')
                time.sleep(0.5)
                continue
            if resp.text.find('验证码不正确！！') > -1:
                print('验证码错误')
                continue
            if resp.text.find('密码错误') > -1:
                print('密码错误')
                return False
            if resp.text.find('用户名不存在') > -1:
                print('用户名错误')
                return False
            try:
                find = soup.find('span', attrs={'id': 'xhxm'})
                tag = find.text
                print('欢迎' + tag[:tag.find('同学')])
                return True
            except:
                print('未知错误，尝试再次登录')
                time.sleep(0.5)
                continue

    #   返回网页随机码
    def __set__VIEWSTATE(self, soup):
        form_tag = soup.find('input', attrs={'name': '__VIEWSTATE'})
        self.data['__VIEWSTATE'] = form_tag.get('value')

    #   返回网页随机码
    def __select__set__VIEWSTATE(self, soup):
        form_tag = soup.find('input', attrs={'name': '__VIEWSTATE'})
        self.select_data['__VIEWSTATE'] = form_tag.get('value')

    #   进入选课界面
    def __enter_lesson(self):
        data = {
            'xh': self._uid,
            'xm': '%C5%B7%BA%A3%C5%A2',
            'gnmkdm': 'N121203',
        }
        self._headers['Referer'] = self._url + 'xs_main.aspx?xh=' + self._uid
        resp = self.session.get(self._url + 'xf_xsqxxxk.aspx', params=data, headers=self._headers, timeout=5)
        self._headers['Referer'] = resp.url
        soup = BeautifulSoup(resp.text, 'lxml')
        self.__set__VIEWSTATE(soup)

    #   课程表格
    def lesson_list(self, soup):
        lesson_table = soup.find('table', id='kcmcGrid')
        lesson_list = []
        lesson_tr = lesson_table.find_all('tr')[1:]
        number = 0
        for lesson in lesson_tr:
            number += 1
            lesson_td = lesson.find_all('td')
            lesson_text = lesson_td[1].string
            lesson_number = lesson_td[2].text
            lesson_credit = lesson_td[6].text
            lesson_last = lesson_td[10].text
            le = Lesson(str(number), lesson_text, lesson_number, lesson_credit, lesson_last)
            lesson_list.append(le)
        with open('课程.txt', 'w', encoding='utf-8')as f:
            for lesson in lesson_list:
                print(lesson.show())
                f.write(lesson.show() + '\n')


    #   搜索所有课程
    def __search_lesson(self):
        data = self.data.copy()
        resp = self.session.post(url=self._headers['Referer'], data=data, headers=self._headers, timeout=5)
        soup = BeautifulSoup(resp.text, 'lxml')
        #   返回 soup 和 网页随机码
        self.__select__set__VIEWSTATE(soup)
        self.soup = soup

    #   选课
    def __select_lesson(self, select_list):
        data = self.select_data.copy()
        data['Button1'] = '提交'.encode('gb2312')
        # 得到网页里的课程的id
        for lesson in select_list:
            num = int(lesson) + 1
            lesson_num = 'kcmcGrid:_ctl' + str(num) + ':xk'
            k = {lesson_num: 'on'}
            data.update(k)
        print('抢课中...')
        while True:
            try:
                resp = self.session.post(url=self._headers['Referer'], data=data, headers=self._headers, timeout=5)
            except requests.exceptions.ConnectionError:
                print('网址响应失败')
                continue
            soup = BeautifulSoup(resp.text, 'lxml')
            self.__select__set__VIEWSTATE(soup)
            if resp.text.find('现在不是选课时间！！'):
                print('现在不是选课时间！！')
            else:
                print('已选或出现异常')

    #   运行程序
    def run(self):
        #   1.登录并进入选课系统
        if self.login():
            print('登录成功，输入\"go\"进入选课系统')
            while True:
                if input('请输入： ') == 'go':
                    self.__enter_lesson()
                    break
                else:
                    print('输入错误，未知功能')
                    continue
        #   2 .搜索所有课程并显示
        print('搜索课程中...')
        self.__search_lesson()
        self.lesson_list(self.soup)
        #   打开爬取到的课程文件夹
        os.startfile('课程.txt')
        #   3.选择课程
        print('选择课程')
        select_list = []
        while True:
            select_num = int(input('要同时抢几门课程(输入数字)：'))
            for i in range(select_num):
                num = input('请输入课程前的ID：')
                select_list.append(num)
            print('选择的课程：')
            print()
            for i in select_list:
                line = linecache.getline('课程.txt', int(i))
                print(line)
            if input('按回车确定：') == '':
                break
            else:
                select_list = []
                continue
        #   单线程
        # self.__select_lesson(select_list)

        #   多线程
        thread = list()
        for i in range(10):
            thread.append(Thread(target=self.__select_lesson, args=(select_list,)))
        for i in range(10):
            thread[i].start()
        for i in range(10):
            thread[i].join()


def main():
    def setting():
        """
        设置基本信息
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
        }

        #   需手动修改的值
        base_url = 'http://210.34.84.1/'  # 网址
        uid = ''            # 账号
        password = ''       # 密码

        set_url = Set_Base_url(base_url, headers)
        _url = set_url.request()
        url = _url[:_url.rfind('/') + 1]
        _spider = Spider(url, headers, uid, password)
        return _spider

    """
    运行
    """
    spider = setting()
    spider.run()


if __name__ == '__main__':
    main()
