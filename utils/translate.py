import os
import sys
import json
import hashlib
import requests

from config import config


class Translate(object):
    """ 百度通用翻译接口封装类。
    """

    def __init__(self):
        self.api = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
        self.app_id = config.APP_ID
        self.secret_key = config.SECRET_KEY
        self.salt = config.SALT

    def sign(self, q):
        """ 生成百度翻译api要求的sign(md5值)。
        :param q: :String: 待翻译文字。
        :return :String: 已翻译文字。
        """
        sign = self.app_id + q + self.salt + self.secret_key
        return hashlib.md5(sign.encode()).hexdigest()

    def result(self, q):
        """ 发送翻译请求、解析翻译结果。输入默认检测语种，输出英文。
        :param q: :String: 待翻译文字。
        :return :String: 已翻译文字。
        """
        if isinstance(q, list):
            # q = str(q)
            q = ','.join(q)

            # print('q', len(q), type(q), q)
            # q = q.replace("[", "")
            # q = q.replace("]", "")
        q = str(q)
        # print('q', type(q), q)
        data = {
            'q': q,
            'from': 'auto',
            'to': 'en',
            'appid': config.APP_ID,
            'salt': config.SALT,
            'sign': self.sign(q),
        }

        # 获取翻译结果
        rps = requests.post(self.api, data=data)
        # print('requests',data, type(rps.content), dir(rps), rps.json())
        # content = json.loads(rps.content)
        content = rps.json()
        # print(type(content), content)
        trans_result = content.get('trans_result')[0].get('dst')
        # print('trans_result',type(trans_result), trans_result)

        # 错误处理 对不能进行json.loads的数据进行容错
        try:
            # trans_result = trans_result.replace("'", '"')
            # print('trans_result',type(trans_result), trans_result)
            # ret = json.loads(trans_result)
            # ret = trans_result.replace("[", "")
            # ret = trans_result.replace("]", "")
            ret = trans_result.split(",")
            print(len(ret), type(ret), ret)
        except Exception as e:
            print('不能进行json.loads处理', e)
            ret = trans_result
        return ret


translate = Translate()
# result = translate.result('["白云", "蓝天", "天空"]')
# result = translate.result("['白云', '蓝天', '天空', '山顶', '自驾游', '驾车', '冰山梁']")
# print(
#     type(result), result,
# )
