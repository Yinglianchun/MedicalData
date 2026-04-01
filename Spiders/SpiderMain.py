import requests
from lxml import etree #定位页面元素
import csv   #存储数据
import os
import re
from pymysql import *
from requests import Response
from utils.query import querys


class spider(object):
    def __init__(self):
        self.spiderUrl = 'https://www.haodf.com/citiao/jibing-gaoxueya/bingcheng.html?p=%s'  # 格式化字符串%s控制p的增多
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
        }  # 请求头 使爬虫像浏览器一样发送请求/模拟
    def init(self):
        if not os.path.exists('./temp.csv'):
            with open('./temp.csv', 'a',newline='',encoding='utf-8') as wf:
                write = csv.writer(wf)
                write.writerow(["type","gender","age","time","content","docName","docHospital","department",
                                 "detailUrl","height","weight","illDuration","allergy"]) #创建csv文件存储数据
                try:
                    conn = connect(host='localhost', user='root', password='12345678', database='medicalinfo', port=3306,
                                   charset='utf8mb4')  # 字段名要与sql中创建数据库时选择的一样，否则不会在navicat中创建表
                    sql = '''
                                        create table cases(
                                            id int  primary key auto_increment,
                                            type varchar(255),
                                            gender varchar(255),
                                            age varchar(255),
                                            time varchar(255),
                                            content varchar(255),
                                            docName varchar(255),
                                            docHospital varchar(255),
                                            department varchar(255),
                                            detailUrl varchar(2555),
                                            height varchar(255),
                                            weight varchar(255),
                                            illDuration varchar(255),
                                            allergy varchar(255)
                                        )
                                    '''
                    cursor = conn.cursor()  # 创建游标执行sql语句
                    cursor.execute(sql)  #
                    conn.commit()  # 提交当前事务
                except:
                    pass  # 异常处理，防止报错
# 具体爬取方法
    def main(self,type,page):
        # pageHtml = requests.get(self.spiderUrl,self.header) # 通过get方法向网页发起请求
        # print(pageHtml) #运行一直返回状态码724，加了.text之后只返回forbidden
        response = requests.get(self.spiderUrl % page, headers=self.header)

        if response.status_code == 200:  # 如果返回的状态码是200
            pageHtml = response.text
            page_tree=etree.HTML(pageHtml)
            li_list = page_tree.xpath('//*[@id="me-content"]/main/section/div/ul/li')
            for index,li in enumerate(li_list):  # 使用enumerate函数同时获取每个元素的索引和值
                print("正在爬取页面第%d" % (index+1)+"个数据")
                initData = []
                # 类型
                type = type
                initData.append(type)
                # 性别
                gender = li.xpath('./a/div/span[@class="patient-name"]/text()')[0][3]
                initData.append(gender)
                # 年龄 使用正则表达式’\d‘获取数字类型
                age = re.search(r'\d+',li.xpath('./a/div/span[@class="patient-name"]/text()')[0]).group()
                initData.append(age)
                # 时间 要判断是否有年份
                try:
                    time = re.search(r'\d{1,4}.\d{1,2}.\d{1,2}', li.xpath('./a/div/span[@class="date"]/text()')[0]).group()
                except:
                    time = re.search(r'\d{1,2}.\d{1,2}',li.xpath('./a/div/span[@class="date"]/text()')[0]).group()
                initData.append(time)
                # 描述
                content = li.xpath('./a/h3[@class="title"]/text()')[0]
                initData.append(content)
                # 医生名
                docName = li.xpath('./div/div[@class="svc-info"]/a[@class="name"]/text()')[0]
                initData.append(docName)
                # 医院名
                docHospital = li.xpath('./div/div[@class="svc-info"]/a[@class="hospital"]/text()')[0]
                initData.append(docHospital)
                # 医院科室
                department = li.xpath('./div/div[@class="svc-info"]/a[@class="faculty"]/text()')[0]
                initData.append(department)
                # 详情页链接
                detailUlr = li.xpath('./a/@href')[0]  # 详情页链接是li标签下a的herf属性名
                initData.append(detailUlr)

                # print(type,gender,age,time,content,docName,docHospital,department,detailUlr)
                #print(initData) # 以数组形式输出
                self.save_to_csv(initData)
                #detailHtml = requests.get(detailUlr, self.header).text
                # response2 = requests.get(detailUlr, headers=self.header)
                # if response2.status_code == 200:
                #     detailHtml = response2.text
                #     detail_tree = etree.HTML(detailHtml)
                # else:
                #     print(f"请求失败，状态码：{response2.status_code}")
                # print(detailHtml)
            if page<2:
                self.main(type, page + 1)


        else:
            print(f"请求失败，状态码：{response.status_code}")
# 存储数据
    def save_to_csv(self,resultData):
        with open('./temp.csv','a',newline='',encoding='utf-8') as f:
            write = csv.writer(f)
            write.writerow(resultData) # 使用`writerow`方法将`resultData`中的数据作为一行写入CSV文件。

    def save_to_sql(self):
        with open('./temp.csv','r',encoding='utf-8') as r_f:
            reader = csv.reader(r_f)
            for i in reader:
                if i[0] == 'type':  # "type" 是列名 而要导入的是数据
                    continue
                querys('''
                insert into cases(type,gender,age,time,content,docName,docHospital,department,detailUrl)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                
                ''',[i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7],i[8]]) # 通过格式化字符串传入

if __name__ == '__main__':
    spiderObj = spider()
    # spiderObj.init()  # 初始化函数
    spiderObj.main('高血压',4)
    spiderObj.save_to_sql()

