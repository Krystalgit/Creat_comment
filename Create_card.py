import random
import string

import requests
import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import bs4
print(help(bs4))
import re
from bs4 import BeautifulSoup as bs
from io import BytesIO



class Creat_Card:
    def __init__(self):
        self.current_path = os.path.dirname(__file__)
        self.session = requests.session()

    def crop_max_square(self, pil_img):
        return self.crop_center(pil_img, min(pil_img.size), min(pil_img.size))

    def crop_center(self, pil_img, crop_width, crop_height):
        img_width, img_height = pil_img.size
        return pil_img.crop(((img_width - crop_width) // 2,
                             (img_height - crop_height) // 2,
                             (img_width + crop_width) // 2,
                             (img_height + crop_height) // 2))

    def mask_circle_transparent(self, pil_img, blur_radius, offset=0):
        offset = blur_radius * 2 + offset
        mask = Image.new('L', pil_img.size, 0)
        draw = ImageDraw.Draw(mask)

        draw.ellipse((offset, offset, pil_img.size[0] - offset, pil_img.size[1] - offset), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

        result = pil_img.copy()
        result.putalpha(mask)
        return result

    def line_break(self, line, CHAR_SIZE=24):
        LINE_CHAR_COUNT = CHAR_SIZE * 2  # 每行字符数：30个中文字符(=60英文字符)
        TABLE_WIDTH = 4
        ret = ''
        width = 0
        for c in line:
            if len(c.encode('utf8')) == 3:  # 中文
                if LINE_CHAR_COUNT <= width + 1:  # 剩余位置不够一个汉字
                    width = 2
                    ret += '\n' + c
                else:  # 中文宽度加2，注意换行边界
                    width += 2
                    ret += c
            else:
                if c == '\t':
                    space_c = TABLE_WIDTH - width % TABLE_WIDTH  # 已有长度对TABLE_WIDTH取余
                    ret += ' ' * space_c
                    width += space_c
                elif c == '\n':
                    width = 0
                    ret += c
                elif c == '.':
                    width += 0.5
                    ret += c
                elif c == '(':
                    width += 0.5
                    ret += c
                elif c == ')':
                    width += 0.5
                    ret += c
                elif c == '，':
                    if LINE_CHAR_COUNT <= width:
                        ret += '\n' + c
                        width = 1.34
                    elif LINE_CHAR_COUNT <= width + 1.34:  # 剩余位置不够一个汉字
                        ret += c + '\n'
                    else:
                        width += 1.34
                        ret += c
                else:
                    width += 1.34
                    ret += c
            if width >= LINE_CHAR_COUNT:
                ret += '\n'
                width = 0
        if ret.endswith('\n'):
            return ret
        return ret + '\n'

    def get_user_basic_info(self, data):
        # print(data)
        post_publish_time = data['post']['post_publish_time']
        post_click_count = data['post']['post_click_count']
        post_comment_count = data['post']['post_comment_count']
        post_like_count = data['post']['post_like_count']
        post_ip_address = data['post']['post_ip_address']
        post_id = data['post']['post_id']
        post_title = data['post']['post_title']
        post_content = data['post']['post_content']
        if 'FundTopicPost' in data['post']['extend']:
            post_topic = [str(i['htid']) + '_' + str(i['name']) for i in data['post']['extend']['FundTopicPost']]
            post_topic = ','.join(post_topic)
        else:
            post_topic = ''
        user_id = data['post']['post_user']['user_id']
        user_nickname = data['post']['post_user']['user_nickname']
        stockbar_code = data['post']['post_guba']['stockbar_code']
        stockbar_name = data['post']['post_guba']['stockbar_name']
        data = dict(post_publish_time=post_publish_time, post_click_count=post_click_count,
                    post_comment_count=post_comment_count, post_like_count=post_like_count,
                    post_ip_address=post_ip_address, post_id=post_id, post_title=post_title, post_content=post_content,
                    post_topic=post_topic, user_id=user_id, user_nickname=user_nickname, stockbar_code=stockbar_code,
                    stockbar_name=stockbar_name)
        df = pd.DataFrame([data])
        return df

    def get_bar_fundcode(self, stockbar_code):
        fundcode = ''
        if re.match('^of', str(stockbar_code)) is not None:
            fundcode = stockbar_code.split('of')[1]
        return fundcode

    def clean_post_content(self, post_content):
        soup = bs(post_content, 'lxml')
        texts = [text for text in soup.stripped_strings]
        texts = ''.join(texts)
        return texts

    def get_article_data(self, postid):
        """
            根绝文章内容，获得主题类型
        """
        # print(postid)
        url = 'https://gbapi.eastmoney.com/content/api/Post/FundArticleContent'
        params = {
            'postid': postid,
            'plat': 'wap',
            'version': '010',
            'product': 'Fund',
            'deviceid': 1,
            'ctoken': '',
            'utoken': ''
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.56 '
        }
        res = self.session.get(url=url, params=params, headers=headers)
        # print(res.text)
        data = res.json()
        df = self.get_user_basic_info(data)
        df['bar_fundcode'] = df['stockbar_code'].map(lambda x: self.get_bar_fundcode(x))
        df['post_content'] = df['post_content'].map(lambda x: self.clean_post_content(x))
        df['qface'] = df['user_id'].map(lambda x: 'https://avator.eastmoney.com/qface/%s/360' % str(x))
        d = df.iloc[0].to_dict()
        return d

    def get_barinfo(self, fundCode):
        url = 'https://uni-fundts.1234567.com.cn/community/fundBar/getFundBarInfo'
        passportid = ''.join(random.sample(string.digits * 3, 17)),
        deviceid = ''.join(
            random.sample(string.digits * 3 + string.ascii_letters * 3, 30)) + '72%7C%7Ciemi_tluafed_me',
        ctoken = ''.join(
            random.sample(string.digits * 10 + string.ascii_letters * 10 + string.punctuation * 1, 171)),
        utoken = ''.join(
            random.sample(string.digits * 10 + string.ascii_letters * 10 + string.punctuation * 1, 331)),
        params = dict(fundCode=fundCode, product='EFund', plat='Android', version='6.6.4', passportid=passportid,
                      deviceid=deviceid, ctoken=ctoken, utoken=utoken)
        res = self.session.get(url=url, params=params)
        FansCount = res.json()['Data']['FansCount']
        PostCount = res.json()['Data']['PostCount']
        print(FansCount, PostCount)
        return FansCount, PostCount

    def draw_card(self, postid, istop=False):
        d = self.get_article_data(postid)
        FansCount, PostCount = self.get_barinfo(d['bar_fundcode'])
        print(d)
        post_title = d['post_title'].replace(' ', '')
        post_content = d['post_content'].replace(' ', '')
        if post_title[0:22] != post_content[0:22]:
            if len(post_title) <= 22:
                post_title = post_title[0:22]
            else:
                post_title = post_title[0:22] + '...'
            post_content = re.sub(post_title.replace(r'...', ''), '', post_content)
            post_content = re.search('(?<=(。|！|，|#|？)).*', post_content).group(0)
            post_content = self.line_break(post_content, 24)
        else:
            if len(post_content) < 50:
                post_title = ''
                post_content = self.line_break(post_content, 24)
            elif len(post_title) <= 22:
                post_title = post_title[0:22]
                post_content = re.sub(post_title.replace('...', ''), '', post_content)
                post_content = re.search('(?<=(。|！|，|#|？)).*', post_content).group(0)
                post_content = self.line_break(post_content, 24)

            else:
                post_title =post_title[0:22] + '...'
                # print(post_title.replace('...', ''), post_content)
                post_content = post_content.replace(post_title.replace('...', ''), '')
                post_content1 = re.search('(?<=(。|！|，|#|？|\]|\$)).*', post_content).group(0)
                if post_content1 is not None:
                    post_content = self.line_break(post_content1, 24)

        rows = post_content.split('\n')

        add_all = False
        if len(rows) > 3:
            add_all = True

        post_content = '\n'.join(rows[0:3])
        rows = post_content.split('\n')
        rows = [i for i in rows if i != '']

        # print(d)
        images = []
        if istop is True:
            image0 = Image.open(self.current_path + '/image/img_top.png')
            images.append(image0)
        pic_path = self.current_path + '/image/white_bg.png'
        image1 = Image.open(pic_path)
        print(len(rows), rows)
        if post_title != '':
            if len(rows) == 3:
                height = 455
            elif len(rows) == 2:
                height = 395
            else:
                height = 335
        else:
            if len(rows) == 3:
                height = 375
            elif len(rows) == 2:
                height = 315
            else:
                height = 255
        print('图片高度=%s' % height)
        image1 = image1.resize((1080, height))
        draw1 = ImageDraw.Draw(image1)
        qface = BytesIO(self.session.get(d['qface']).content)
        image_qface = Image.open(qface)
        image_qface = self.crop_max_square(image_qface).resize((100, 100), Image.LANCZOS)
        image_qface = self.mask_circle_transparent(image_qface, 0)
        image1.paste(image_qface, (75, 34), image_qface)
        images.append(image1)


        font_name = ImageFont.truetype(self.current_path + '/font/苹方黑体-中粗-简.ttf', 40)
        font_content = ImageFont.truetype(self.current_path + '/font/苹方黑体-准-简.ttf', 38)
        font_img2 = ImageFont.truetype(self.current_path + '/font/苹方黑体-准-简.ttf', 36)
        font_date = ImageFont.truetype(self.current_path + '/font/苹方黑体-准-简.ttf', 28)
        draw1.text((200, 30), u'%s' % d['user_nickname'], '#000000', font_name, align='left')
        draw1.text((200, 96), u'%s' % pd.to_datetime(d['post_publish_time']).strftime('%Y-%m-%d %H:%M:%S'), '#888888',
                   font_date, align='left')
        draw1.text((70, 176), u'%s' % post_title, '#000000', font_name, align='left')
        if post_title != '':
            draw1.text((70, 244), u'%s' % post_content, '#000000', font_content, align='left', spacing=20)
        else:
            draw1.text((70, 164), u'%s' % post_content, '#000000', font_content, align='left', spacing=20)

        if add_all is True:
            image_all = Image.open(self.current_path + '/image/all.png')
            if post_title == '':
                if len(rows) == 3:
                    image1.paste(image_all, (864, 338))
            else:
                if len(rows) == 3:
                    image1.paste(image_all, (864, 358))

        if istop is True:
            image_cover = Image.open(self.current_path + '/image/img_cover.png')
            image1.paste(image_cover, (0, 0), image_cover)

        image2 = Image.open(self.current_path + '/image/comment_card_part2.png')
        draw2 = ImageDraw.Draw(image2)
        # print(PostCount)
        barname = d['stockbar_name']
        if len(barname) > 10:
            barname = barname[0:9] + str('...')
        draw2.text((100, 22), u'%s' % barname, '#FFFFFF', font_img2, align='left')
        draw2.text((500, 22), u'%s帖子热议中' % PostCount, '#FFFFFF', font_img2, align='left')
        images.append(image2)

        # 拼接长图

        total_height = 0
        for i in images:
            total_height += i.size[1]
        to_image = Image.new('RGBA', (1080, total_height))
        height = 0
        for i in images:
            to_image.paste(i, (0, height))
            height += i.size[1]
        to_image.save(self.current_path + '/comment_card1.png', 'png')
        return to_image

    def streamlit(self):
        st.header('定投达人卡片素材生成')
        colwd1, colwd2 = st.columns(2)
        with colwd1:
            postid = st.text_input('输入帖子postid', '1304816142')
            is_valuable = st.selectbox('是否是第一张卡片', ['否', '是'])
        with colwd2:
            if is_valuable == '是':
                img = self.draw_card(postid, istop=True)
            else:
                img = self.draw_card(postid, istop=False)
            st.image(img)
            with open(self.current_path + '/temp.png', 'rb') as file:
                st.download_button(
                    label='下载图片',
                    data=file,
                    file_name=self.selectfund + '_' + self.optiondate + '.png',
                    mime='image/png'
                )

if __name__ == '__main__':
    c = Creat_Card()
    # df = c.get_article_data('1304110194')
    # d = c.draw_card('1304816142', istop=True)
    # c.get_barinfo('010806')
    c.streamlit()