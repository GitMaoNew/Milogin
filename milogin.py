#!/usr/bin/env python
# coding=utf-8
# code by 92ez.com

import requests
from Crypto.Hash import SHA
import random
import time
import json
import sys
import re

reload(sys)
sys.setdefaultencoding('utf8')


def getToken(host):

    homeRequest = requests.get('http://' + host + '/cgi-bin/luci/web/home')
    key = re.findall(r'key: \'(.*)\',', homeRequest.text)[0]
    mac = re.findall(r'deviceId = \'(.*)\';', homeRequest.text)[0]

    aimurl = "http://" + host + "/cgi-bin/luci/api/xqsystem/login"
    nonce = "0_" + mac + "_" + str(int(time.time())) + "_" + str(random.randint(1000, 10000))
    pwdtext = sys.argv[2]

    pwd = SHA.new()
    pwd.update(pwdtext + key)
    hexpwd1 = pwd.hexdigest()

    pwd2 = SHA.new()
    pwd2.update(nonce + hexpwd1)
    hexpwd2 = pwd2.hexdigest()

    data = {
        "logtype": 2,
        "nonce": nonce,
        "password": hexpwd2,
        "username": "admin"
    }

    response = requests.post(url=aimurl, data=data, timeout=5)
    resjson = json.loads(response.content)

    if resjson['code'] == 0:
        return resjson['token']
    else:
        return False


def getInfo(host, token):

    base_url = 'http://' + host + '/cgi-bin/luci/;stok=' + token + '/api/misystem/status'
    wan_url = 'http://' + host + '/cgi-bin/luci/;stok=' + token + '/api/xqnetwork/wan_info'
    stop_url = 'http://' + host + '/cgi-bin/luci/;stok=' + token + '/api/xqnetwork/pppoe_stop'
    start_url = 'http://' + host + '/cgi-bin/luci/;stok=' + token + '/api/xqnetwork/pppoe_start'
    pppoe_url = 'http://' + host + '/cgi-bin/luci/;stok=' + token + '/api/xqnetwork/pppoe_status'
    reboot_url = 'http://' + host + '/cgi-bin/luci/;stok=' + token + '/api/xqnetwork/reboot?client=web'

    getStatus(base_url)
    getWanInfo(wan_url)

    action = sys.argv[3]

    if action == 'reconnect':
        doReconnect(stop_url, start_url, pppoe_url)
    elif action == 'restart':
        doReboot(reboot_url)
    else:
        pass


def getStatus(url):
    try:
        statusInfo = json.loads(requests.get(url,timeout=5).content)
        devList = statusInfo['dev']

        print '[CPU]: ' + str(statusInfo['cpu']['core']) + '核   ' + statusInfo['cpu']['hz'] + '   系统负载 ' + str(statusInfo['cpu']['load'])
        print '[MAC]: ' + statusInfo['hardware']['mac']
        print '[MEM]: Type: ' + statusInfo['mem']['type'] + '   Total: ' + statusInfo['mem']['total'] + '   Usage: ' + str(statusInfo['mem']['usage']*100) + '% \n'
        print '--------------------[DEV]----------------------\n'
        for dev in devList:
            print dev['mac'] + ' ' + dev['devname']
    except Exception,e:
        print e


def getWanInfo(url):
    try:
        wanInfo = json.loads(requests.get(url,timeout=5).content)
        print '\n--------------------[WAN]----------------------\n'
        print '用户: ' + wanInfo['info']['details']['username']
        print '密码: ' + wanInfo['info']['details']['password']
        print '类型: ' + wanInfo['info']['details']['wanType']
        print 'IP地址: ' + wanInfo['info']['ipv4'][0]['ip']
        print '网关: ' + wanInfo['info']['gateWay']
        print 'DNS: ' + wanInfo['info']['dnsAddrs']+ ',' +wanInfo['info']['dnsAddrs1']
    except Exception,e:
        print e


def doReconnect(stop,start,pppoe):
    print '\n-----------------[Reconnect]-------------------\n'
    try:
        currentip = json.loads(requests.get(pppoe, timeout=5).content)['ip']['address']
        print 'Current ip is ' + currentip
        stopInfo = json.loads(requests.get(stop,timeout=5).content)
        if stopInfo['code'] == 0:
            print 'Sleep 3s...'
            time.sleep(3)
            startInfo = json.loads(requests.get(start, timeout=5).content)
            if startInfo['code'] == 0:
                print 'Opration success... sleep 8s ...'
                time.sleep(8)
                newip = json.loads(requests.get(pppoe,timeout=5).content)['ip']['address']
                print 'Success! New ip is ' +newip
            else:
                print 'Failed!'
        else:
            print 'Failed!'
    except Exception,e:
        print e


def doReboot(url):
    try:
        reboot = json.loads(requests.get(url, timeout=5).content)

        if reboot['code'] == 0:
            print 'Rebooting...'
        else:
            print 'Reboot failed!'
    except Exception,e:
        print e

if __name__ == '__main__':
    print '\n########### Login Mi Router Test Py ############'
    print '		Author 92ez.com'
    print '################################################\n'

    host = sys.argv[1]
    token = getToken(host)

    if token:
        getInfo(host, token)
    else:
        print 'Login failed!'
