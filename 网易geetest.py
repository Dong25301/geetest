from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import cv2
import numpy as np
from io import BytesIO
import time, requests

"""配置"""
EMAIL = 'donggang25301@163.com'
PASSWORD = ''
URL = 'https://id.163yun.com/login'


class CrackSlider():
    """
    通过浏览器截图，识别验证码中缺口位置，获取需要滑动距离，并模仿人类行为破解滑动验证码
    """

    def __init__(self):
        super(CrackSlider, self).__init__()
        self.url = URL
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 20)
        self.email = EMAIL
        self.password = PASSWORD
        self.zoom = 1

    def open(self):
        self.driver.get(self.url)
        email = self.wait.until(EC.presence_of_element_located((By.NAME, 'account')))
        password = self.wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        email.send_keys(self.email)
        password.send_keys(self.password)

    def get_geetest_button(self):
        """[summary]
        获取初始验证按钮,返回按钮对象
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'yidun_slider')))
        return button

    def get_pic(self):
        """获取缩放系数"""
        time.sleep(2)
        target = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'yidun_bg-img')))
        template = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'yidun_jigsaw')))
        target_link = target.get_attribute('src')
        template_link = template.get_attribute('src')
        target_img = Image.open(BytesIO(requests.get(target_link).content))
        template_img = Image.open(BytesIO(requests.get(template_link).content))
        # 保存验证图片到本地
        target_img.save('target.jpg')
        template_img.save('template.png')
        # size_orign = target.size
        local_img = Image.open('target.jpg')
        size_loc = local_img.size
        self.zoom = 320 / int(size_loc[0])

    def get_tracks(self, distance):
        distance += 20
        v = 0
        t = 0.2
        forward_tracks = []
        current = 0
        mid = distance * 3 / 5
        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3
            s = v * t + 0.5 * a * (t ** 2)
            v = v + a * t
            current += s
            forward_tracks.append(round(s))
        # back_tracks = [-3, -3, -2, -2, -2, -2, -2, -1, -1, -1] :依据back_tracks 调整滑动偏移幅度
        back_tracks = [-3, -3, -2, -2, -1]
        return {'forward_tracks': forward_tracks, 'back_tracks': back_tracks}

    def match(self, target, template):
        """缩放系数乘以match函数拿到的缺口水平坐标就是我们要移动的距离"""
        img_rgb = cv2.imread(target)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template = cv2.imread(template, 0)
        run = 1
        w, h = template.shape[::-1]
        # print(w, h)
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)

        # 使用二分法查找阈值的精确值
        L = 0
        R = 1
        while run < 20:
            run += 1
            threshold = (R + L) / 2
            # print(threshold)
            if threshold < 0:
                print('Error')
                return None
            loc = np.where(res >= threshold)
            # print(len(loc[1]))
            if len(loc[1]) > 1:
                L += (R - L) / 2
            elif len(loc[1]) == 1:
                print('目标区域起点x坐标为：%d' % loc[1][0])
                break
            elif len(loc[1]) < 1:
                R -= (R - L) / 2

        return loc[1][0]

    def slide_click_verification(self, tracks, slider):
        """滑动按钮验证"""
        ActionChains(self.driver).click_and_hold(slider).perform()
        for track in tracks['forward_tracks']:
            """move_by_offset()将鼠标移动到当前偏移量"""
            ActionChains(self.driver).move_by_offset(xoffset=track, yoffset=0).perform()
        time.sleep(0.5)
        for back_tracks in tracks['back_tracks']:
            ActionChains(self.driver).move_by_offset(xoffset=back_tracks, yoffset=0).perform()
        ActionChains(self.driver).move_by_offset(xoffset=-3, yoffset=0).perform()
        ActionChains(self.driver).move_by_offset(xoffset=3, yoffset=0).perform()
        time.sleep(0.5)
        # 释放按钮(放开鼠标左键)
        ActionChains(self.driver).release().perform()

    def successful(self):
        try:
            failure = self.wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, 'm-error-message'), '请完成滑块验证'))
            if failure:
                self.crack_slider()
        except:
            print('验证成功')

    def login(self):
        """登录"""
        submit = self.wait.until(EC.element_to_be_clickable((By.TAG_NAME, 'button')))
        submit.click()
        time.sleep(2)
        print('登录成功')

    def crack_slider(self):
        self.open()
        target = 'target.jpg'
        template = 'template.png'
        self.get_pic()
        # 计算出图片的缺口距离
        distance = self.match(target, template)
        tracks = self.get_tracks((distance + 7) * self.zoom)  # 对位移的缩放计算获得偏移量
        # 获取按钮元素
        slider = self.get_geetest_button()
        # 滑动按钮进行验证
        self.slide_click_verification(tracks, slider)
        # 判断是否验证成功
        self.successful()
        # 登录
        self.login()


if __name__ == '__main__':
    crack = CrackSlider()
    crack.crack_slider()
