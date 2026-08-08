import re
import base64
import requests
import hashlib
import configparser
import os

headers = {'User-Agent': 'okhttp/3.15'}

def get_fan_conf():
    config = configparser.ConfigParser()
    config.read("config.ini")

    #url = 'http://www.饭太硬.com/tv/'
    url = 'http://www.饭太硬.net/tv/'

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Error] 网络请求失败：{e}")
        return

    match = re.search(r'[A-Za-z0]{8}\*\*(.*)', response.text)
    if not match:
        print("[Error] 网页内容格式不匹配，未找到 Base64 字符串。")
        return

    result = match.group(1)

    try:
        decoded = base64.b64decode(result).decode('utf-8')
    except Exception as e:
        print(f"[Error] Base64 解码失败：{e}")
        return

    # 计算 MD5
    m = hashlib.md5()
    m.update(result.encode('utf-8'))
    md5 = m.hexdigest()

    try:
        old_md5 = config.get("md5", "conf")
        if md5 == old_md5:
            print("No update needed.")
            return
    except configparser.NoSectionError:
        config.add_section("md5")
    except configparser.NoOptionError:
        pass

    try:
        spider_url = re.search(r'spider"\:"(.*);md5;', decoded).group(1)
    except Exception as e:
        print(f"[Error] 正则提取 spider URL 失败：{e}")
        return
    print("spider_url="+spider_url)
    
    content = decoded.replace(spider_url, './JAR/fan.txt')
    content = diy_conf(content)
    with open('xo.json', 'w', newline='', encoding='utf-8') as f:
        f.write(content)
    # 本地包
    local_content = local_conf(content)
    with open('a.json', 'w', newline='', encoding='utf-8') as f:
        f.write(local_content)


    try:
        config.set("md5", "conf", md5)
        with open("config.ini", "w") as f:
            config.write(f)
    except Exception as e:
        print(f"[Error] 配置文件写入失败：{e}")
        return

    try:
        jmd5 = re.search(r';md5;(\w+)"', content).group(1)
    except Exception as e:
        print(f"[Error] 提取 jar 的 MD5 失败：{e}")
        return

    try:
        current_md5 = config.get("md5", "jar").strip()
    except configparser.NoOptionError:
        current_md5 = ""
    except configparser.NoSectionError:
        config.add_section("md5")
        current_md5 = ""

    if jmd5 != current_md5:
        try:
            config.set("md5", "jar", jmd5)
            with open("config.ini", "w") as f:
                config.write(f)

            jar_response = requests.get(spider_url, timeout=10)
            jar_response.raise_for_status()

            os.makedirs("./JAR", exist_ok=True)
            with open("./JAR/fan.txt", "wb") as f:
                f.write(jar_response.content)

            print("[OK] 已成功更新 fan.txt 和配置。")
        except Exception as e:
            print(f"[Error] 下载或写入 fan.txt 文件失败：{e}")
            return
    else:
        print("Jar 文件未更新，无需重新下载。")

def diy_conf(content):
    content = content.replace('备用公众号【叨观荐影】', '豆瓣')
    pattern = r'{"key":"Bili"(.)*\n{"key":"Biliych"(.)*\n'
    replacement = ''
    content = re.sub(pattern, replacement, content)
    return content

def local_conf(content):
    pattern = r'{"key":"\d+看球"(.|\n)*(?={"key":"Aid")'
    replacement = r'{"key":"百度","name":"百度┃采集","type":1,"api":"https://api.apibdzy.com/api.php/provide/vod?ac=list","searchable":1,"filterable":0},\n{"key":"量子","name":"量子┃采集","type":0,"api":"https://cj.lziapi.com/api.php/provide/vod/at/xml/","searchable":1,"changeable":1},\n{"key":"非凡","name":"非凡┃采集","type":0,"api":"http://cj.ffzyapi.com/api.php/provide/vod/at/xml/","searchable":1,"changeable":1},\n{"key":"暴風","name":"暴風┃采集","type":1,"api":"https://bfzyapi.com/api.php/provide/vod/?ac=list","searchable":1,"changeable":1},\n{"key":"索尼","name":"索尼┃采集","type":1,"api":"https://suoniapi.com/api.php/provide/vod","searchable":1,"changeable":1},\n'
    content = re.sub(pattern, replacement, content)
    return content

if __name__ == '__main__':
    get_fan_conf()
