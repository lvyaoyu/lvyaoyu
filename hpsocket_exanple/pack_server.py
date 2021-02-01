# coding: utf-8
import json
import re
import time
import sys
import os
import enum
from json.decoder import JSONDecodeError

from hpsocket_exanple import utility
import requests
from urllib import parse

sys.path.append(os.getcwd())
sys.path.append(os.getcwd() + '/../')

from HPSocket import TcpPack
from HPSocket import helper
from HPSocket.TcpPack import HP_TcpPackServer
import HPSocket.pyhpsocket as HPSocket
from apscheduler.schedulers.blocking import BlockingScheduler

from decryption_img import WechatImageDecoder

scheduler = BlockingScheduler()

tail_count = 0


class Flag(enum.IntEnum):
    WECHAT_INFO_FLAG = 0x100
    QUERY_CONTACT_FLAG = 0x101
    CONTACT_INFO_FLAG = 0x102
    MSG_INFO_FLAG = 0x103
    SEND_MSG_FLAG = 0x104
    SEND_REPLY_FLAG = 0x105
    SEND_URL_FLAG = 0x106
    SEND_IMG_FLAG = 0x107
    SEND_VID_FLAG = 0x108
    DECRYPT_DB_FLAG = 0x109
    ACCEPT_FRIEND_FLAG = 0x10A
    CLOSE_WECHAT_FLAG = 0x10B
    QUERY_GROUP_FLAG = 0x10C
    GROUP_INFO_FLAG = 0x10D
    EXECUTE_JS_FLAG = 0x10E
    ADD_FRIEND2_FLAG = 0x10F
    QUERY_MEMBER_FLAG = 0x110
    MEMBER_INFO_FLAG = 0x111
    AT_MSG_FLAG = 0x112
    SEND_CARD_FLAG = 0x113
    OPEN_URL_FLAG = 0x114
    ADD_FRIEND_FLAG = 0x115
    DEL_FRIEND_FLAG = 0x116
    DEL_CHATROOM_MEMBER_FLAG = 0x117
    ADD_CHATROOM_MEMBER_FLAG = 0x118
    SET_CHATROOM_NAME_FLAG = 0x119
    SET_CHATROOM_ANNOUNCEMENT_FLAG = 0x11A
    EXECUTE_SQL_FLAG = 0x11B
    QUIT_CHATROOM_FLAG = 0x11C
    VERIFY_FRIEND_FLAG = 0x11D
    DOWN_IMG_FLAG = 0x11E
    DECODE_IMG_FLAG = 0x11F
    SQL_INFO_FLAG = 0x120
    REVOKE_MSG_FLAG = 0x121
    GET_CHATROOM_MEMBER_FLAG = 0x122
    SEND_GIF_FLAG = 0x123
    RECV_ROOM_FLAG = 0x124


class Server(HP_TcpPackServer):
    EventDescription = HP_TcpPackServer.EventDescription

    @EventDescription
    def OnPrepareListen(self, Sender, SocketHandler):
        print('开始绑定监听地址')

    @EventDescription
    def OnAccept(self, Sender, ConnID, Client):
        (ip, port) = HPSocket.HP_Server_GetRemoteAddress(Sender=Sender, ConnID=ConnID)
        print(ConnID, '已接受客户端的请求连接，ip:{}，port:{}'.format(ip, port))

    @EventDescription
    def OnSend(self, Sender, ConnID, Data):
        flag = int.from_bytes(Data[0:4], byteorder='little')
        data = Data[8:]
        data = utility.aes_decode(data, "money888money888")
        ret = utility.get_dict(data)
        print(ConnID, '标识：{}，已向客户端发送消息：{}'.format(flag, ret))

    @EventDescription
    def OnReceive(self, Sender, ConnID, Data):
        flag = int.from_bytes(Data[0:4], byteorder='little')
        if flag in [256, 294, ]:
            return
        data = Data[4:].decode()
        data = utility.aes_decode(data, "money888money888")
        ret = utility.get_dict(data)
        if ret.get('is_self') == 1:
            return
        print(ConnID, '标识：{}，已接收到客户端发来的消息：{}'.format(flag, ret))

        # 筛选是否为群聊
        if not ret.get('sender').endswith('@chatroom'):
            return
        # 筛选具体群聊
        if ret.get('sender') == '25573652600@chatroom':
            tail = ""
            global tail_count

            # 处理虚拟货币
            if ret.get('type') == 1:
                label = ret.get('msg').lower()
                try:
                    response = requests.get('http://rpa.uniner.com:5000/search/%s' % label)
                    data = json.loads(response.text)
                    # print(data)
                    amount = data["tick"]["amount"]
                    count = data['tick']['count']
                    open = data['tick']['open']
                    close = data['tick']['close']
                    low = data['tick']['low']
                    high = data['tick']['high']
                    vol = data['tick']['vol']
                    if tail_count % 5 == 0:
                        tail = "随机小尾巴广告 www.uniner.com"
                    tail_count += 1
                    msg = '[%s 滚动24小时行情\n' \
                          '----------------\n' \
                          '以基础币种计量的交易量    %s\n' \
                          '交易次数    %s\n' \
                          '本阶段开盘价    %s\n' \
                          '本阶段收盘价    %s\n' \
                          '本阶段最低价    %s\n' \
                          '本阶段最高价    %s\n' \
                          '以报价币种计量的交易量    %s\n' \
                          '----------------\n' \
                          '%s]'
                    msg = msg % (label.upper(), amount, count, open, close, low, high, vol, tail)
                    data = send_msg(ret.get('sender'), msg)

                except JSONDecodeError as e:
                    print(e)
                    data = send_msg(ret.get('sender'), '未知币种')
                finally:
                    self.Send(Sender=Sender, ConnID=ConnID, Data=data)

            # 处理图片
            if ret.get('type') == 3:
                src_path = ret.get('extra_data')
                if not os.path.isabs(src_path):
                    return
                images_path = r'C:\Users\EDZ\PycharmProjects\test\hpsocket_exanple\images'
                # print('dat文件路径', src_path)

                if not wait_file(src_path):
                    print(src_path, '未下载成功')
                    return
                wd = WechatImageDecoder(src_path, images_path)
                dst_path = wd.run()
                # print('解密文件路径', dst_path)
                if not wait_file(dst_path):
                    print(dst_path, '未解密成功')
                    return

                img_base64 = utility.get_file_base64(dst_path)

                access_token = "24.d318d985795054273d0546fa890567e8.2592000.1610267722.282335-23048184"
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                }
                args = "image=" + parse.quote(img_base64) + "&id_card_side=front"
                url = "https://aip.baidubce.com/rest/2.0/ocr/v1/idcard?access_token=" + access_token
                response = requests.post(url=url, headers=headers, data=args)
                data = json.loads(response.text)
                # print(data)
                # tab = data.encode('utf-8')
                name = data["words_result"]["姓名"]["words"]
                nation = data["words_result"]["民族"]["words"]
                address = data["words_result"]["住址"]["words"]
                id_card = data["words_result"]["公民身份号码"]["words"]
                born = data["words_result"]["出生"]["words"]
                sex = data["words_result"]["性别"]["words"]
                # print(name, sex, born, nation, address, id_card)
                if tail_count % 5 == 0:
                    tail = "随机小尾巴广告 www.uniner.com"
                tail_count += 1
                text = '[身份证信息\n' \
                       '----------\n' \
                       '姓名：%s\n' \
                       '性别：%s\n' \
                       '出生年月日：%s\n' \
                       '民族：%s\n' \
                       '住址：%s\n' \
                       '身份证号码：%s\n' \
                       '----------\n' \
                       '%s]' % (name, sex, born, nation, address, id_card, tail)
                data = send_msg(ret.get('sender'), text)
                self.Send(Sender=Sender, ConnID=ConnID, Data=data)

            # 处理位置信息
            if ret.get('type') == 48:
                # if not ret.get('thumb_path'):
                #     return
                msg = ret.get('msg')
                try:
                    lng = re.search('y="(.+?)"', msg).group(1)
                    lat = re.search('x="(.+?)"', msg).group(1)
                    print(lng, lat)
                    if tail_count % 5 == 0:
                        tail = "随机小尾巴广告 www.uniner.com"
                    tail_count += 1
                    text = '[经纬度查询\n' \
                           '----------\n' \
                           '经度：%s\n' \
                           '纬度：%s\n' \
                           '----------\n' \
                           '%s]' % (lng, lat, tail)
                    data = send_msg(ret.get('sender'), text)
                except Exception as e:
                    print(e)
                    data = '不是有效地址信息'
                finally:
                    self.Send(Sender=Sender, ConnID=ConnID, Data=data)

        if ret.get('sender') == '18551934675@chatroom':
            if ret.get('type') == 1 and (ret.get('msg') in ['时间','shijian','sj','time','Time','時間']):
                new_datetime = time.time()
                start_datetime = time.strptime('{} 09:30:00'.format(time.strftime('%Y-%m-%d', time.localtime())),
                                               "%Y-%m-%d %H:%M:%S")
                start_datetime = time.mktime(start_datetime)
                end_datetime = time.strptime('{} 18:30:00'.format(time.strftime('%Y-%m-%d', time.localtime())),
                                             "%Y-%m-%d %H:%M:%S")
                end_datetime = time.mktime(end_datetime)
                to_work_time_difference = int(start_datetime - new_datetime)
                off_work_time_difference = int(end_datetime - new_datetime)

                print(to_work_time_difference)
                print(off_work_time_difference)

                if to_work_time_difference >= 0:
                    msg = '距离上班班时间还有 %s 秒' % abs(to_work_time_difference)
                    data = send_msg(ret.get('sender'), msg)
                    self.Send(Sender=Sender, ConnID=ConnID, Data=data)
                elif to_work_time_difference < 0:
                    if off_work_time_difference >= 0:
                        msg = '距离下班时间还有 %s 秒' % off_work_time_difference
                    else:
                        msg = '已经加班 %s 秒' % abs(off_work_time_difference)
                    data = send_msg(ret.get('sender'), msg)
                    self.Send(Sender=Sender, ConnID=ConnID, Data=data)
        return HPSocket.EnHandleResult.HR_OK

    # @EventDescription
    def OnClose(self, Sender, ConnID, Operation, ErrorCode):
        (ip, port) = HPSocket.HP_Server_GetRemoteAddress(Sender=Sender, ConnID=ConnID)
        print(ConnID, '客户端已关闭连接，ip:{}，port:{}'.format(ip, port))
        return HPSocket.EnHandleResult.HR_OK

    @EventDescription
    def OnShutdown(self, Sender):
        print('服务器组件停止运行')


# def my_send(user_name, flag, request):
#     conn_id = g_clients[user_name]["conn_id"]
#
#     data = utility.get_json(request)
#     data = utility.aes_encode(data, "money888money888")
#     data = data.encode()
#     data = flag.to_bytes(4, 'little') + data
#     g_server.Send(Sender=g_server.Server, ConnID=conn_id, Data=data)
#
#
# def my_recv(data):
#     data = data[4:].decode()
#     data = utility.aes_decode(data, "money888money888")
#     response = utility.get_dict(data)
#     return response

def send_msg(user_name, text):
    data = utility.get_json({'user_name': user_name, 'text': text})
    data = utility.aes_encode(data, "money888money888")
    data = data.encode()
    data = Flag.SEND_MSG_FLAG.to_bytes(4, 'little') + data
    return data


def send_img(user_name, file_path):
    data = utility.get_json({'user_name': user_name,
                             'file_path': file_path})
    data = utility.aes_encode(data, "money888money888")
    data = data.encode()
    data = Flag.SEND_IMG_FLAG.to_bytes(4, 'little') + data
    return data


def send_gif(user_name, file_path):
    data = utility.get_json({'user_name': user_name,
                             'file_path': file_path})
    data = utility.aes_encode(data, "money888money888")
    data = data.encode()
    data = Flag.SEND_GIF_FLAG.to_bytes(4, 'little') + data
    return data


def send_vid(user_name, file_path):
    data = utility.get_json({'user_name': user_name,
                             'file_path': file_path})
    data = utility.aes_encode(data, "money888money888")
    data = data.encode()
    data = Flag.SEND_VID_FLAG.to_bytes(4, 'little') + data
    return data


def send_url(user_name, xml):
    data = utility.get_json({'user_name': user_name,
                             'xml': xml})
    data = utility.aes_encode(data, "money888money888")
    data = data.encode()
    data = Flag.DECRYPT_DB_FLAG.to_bytes(4, 'little') + data
    return data


def decode_img(src_path, dst_path):
    data = utility.get_json({'src_path': src_path,
                             'dst_path': dst_path})
    data = utility.aes_encode(data, "money888money888")
    data = data.encode()
    data = Flag.SEND_URL_FLAG.to_bytes(4, 'little') + data
    return data


def wait_file(file_path):
    for i in range(10):
        try:
            os.rename(src=file_path, dst=file_path)
            return True
        except:
            time.sleep(0.5)
    else:
        return False


# def forward_msg(user_name,local_id):
#     data = utility.get_json({'user_name': user_name,
#                              'local_id': local_id})
#     data = utility.aes_encode(data, "money888money888")
#     data = data.encode()
#     data = Flag.SEND_URL_FLAG.to_bytes(4, 'little') + data
#     return data


if __name__ == '__main__':
    server = Server()
    print('开始启动服务器')
    server.Start(host='0.0.0.0', port=61811, head_flag=0x169, size=0x3FFFFF)
    while True:
        time.sleep(1)
