import datetime
import json
import os
import random
from math import ceil

import requests
from bs4 import BeautifulSoup
from flask import Flask, request

app = Flask(__name__)

app.json.ensure_ascii = False

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}


def get_punch_gps(punch_id, class_id, cookie=None):
    lat = 23.123456
    lng = 123.123456
    w = "auto"
    punch_url = f"http://k8n.cn/student/punchs/course/{class_id}/{punch_id}"
    headers['referer'] = f"https://k8n.cn/student/course/{class_id}"
    headers[
        'user-agent'] = "Mozilla/5.0 (Linux; Android 13.1.2; Nexus 5 Build/N2G47H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Safari/537.36 XWEB/1160083 MMWEBSDK/20230701 MMWEBID/2984 MicroMessenger/8.0.40.2420(0x28002837) WeChat/arm64 Weixin Android Tablet NetType/WIFI Language/zh_CN ABI/arm64"
    headers['content-type'] = 'application/x-www-form-urlencoded'
    headers["cookie"] = cookie
    response = requests.get(punch_url, headers=headers)
    # print(response.text)
    soup = BeautifulSoup(response.text, 'html.parser')
    script_element = soup.find("script", string=lambda text: text and "var gpsranges =" in text)
    # print(script_element)
    if script_element:
        script_content = script_element.string

        start_index = script_content.find("[[")
        end_index = script_content.find("]]") + 2

        gpsranges_data = script_content[start_index:end_index]
        # print(gpsranges_data)
        gpsranges_array = json.loads(gpsranges_data)
        # print(gpsranges_array)
        if gpsranges_array:
            lat = gpsranges_array[0][0]
            lng = gpsranges_array[0][1]
    else:
        print("定位设置获取失败，已使用默认配置！")
        #gpsranges = [["23.123456","123.123456",50]];
    if 23.12345<float(lat)<23.23456 and 123.12345<float(lng)<123.23456: # 宿舍签到，使用宿舍位置
        lat = 31.8253200
        lng = 123.4233700
        w = "寝室"
    return [float(lat), float(lng), w]


def go_punch(punch_id, lat, lng, class_id=None, user=None):
    print(f"{punch_id}, {lat}, {lng} going punch:")
    # 初始值
    acc = 0.030840206891298294
    # 随机变化值
    change_value = 0.00003

    # 随机变化
    lat += random.uniform(-change_value, change_value)
    lng += random.uniform(-change_value, change_value)
    acc += random.uniform(-change_value - 0.05, change_value + 0.05)

    punch_url = f"http://k8n.cn/student/punchs/course/{class_id}/{punch_id}"
    headers['referer'] = f"https://k8n.cn/student/course/{class_id}"
    headers["cookie"] = user['cookie']
    headers[
        'user-agent'] = "Mozilla/5.0 (Linux; Android 13.1.2; Nexus 5 Build/N2G47H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Safari/537.36 XWEB/1160083 MMWEBSDK/20230701 MMWEBID/2984 MicroMessenger/8.0.40.2420(0x28002837) WeChat/arm64 Weixin Android Tablet NetType/WIFI Language/zh_CN ABI/arm64"
    headers['content-type'] = 'application/x-www-form-urlencoded'
    # print(user['res'])
    post_data_str = f"id={punch_id}&lat={lat}&lng={lng}&acc={acc}&res=&gps_addr=&res={user['res']}"
    response = requests.post(punch_url, headers=headers, data=post_data_str)
    # print(response.text)
    soup = BeautifulSoup(response.text, 'html.parser')

    title_element = soup.find("h1", id="title")

    if title_element:
        title_content = title_element.get_text()
        # print(title_content)
        return title_content
    else:
        # print("去签到 失败")
        return 'go_punch error'


@app.route('/', methods=['GET'])
def index():
    print("\n----------------------------------")
    classid = request.args.get('classid', default=None, type=int)
    user = request.args.get('user', default=None, type=str)
    if user:
        try:
            d = os.path.join(os.getcwd(), "cookies", f"{user}.json")
            user = open(d, 'r').read()
            user = json.loads(user)
            # print(user['res'])
        except OSError as e:
            print(e)
            datas = "无此用户"
            return datas
    else:
        datas = "请输入用户"
        return datas
    if classid:
        # now = datetime.datetime.now()
        # hour = 9
        # if now.hour < hour:
        #     datas = f"当前时间不在打卡范围内，请在{hour}时后操作！"
        #     print(datas)
        #     return datas
        datas = punch(classid, user)
        return datas
    else:
        print('请输入班级id')
        return '请输入班级id'


def punch(class_id, user):
    result = {'class_id': class_id, 'punch_data':{}, 'msg': None}

    current_time = datetime.datetime.now()
    result['time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")

    url = f"https://k8n.cn/student/course/{class_id}/punchs"
    # print(url)
    headers["cookie"] = user['cookie']
    response = requests.get(url, headers=headers)

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, 'html.parser')
    # print(soup)
    layui_fluid_content = soup.find(class_="layui-fluid")
    if layui_fluid_content:
        punch_id = punch_status = None
        layui_col_xs6_elements = layui_fluid_content.find_all(class_="layui-col-xs6")

        for element in layui_col_xs6_elements[:1]:
            # print(element)
            # print("\n----------------------------\n")
            card = element.find(class_="card")
            card_body = element.find(class_="card-body")
            span_time_element = element.find(class_="countdown")
            # div_type = element.find(class_="subtitle")
            span_element = element.find(class_="layui-badge")
            if card:
                card_onclick = card.get("onclick")
                if card_onclick:
                    # punch_gps_photo(2308764,'')
                    card_onclick = card_onclick.split("(")[0]
                    if card_onclick == "punch_gps_photo":
                        result['punch_data']['type'] = "GPS+照片"
                    else:
                        result['punch_data']['type'] = "GPS"
            else:
                msg = "没有找到签到类型"
            if card_body:
                card_body_id = card_body.get("id")
                punch_id = card_body_id.split("_")[1]
                result['punch_data']["id"] = punch_id
                # print("签到ID：", punch_id)
            else:
                msg = "没有找到签到ID"
                print(msg)
            if span_time_element:
                countdown_time = span_time_element.get_text()
                countdown_time = datetime.datetime.strptime(countdown_time, "%Y-%m-%d %H:%M:%S")
                time_difference_seconds = (countdown_time - current_time).total_seconds()
                mins = time_difference_seconds / 60
                result['punch_data']['msg'] = f"{ceil(mins)}分钟后结束"
            else:
                msg = "没有找到结束时间"
            # if div_type:
            #     punch_type = div_type.get_text()
            #     punch_type = punch_type.split(" ")
            #     punch_type = punch_type[0]
            #     result['punch_data']['type'] = punch_type.replace("\n", "")
            # else:
            #     msg = "没有找到签到类型"
            if span_element:
                punch_status = span_element.get_text()
                result['punch_data']["status"] = punch_status
                # print("签到状态：", punch_status)
            else:
                msg = "没有找到签到状态"
        # print(msg)

        if punch_id and punch_status == "未签":
            lat, lng, w = get_punch_gps(punch_id, class_id, user['cookie'])
            msg = go_punch(punch_id, lat, lng, class_id, user)
            # msg= "1"
            if msg == "签到成功":
                result['punch_data']["status"] = "签到成功"
            result["w"] = w
            result["msg"] = msg
        else:
            msg = "没有需要签到的"
            # print(msg)
            result["msg"] = msg

    else:
        msg_title = soup.find(class_="weui-msg__title")
        if msg_title:
            # 获取签到id失败，layui_fluid_content没找到
            msg_title= msg_title.get_text()
            msg_title = f"{msg_title}，可能classid填写错误"
        else:
            # 啥也没获取到，cookie失效
            msg_title = "未知错误，可能cookie已失效"
        result["msg"] = msg_title
        print("get_punch error, msg:"+msg_title)
        
    print(result)
    return result


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1234, debug=False)
