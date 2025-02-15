import difflib
import json
import re
import time
import urllib.parse
import urllib.request
import requests
import urllib.parse
import urllib3
import warnings
import urllib.parse
import json

warnings.filterwarnings("ignore")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

""" 基础翻译域名 """
BASE_URL = "https://translate.google.com.hk/"
# 支持的翻译的语言
SUPPORTED_LANGUAGES = [
    'af', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn',
    'bs', 'bg', 'ca', 'ceb', 'ny', 'zh-CH', 'zh-CN',
    'zh-TW', 'co', 'hr', 'cs', 'da', 'nl', 'en', 'eo',
    'et', 'tl', 'fi', 'fr', 'fy', 'gl', 'ka', 'de', 'el',
    'gu', 'ht', 'ha', 'haw', 'iw', 'hi', 'hmn', 'hu',
    'is', 'ig', 'id', 'ga', 'it', 'ja', 'jw', 'kn',
    'kk', 'km', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'lt',
    'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'mi', 'mr', 'mn',
    'my', 'ne', 'no', 'ps', 'fa', 'pl', 'pt', 'ma', 'ro',
    'ru', 'sm', 'gd', 'sr', 'st', 'sn', 'sd', 'si', 'sk',
    'sl', 'so', 'es', 'su', 'sw', 'sv', 'tg', 'ta', 'te',
    'th', 'tr', 'uk', 'ur', 'uz', 'vi', 'cy', 'xh', 'yi',
    'yo', 'zu', 'auto'
]
# 关键字替换映射：针对不同目标语言的关键字映射
keyword_dict = {
    'zh-CN': {  # 简体中文
        "chainless": "无链",
        "Chainless": "无链",
        "simitalk": "私米",
        "SimiTalk": "私米",
        "无链": "无链",
        "私米": "私米"
    },
    'zh-TW': {  # 繁体中文
        "chainless": "無鏈",
        "Chainless": "無鏈",
        "simitalk": "私米",
        "SimiTalk": "私米",
        "无链": "無鏈",
        "私米": "私米"
    },
    'en': {  # 英语
        "chainless": "Chainless",
        "Chainless": "Chainless",
        "simitalk": "SimiTalk",
        "SimiTalk": "SimiTalk",
        "无链": "Chainless",
        "私米": "SimiTalk"
    },
}


def generate_token(text, tkk):
    """计算tk参数"""

    def uo(a, b):
        for c in range(0, len(b) - 2, 3):
            d = b[c + 2]
            d = ord(d) - 87 if 'a' <= d else int(d)
            d = a >> d if b[c + 1] == '+' else a << d
            a = (a + d & 4294967295) if b[c] == '+' else a ^ d
        return a

    d = tkk.split('.')
    b = int(d[0])
    e = []
    for g in range(len(text)):
        l = ord(text[g])
        if l < 128:
            e.append(l)
        elif l < 2048:
            e.append(l >> 6 | 192)
            e.append(l & 63 | 128)
        elif 55296 == (l & 64512) and g + 1 < len(text) and 56320 == (ord(text[g + 1]) & 64512):
            l = 65536 + ((l & 1023) << 10) + (ord(text[g + 1]) & 1023)
            e.append(l >> 18 | 240)
            e.append(l >> 12 & 63 | 128)
            e.append(l >> 6 & 63 | 128)
            e.append(l & 63 | 128)
            g += 1
        else:
            e.append(l >> 12 | 224)
            e.append(l >> 6 & 63 | 128)
            e.append(l & 63 | 128)

    a = b
    for f in range(len(e)):
        a += e[f]
        a = uo(a, "+-a^+6")
    a = uo(a, "+-3^+b+-f")
    a ^= int(d[1])
    if a < 0:
        a = (a & 2147483647) + 2147483648
    a %= 1E6
    return "{}.{}".format(int(a), int(a) ^ b)


class GuRans:
    """
    请求值
    """

    def __init__(self):
        self.base_url = BASE_URL
        # self.url = 'https://translate.google.com.hk/translate_a/single'
        self.url = f"{self.base_url}translate_a/single"
        self.TKK = "434674.96463358"  # 这个值可能需要定期更新

        # HTTP请求头
        self.header = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cookie": "NID=188=M1p_rBfweeI_Z02d1MOSQ5abYsPfZogDrFjKwIUbmAr584bc9GBZkfDwKQ80cQCQC34zwD4ZYHFMUf4F59aDQLSc79_LcmsAihnW0Rsb1MjlzLNElWihv-8KByeDBblR2V1kjTSC8KnVMe32PNSJBQbvBKvgl4CTfzvaIEgkqss",
            "referer": self.base_url,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36",
            "x-client-data": "CJK2yQEIpLbJAQjEtskBCKmdygEIqKPKAQi5pcoBCLGnygEI4qjKAQjxqcoBCJetygEIza3KAQ==",
        }

        # 翻译请求的参数
        self.data = {
            "client": "webapp",  # 基于网页访问服务器
            "sl": "auto",  # 源语言, auto 表示由谷歌自动识别
            "tl": "zh-CN",  # 翻译的目标语言
            "hl": "zh-CN",  # 界面语言选中文
            "dt": ["at", "bd", "ex", "ld", "md", "qca", "rw", "rm", "ss", "t"],  # dt表示要求服务器返回的数据类型
            "otf": "2",
            "ssel": "0",
            "tsel": "0",
            "kc": "1",
            "tk": "",  # 谷歌服务器会核对的token
            "q": ""  # 待翻译的字符串
        }

    def construct_url(self):
        """构建请求URL的方法"""
        base = self.url + '?'
        for key in self.data:
            if isinstance(self.data[key], list):
                base = base + "dt=" + "&dt=".join(self.data[key]) + "&"
            else:
                base = base + key + '=' + self.data[key] + '&'
        base = base[:-1]
        return base

    def real_query(self, q, lang_to=''):
        """发送翻译请求的方法"""

        # 清理输入字符串
        # q = re.sub(r'''[^\u2E80-\u9FFF \n\t\w_.!'"“”`+-=——,$%^，。？、~@#￥%……|[\]&\\*《》<>「」{}【】()/]''', '', q)
        _pattern = r"""[^\u2E80-\u9FFF \n\t\w_.!'"“”`+-=——,$%^，。？、~@#￥%……|[\]&\\*《》<>「」{}【】()/]"""
        q = re.sub(_pattern, '', q)
        retry = 2
        while retry > 0:
            try:
                # print(q)
                self.data['q'] = urllib.parse.quote(q)
                self.data['tk'] = generate_token(q, self.TKK)
                if lang_to:
                    self.data['tl'] = lang_to
                url = self.construct_url()
                # print(url, self.header)
                re_obj = requests.post(url, headers=self.header)
                response = json.loads(re_obj.text)
                target_text = ''
                for item in response[0]:
                    if item[0]:
                        target_text += item[0]
                return target_text, response[2], re_obj.status_code
            except Exception as e:
                print(e)
                retry -= 1
                time.sleep(1)
        return "", False, False


def health():
    """健康检测接口,返回是速度"""
    start_time = time.time()
    gs = GuRans()
    tgt_string, _l, _c = gs.real_query('this is a test text')
    end_time = time.time()
    if tgt_string and _c == 200:
        return end_time - start_time
    else:
        return -1


def translate(_data, headers=None):
    # 提取输入数据
    msg_id = _data.get('msgId')
    src_content = _data.get('srcContent')
    base_src_content=src_content
    language_from = _data.get('languageFrom')
    language_to = _data.get('languageTo')
    src_decrypted_content = _data.get('srcDecryptedContent')
    base_src_decrypted_content=src_decrypted_content
    # print("传入的原始内容(srcDecryptedContent): ", src_decrypted_content)
    server_msg_id = _data.get('serverMsgId')
    task_id = _data.get('taskId')
    name_list = _data.get('nameList')
    gs = GuRans()

    # 确保小写
    language_from = language_from.lower() if language_from else None
    language_to = language_to.lower() if language_to else None

    # 检查目标语言支持情况
    default_language = 'zh-CN'
    if language_to is None:
        _language_to = default_language
    elif language_to not in SUPPORTED_LANGUAGES:
        return {'code': 200, 'msg': '语言不支持', 'data': {'msgId': msg_id, 'status': -1}}
    else:
        _language_to = language_to

    # 将目标翻译语言设置到翻译主体
    gs.data['tl'] = _language_to

    # 翻译语言暂时不使用srcContent，使用src_decrypted_content
    if src_decrypted_content:
        src_decrypted_content = src_decrypted_content.strip()

    # 确保翻译语言不能为空
    if not src_decrypted_content:
        return {'code': 200, 'msg': '内容不能为空', 'data': {'msgId': msg_id, 'status': -1}}

    # 源语言分析，如果不支持，默认auto
    if language_from and language_from in SUPPORTED_LANGUAGES:
        gs.data['sl'] = language_from
    else:
        gs.data['sl'] = 'auto'

    # 获取目标语言对应的关键字映射
    keyword_map = keyword_dict.get(_language_to, {})

    # 抽取URL并进行编码
    url_dict = extract_urls(src_decrypted_content)
    url_placeholders = {}
    for idx, url in enumerate(url_dict.keys()):
        # 使用原始 URL，无需额外编码
        placeholder = f"[URL_{idx}]"
        src_decrypted_content = src_decrypted_content.replace(url, placeholder)
        url_placeholders[placeholder] = url  # 存储原始 URL

    # 替换关键字为目标语言的文本
    for keyword, replacement in keyword_map.items():
        src_decrypted_content = src_decrypted_content.replace(keyword, replacement)

    # 调用翻译
    target_text, auto_from, _code = gs.real_query(src_decrypted_content)

    # 恢复URL
    for placeholder, url in url_placeholders.items():
        target_text = target_text.replace(placeholder, url)

    # 获取原始语言
    if auto_from:
        language_from = auto_from

    # 组装返回数据
    if target_text and _code == 200:
        re_data = {
            "msgId": msg_id,
            "srcContent": base_src_content,
            "serverMsgId": server_msg_id,
            "srcDecryptedContent": base_src_decrypted_content,
            "languageFrom": language_from,
            "languageTo": language_to,
            "dstContent": target_text,
            "dstLength": len(str(target_text)),
            "status": 0,
            "taskId": task_id,
            "nameList": name_list,
            "recode": _code,
        }
        return {'code': 200, 'msg': 'success', 'data': re_data}
    else:
        return {'code': 500, 'msg': '翻译失败', 'data': {'msgId': msg_id, 'status': -1}}


def is_can_translate(_data):
    # pattern = r'^[a-zA-Z0-9\u4e00-\u9fff\u3000-\u303f\u2000-\u206f\u0020-\u007e\uff00-\uffef]+$'
    pattern = r"""^[a-zA-Z0-9\u4e00-\u9fff\u3000-\u303f\u2000-\u206f\u0020-\u007e\uff00-\uffef]+$"""
    return bool(re.match(pattern, _data))


def is_can_translate_d(_data):
    if _data != '。':
        return True
    return False


def concurrent_test(text):
    _text = ""
    replace_dict = {}
    num = 0
    for _ in text:
        if _ and is_can_translate(_) and _ != " ":
            _text += _
        else:
            symbol = f"[& {num} &]"
            num += 1
            _text += symbol
            replace_dict[symbol] = _
    return _text, replace_dict


def replace_str(_text, s_dict):
    for _k, _v in s_dict.items():
        _text = _text.replace(_k, _v)
    return _text


def is_all_chinese_and_symbols(s):
    # pattern = r'^[\u4e00-\u9fa5\u3000-\u303F\uFF00-\uFFEF]+$'
    pattern = r"""^[\u4e00-\u9fa5\u3000-\u303F\uFF00-\uFFEF]+$"""
    return bool(re.match(pattern, s))


def string_chinese(in_put):
    in_put = in_put.replace("Chainless", "").replace("SimiTalk", "")
    _len = len(in_put)
    _cn = 0
    for _i, _s in enumerate(in_put):
        if is_all_chinese_and_symbols(_s):
            if _i == 0:
                _cn += _len / 4
            _cn += 1
    if _cn >= _len / 2:
        return True
    return False


def extract_urls(text):
    # 定义正则表达式模式，匹配 http、https 和 www 开头的 URL
    # url_pattern = r'https?://[^\s]+|www\.[^\s]+'
    url_pattern = r"""https?://[^\s]+|www\.[^\s]+"""
    re_dict = {}
    # 使用 re.findall() 提取所有匹配的 URL
    urls = re.findall(url_pattern, text)
    for url in urls:
        re_dict[url.lower()] = url
    return re_dict


def get_models():
    """模型值"""
    models = {
        "object": "list",
        "data": [
            {"id": "gurans", "object": "model", "created": 1738940617, "owned_by": "Google"}
        ]
    }
    return json.dumps(models)


if __name__ == "__main__":
    # 测试用例
    test_text = r"""武当山驻少林寺办事处王喇嘛，给大家介绍私米，还有无链，介绍l一个文章： https://chainless.hk/zh-hans/2023/11/26/dw20%e5%8e%bb%e4%b8%ad%e5%bf%83%e6%9c%ac%e4%bd%8d%e5%b8%81%e7%9a%84%e5%ae%9e%e7%8e%b0/   好了"""
    print(f"即将测试的文字长度: {len(test_text)}")
    ask_data = {
        'msgId': "",
        'srcContent': "",
        'nameList': "",
        'languageFrom': "auto",
        'languageTo': "en",
        'srcDecryptedContent': test_text,
        'serverMsgId': "",
        'num': 100
    }
    # print("111: ", test_text)
    # print("ask_data: ", ask_data)
    # print("传入的原始内容(srcDecryptedContent): ", ask_data['srcDecryptedContent'])

    # print("翻译测试: ", translate(ask_data))
    print("翻译测试: ", json.dumps(translate(ask_data), ensure_ascii=False, indent=4))

    print(f"健康状态测试，耗时: {health()}")
