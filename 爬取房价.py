# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 15:37:54 2019

@author: 10098
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from pyquery import PyQuery as pq
from time import sleep
url = 'https://www.anjuke.com/fangjia/quanguo2019/'

options = webdriver.ChromeOptions()
        #options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2}) # 不加载图片,加快访问速度
options.add_experimental_option('excludeSwitches', ['enable-automation']) # 此步骤很重要，设置为开发者模式，防止被各大网站识别出来使用了Selenium

browser = webdriver.Chrome(options=options)
wait = WebDriverWait(browser, 10) #超时时长为10s
browser.get(url)

        # 自适应等待，点击密码登录选项
browser.implicitly_wait(30) #智能等待，直到网页加载完毕，最长等待时间为30s
pro=[ '安徽', '福建', '甘肃', '广东', '广西', '贵州', '海南', '河北', '黑龙江', '河南', '湖北', '湖南', '江苏', '江西', '吉林', '辽宁', '内蒙古', '宁夏', '青海', '陕西', '山东', '山西', '四川', '新疆', '西藏', '云南', '浙江']
city=[]
price=[]
i=2
while i<29 :
 j=1
 browser.get(url)
 browser.find_element_by_xpath('/html/body/div[2]/div[3]/div/span[2]/a[{}]'.format(i)).click()
 while j<21 :
  city.append(browser.find_element_by_xpath('/html/body/div[2]/div[4]/div[1]/div[1]/ul/li[j]/a/b'.format(j)).text )
  price.append(browser.find_element_by_xpath('/html/body/div[2]/div[4]/div[1]/div[1]/ul/li[j]/a/span'.format(j)).text )
  j=j+1
  print(city)
 i=i+1
