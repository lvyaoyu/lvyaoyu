# coding: utf-8
import time
import sys
import os
import enum

from hpsocket_exanple import utility

sys.path.append(os.getcwd())
sys.path.append(os.getcwd() + '/../')

from HPSocket import TcpPack
from HPSocket.TcpPack import HP_TcpPackClient, HP_TcpPackServer
import HPSocket.pyhpsocket as HPSocket


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


class Client(HP_TcpPackClient):
    counter = 0
    EventDescription = HP_TcpPackServer.EventDescription

    @EventDescription
    def OnPrepareConnect(self, Sender, ConnID, Socket):
        print('准备连接服务器')

    @EventDescription
    def OnConnect(self, Sender, ConnID):
        print('服务器连接成功')

    @EventDescription
    def OnSend(self, Sender, ConnID, Data):
        flag = int.from_bytes(Data[0:4], byteorder='little')
        data = Data[8:]
        data = utility.aes_decode(data, "money888money888")
        ret = utility.get_dict(data)
        print(ConnID, '标识：{}，已向服务端发送消息：{}'.format(flag, ret))

    @EventDescription
    def OnReceive(self, Sender, ConnID, Data):
        flag = int.from_bytes(Data[0:4], byteorder='little')
        # print(flag,type(flag))
        if flag in [256, 294, ]:
            return
        data = Data[4:].decode()
        data = utility.aes_decode(data, "money888money888")
        ret = utility.get_dict(data)
        print(ConnID, '标识：{}，已接收到服务器发来的消息：{}'.format(flag, ret))

    @EventDescription
    def OnClose(self, Sender, ConnID, Operation, ErrorCode):
        print('服务器已关闭连接')

    def SendTest(self, Data):
        # self.counter += 1
        # # self.Send(self.Client, Data)

        data = utility.get_json({'user_name': "wxid_thfmvxhuch0x22", 'text': Data})
        print(data)
        data = utility.aes_encode(data, "money888money888")
        data = data.encode()
        data = Flag.SEND_MSG_FLAG.to_bytes(4, 'little') + data
        # print(data)
        self.Send(Sender=self.Client, Data=data)


if __name__ == '__main__':
    client = Client()
    client.Start(host='127.0.0.1', port=49449, head_flag=0x169, size=0x3FFFFF)
    while True:
        time.sleep(0.2)
        data = input('请输入发送内容：')
        client.SendTest(data)
