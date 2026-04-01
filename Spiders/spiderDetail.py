import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from utils.query import querys




class spider(object):
    def __init__(self,spiderUrl):
        self.spiderUrl = spiderUrl  # 传入参数

    def startBrowser(self):  # 初始化
        service = Service('D:\浙经济毕业论文参考文献\Demo\医疗疾病数据分析可视化系统\MedicalData\Spiders\chromedriver.exe')
        option = webdriver.ChromeOptions()
        option.add_experimental_option("debuggerAddress", "localhost:9223")
        #option.add_argument('--disable-blink-features=AutomationControlled')
        browser = webdriver.Chrome(service=service, options=option)

        return browser

    def main(self,id):   # 定位id导入数据库
    #def main(self, id, browser):
        browser = self.startBrowser()  # 获得浏览器对象
        print('列表URL为:'+self.spiderUrl)
        browser.get(self.spiderUrl)
        # 身高 页面中多个标签的类名相同 用全局搜索先匹配到有“身高体重”的span然后再用following匹配接下来的一条
        try:
            height = re.findall(r'\d+', browser.find_element(by=By.XPATH,value='//span[contains(text(),"身高体重")]/following-sibling::span[1]').text)[0]
        except:
            height = '无'

        # 体重
        try:
            weight = re.findall(r'\d+', browser.find_element(by=By.XPATH,value='//span[contains(text(),"身高体重")]/following-sibling::span[1]').text)[1]
        except:
            weight = '无'

        # 患病时间
        try:
            illDuration = browser.find_element(by=By.XPATH,value='//span[contains(text(),"患病时长")]/following-sibling::span[1]').text
        except:
            illDuration = '无'

        # 过敏史 “\(”匹配括号前的汉字
        # group(1)是匹配对象的一个方法，用于返回匹配到的第一个分组的内容。在正则表达式中，括号()用于定义分组。这些分组可以用于提取匹配的子串，或者在后续的正则表达式中引用。
        try:
            allergy = re.search(r'([\u4e00-\u9fa5]+)\(', browser.find_element(by=By.XPATH,value='//span[contains(text(),"过敏史")]/following-sibling::span[1]').text).group(1)
        except:
            allergy = '暂无信息'

        print(height,weight,illDuration,allergy)
        querys('UPDATE cases SET height=%s,weight=%s,illDuration=%s,allergy=%s WHERE id = %s',
               [height,weight,illDuration,allergy,id]  # 一定要id定位，否则导入数据库的数据都是一样的
               )
if __name__ == '__main__':
   caseList = querys('select * from cases',[],'select')  # 查询病例表
   for i in caseList[241:]:
       spiderObj = spider(i[9])
       spiderObj.main(i[0])
# if __name__ == '__main__':
#     # 只启动一次浏览器
#     temp_spider = spider("")
#     browser = temp_spider.startBrowser()
    
#     try:
#         caseList = querys('select * from cases',[],'select')  # 查询病例表
#         for i in caseList[241:]:
#             spiderObj = spider(i[9])
#             spiderObj.main(i[0], browser)  # 传入浏览器对象
#     finally:
#         browser.quit()  # 确保最后关闭浏览器
