# coding=utf-8
import time
import urllib
from httplib2 import Http
import os
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

try:
    import urllib2 as wdf_urllib
    from cookielib import CookieJar
except ImportError:
    import urllib.request as wdf_urllib
    from http.cookiejar import CookieJar

import re
import time
import xml.dom.minidom
import json
import sys
import math
import subprocess


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

fn_qrcode = os.path.join(BASE_DIR, 'qrcode.jpg')

h = Http(timeout=5)

headers_templates = {
    'Connection': 'keep-alive',
    'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64)'
                   'AppleWebKit/537.36 (KHTML, like Gecko)'
                   'Chrome/44.0.2403.125 Safari/537.36'),
    'Accept': '*/*',
    'Accept-Charset': 'UTF-8,*;q=0.5',
    'Accept-Encoding': 'gzip',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'DNT': '1',
}


DEBUG = False

MAX_GROUP_NUM = 35  # 每组人数
INTERFACE_CALLING_INTERVAL = 16  # 接口调用时间间隔, 值设为13时亲测出现"操作太频繁"
MAX_PROGRESS_LEN = 50


tip = 0
uuid = ''

base_uri = ''
redirect_uri = ''

skey = ''
wxsid = ''
wxuin = ''
pass_ticket = ''
deviceId = 'e000000000000000'

BaseRequest = {}

ContactList = []
My = []

try:
    xrange
    range = xrange
except:
    # python 3
    pass


def getRequest(url, data=None):
    try:
        data = data.encode('utf-8')
    except:
        pass
    finally:
        return wdf_urllib.Request(url=url, data=data)


def get_uuid():
    url = 'https://login.weixin.qq.com/jslogin'

    body = urllib.urlencode({
        'appid': 'wx782c26e4c19acffb',
        'fun': 'new',
        'lang': 'en_US',
        '_': int(1000*time.time()),
        })

    rsp, content = h.request(url, 'POST', headers=headers_templates, body=body)

    _prog = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
    m = re.search(_prog, content)
    if m is not None and m.group(1) == '200':
        return m.group(2)
    return None


def get_qrcode(uuid, filename):
    url = 'https://login.weixin.qq.com/qrcode/{}'.format(uuid)
    rsp, content = h.request(url)

    with open(filename, 'wb') as f:
        f.write(content)


def open_qrcode(filename):
    if sys.platform.find('darwin') >= 0:
        subprocess.call(['open', filename])
    elif sys.platform.find('linux') >= 0:
        subprocess.call(['xdg-open', filename])
    else:
        os.startfile(filename)


def is_login(uuid):
    url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login'
    body = 'uuid=%s&tip=0&_=%s' % (uuid, int(1000*time.time()))

    lh = Http(timeout=30)
    rsp, content = lh.request('%s?%s' % (url, body))

    _prog = r'window.code=(\d+);(?:\s+window.redirect_uri="(\S+?)";)?'

    m = re.search(_prog, content)
    if m is not None:
        code = m.group(1)
        if code == '200':  # 已登录
            print('正在登录...')
            return m.group(2)  # redirect_uri
        if code == '201':  # 已扫描
            print('成功扫描, 请在手机上点击确认以登录')
    return None


def login():
    global skey, wxsid, wxuin, pass_ticket, BaseRequest

    request = getRequest(url=redirect_uri)
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    '''
        <error>
            <ret>0</ret>
            <message>OK</message>
            <skey>xxx</skey>
            <wxsid>xxx</wxsid>
            <wxuin>xxx</wxuin>
            <pass_ticket>xxx</pass_ticket>
            <isgrayscale>1</isgrayscale>
        </error>
    '''

    doc = xml.dom.minidom.parseString(data)
    root = doc.documentElement

    for node in root.childNodes:
        if node.nodeName == 'skey':
            skey = node.childNodes[0].data
        elif node.nodeName == 'wxsid':
            wxsid = node.childNodes[0].data
        elif node.nodeName == 'wxuin':
            wxuin = node.childNodes[0].data
        elif node.nodeName == 'pass_ticket':
            pass_ticket = node.childNodes[0].data

    # print('skey: %s, wxsid: %s, wxuin: %s, pass_ticket: %s' % (skey, wxsid,
    # wxuin, pass_ticket))

    if not all((skey, wxsid, wxuin, pass_ticket)):
        return False

    BaseRequest = {
        'Uin': int(wxuin),
        'Sid': wxsid,
        'Skey': skey,
        'DeviceID': deviceId,
    }

    return True


def webwxinit():

    url = base_uri + \
        '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
            pass_ticket, skey, int(time.time()))
    params = {
        'BaseRequest': BaseRequest
    }

    request = getRequest(url=url, data=json.dumps(params))
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    if DEBUG:
        f = open(os.path.join(os.getcwd(), 'webwxinit.json'), 'wb')
        f.write(data)
        f.close()

    # print(data)

    global ContactList, My
    dic = json.loads(data)
    ContactList = dic['ContactList']
    My = dic['User']

    ErrMsg = dic['BaseResponse']['ErrMsg']
    if DEBUG:
        print("Ret: %d, ErrMsg: %s" % (dic['BaseResponse']['Ret'], ErrMsg))

    Ret = dic['BaseResponse']['Ret']
    if Ret != 0:
        return False

    return True


def webwxgetcontact():

    url = base_uri + \
        '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
            pass_ticket, skey, int(time.time()))

    request = getRequest(url=url)
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    data = response.read()

    if DEBUG:
        f = open(os.path.join(os.getcwd(), 'webwxgetcontact.json'), 'wb')
        f.write(data)
        f.close()

    # print(data)
    data = data.decode('utf-8', 'replace')

    dic = json.loads(data)
    MemberList = dic['MemberList']

    # 倒序遍历,不然删除的时候出问题..
    SpecialUsers = ["newsapp", "fmessage", "filehelper", "weibo", "qqmail", "tmessage", "qmessage", "qqsync", "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp", "blogapp", "facebookapp", "masssendapp",
                    "meishiapp", "feedsapp", "voip", "blogappweixin", "weixin", "brandsessionholder", "weixinreminder", "wxid_novlwrv3lqwv11", "gh_22b87fa7cb3c", "officialaccounts", "notification_messages", "wxitil", "userexperience_alarm"]
    for i in range(len(MemberList) - 1, -1, -1):
        Member = MemberList[i]
        if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
            MemberList.remove(Member)
        elif Member['UserName'] in SpecialUsers:  # 特殊账号
            MemberList.remove(Member)
        elif Member['UserName'].find('@@') != -1:  # 群聊
            MemberList.remove(Member)
        elif Member['UserName'] == My['UserName']:  # 自己
            MemberList.remove(Member)

    return MemberList


def createChatroom(UserNames):
    # MemberList = []
    # for UserName in UserNames:
        # MemberList.append({'UserName': UserName})
    MemberList = [{'UserName': UserName} for UserName in UserNames]

    url = base_uri + \
        '/webwxcreatechatroom?pass_ticket=%s&r=%s' % (
            pass_ticket, int(time.time()))
    params = {
        'BaseRequest': BaseRequest,
        'MemberCount': len(MemberList),
        'MemberList': MemberList,
        'Topic': '',
    }

    request = getRequest(url=url, data=json.dumps(params))
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    dic = json.loads(data)
    ChatRoomName = dic['ChatRoomName']
    MemberList = dic['MemberList']
    DeletedList = []
    for Member in MemberList:
        if Member['MemberStatus'] == 4:  # 被对方删除了
            DeletedList.append(Member['UserName'])

    ErrMsg = dic['BaseResponse']['ErrMsg']
    if DEBUG:
        print("Ret: %d, ErrMsg: %s" % (dic['BaseResponse']['Ret'], ErrMsg))

    return ChatRoomName, DeletedList


def deleteMember(ChatRoomName, UserNames):
    url = base_uri + \
        '/webwxupdatechatroom?fun=delmember&pass_ticket=%s' % (pass_ticket)
    params = {
        'BaseRequest': BaseRequest,
        'ChatRoomName': ChatRoomName,
        'DelMemberList': ','.join(UserNames),
    }

    request = getRequest(url=url, data=json.dumps(params))
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    dic = json.loads(data)
    ErrMsg = dic['BaseResponse']['ErrMsg']
    Ret = dic['BaseResponse']['Ret']
    if DEBUG:
        print("Ret: %d, ErrMsg: %s" % (Ret, ErrMsg))

    if Ret != 0:
        return False

    return True


def addMember(ChatRoomName, UserNames):
    url = base_uri + \
        '/webwxupdatechatroom?fun=addmember&pass_ticket=%s' % (pass_ticket)
    params = {
        'BaseRequest': BaseRequest,
        'ChatRoomName': ChatRoomName,
        'AddMemberList': ','.join(UserNames),
    }

    request = getRequest(url=url, data=json.dumps(params))
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    dic = json.loads(data)
    MemberList = dic['MemberList']
    DeletedList = []
    for Member in MemberList:
        if Member['MemberStatus'] == 4:  # 被对方删除了
            DeletedList.append(Member['UserName'])

    ErrMsg = dic['BaseResponse']['ErrMsg']
    if DEBUG:
        print("Ret: %d, ErrMsg: %s" % (dic['BaseResponse']['Ret'], ErrMsg))

    return DeletedList


def main():

    try:
        opener = wdf_urllib.build_opener(
            wdf_urllib.HTTPCookieProcessor(CookieJar()))
        wdf_urllib.install_opener(opener)
    except:
        pass

    uuid = get_uuid()
    if not uuid:
        print('获取uuid失败')
        return

    get_qrcode(uuid, fn_qrcode)
    open_qrcode(fn_qrcode)

    print('请使用微信扫描二维码以登录')
    time.sleep(1)

    while True:
        redirect_uri = is_login(uuid)
        if redirect_uri:
            break

    os.remove(fn_qrcode)

    return

    if not login():
        print('登录失败')
        return

    if not webwxinit():
        print('初始化失败')
        return

    MemberList = webwxgetcontact()

    MemberCount = len(MemberList)
    print('通讯录共%s位好友' % MemberCount)

    ChatRoomName = ''
    result = []
    d = {}
    for Member in MemberList:
        d[Member['UserName']] = (Member['NickName'].encode(
            'utf-8'), Member['RemarkName'].encode('utf-8'))

    print('开始查找...')

    group_num = int(math.ceil(MemberCount / float(MAX_GROUP_NUM)))
    for i in range(0, group_num):
        UserNames = []
        for j in range(0, MAX_GROUP_NUM):
            if i * MAX_GROUP_NUM + j >= MemberCount:
                break
            Member = MemberList[i * MAX_GROUP_NUM + j]
            UserNames.append(Member['UserName'])

        # 新建群组/添加成员
        if ChatRoomName == '':
            (ChatRoomName, DeletedList) = createChatroom(UserNames)
        else:
            DeletedList = addMember(ChatRoomName, UserNames)

        DeletedCount = len(DeletedList)
        if DeletedCount > 0:
            result += DeletedList

        # 删除成员
        deleteMember(ChatRoomName, UserNames)

        # 进度条
        progress_len = MAX_PROGRESS_LEN
        progress = '-' * progress_len
        progress_str = '%s' % ''.join(
            map(lambda x: '#', progress[:(progress_len * (i + 1)) / group_num]))
        print(''.join(
            ['[', progress_str, ''.join('-' * (progress_len - len(progress_str))), ']']))
        print('新发现你被%d人删除' % DeletedCount)
        for i in range(DeletedCount):
            if d[DeletedList[i]][1] != '':
                print(d[DeletedList[i]][0] + '(%s)' % d[DeletedList[i]][1])
            else:
                print(d[DeletedList[i]][0])

        if i != group_num - 1:
            print('正在继续查找,请耐心等待...')
            # 下一次进行接口调用需要等待的时间
            time.sleep(INTERFACE_CALLING_INTERVAL)
    # todo 删除群组

    print('\n结果汇总完毕,20s后可重试...')
    resultNames = []
    for r in result:
        if d[r][1] != '':
            resultNames.append(d[r][0] + '(%s)' % d[r][1])
        else:
            resultNames.append(d[r][0])

    print('---------- 被删除的好友列表(共%d人) ----------' % len(result))
    # 过滤emoji
    resultNames = map(lambda x: re.sub(r'<span.+/span>', '', x), resultNames)
    if len(resultNames):
        print('\n'.join(resultNames))
    else:
        print("无")
    print('---------------------------------------------')


if __name__ == '__main__':
    main()
