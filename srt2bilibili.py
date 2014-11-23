#!/usr/bin/env python
#coding:utf-8
# Author:  Beining --<ACICFG>
# Purpose: A batch poster of srt file to danmaku on Bilibili.
# Created: 11/23/2014
# srt2Bilibili is licensed under GNUv2 license
'''
srt2Bilibili 0.0.1
Beining@ACICFG
cnbeining[at]gmail.com
http://www.cnbeining.com
https://github.com/cnbeining/srt2bilibili
GNUv2 license
'''

import sys
import os
import random
import requests
import urllib
import pysrt
import logging
import hashlib
import time as time_old
import getopt


from xml.dom.minidom import parse, parseString
import xml.dom.minidom

global FAKE_HEADER, APPKEY, SECRETKEY, VER, rnd, cid

FAKE_HEADER = {
    'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'}
APPKEY = '85eb6835b0a1034e'
SECRETKEY = '2ad42749773c441109bdc0191257a664'
VER = '0.01'



#----------------------------------------------------------------------
def calc_sign(string):
    """str/any->str
    return MD5.
    From: Biligrab, https://github.com/cnbeining/Biligrab
    MIT License"""
    return str(hashlib.md5(str(string).encode('utf-8')).hexdigest())

#----------------------------------------------------------------------
def find_cid_api(vid, p):
    """find cid and print video detail
    str,int?,str->str
    TODO: Use json.
    From: Biligrab, https://github.com/cnbeining/Biligrab
    MIT License"""
    cid = 0
    if str(p) is '0' or str(p) is '1':
        str2Hash = 'appkey={APPKEY}&id={vid}&type=xml{SECRETKEY}'.format(APPKEY = APPKEY, vid = vid, SECRETKEY = SECRETKEY)
        biliurl = 'https://api.bilibili.com/view?appkey={APPKEY}&id={vid}&type=xml&sign={sign}'.format(APPKEY = APPKEY, vid = vid, SECRETKEY = SECRETKEY, sign = calc_sign(str2Hash))
    else:
        str2Hash = 'appkey={APPKEY}&id={vid}&page={p}&type=xml{SECRETKEY}'.format(APPKEY = APPKEY, vid = vid, p = p, SECRETKEY = SECRETKEY)
        biliurl = 'https://api.bilibili.com/view?appkey={APPKEY}&id={vid}&page={p}&type=xml&sign={sign}'.format(APPKEY = APPKEY, vid = vid, SECRETKEY = SECRETKEY, p = p, sign = calc_sign(str2Hash))
    logging.debug(biliurl)
    logging.info('Fetching webpage...')
    try:
        request = urllib.request.Request(biliurl, headers=BILIGRAB_HEADER)
        response = urllib.request.urlopen(request)
        data = response.read()
        dom = parseString(data)
        for node in dom.getElementsByTagName('cid'):
            if node.parentNode.tagName == "info":
                cid = node.toxml()[5:-6]
                logging.info('cid is ' + cid)
                break
        return cid
    except:  # If API failed
        logging.warning('Cannot connect to API server! \nIf you think this is wrong, please open an issue at \nhttps://github.com/cnbeining/Biligrab/issues with *ALL* the screen output, \nas well as your IP address and basic system info.')
        return 0

#----------------------------------------------------------------------
def convert_cookie(cookie_raw):
    """str->dict
    'DedeUserID=358422; DedeUserID__ckMd5=72682a6838d150dd; SESSDATA=72e0ee97%2C1419212650%2C6b47a180'
    cookie = {'DedeUserID': 358422, 'DedeUserID__ckMd5': '72682a6838d150dd', 'SESSDATA': '72e0ee97%2C1419212650%2C6b47a180'}"""
    cookie = {}
    logging.debug('Raw Cookie: ' + cookie_raw)
    for i in [i.strip() for i in cookie_raw.split(';')]:
        cookie[i.split('=')[0]] = i.split('=')[1]
    return cookie

#----------------------------------------------------------------------
def getdate():
    """None->str
    2014-11-23 10:39:46"""
    return time_old.strftime("%Y-%m-%d %X", time_old.localtime())

#----------------------------------------------------------------------
def post_one(message, rnd, cid, cookie, fontsize = 25, mode = 1, color = 16777215, playTime = 0, pool = 0):
    """
    PARS NOT THE PERFECT SAME AS A PAYLOAD!"""
    headers = {'Origin': 'http://static.hdslb.com', 'X-Requested-With': 'ShockwaveFlash/15.0.0.223', 'Referer': 'http://static.hdslb.com/play.swf', 'User-Agent': BILIGRAB_UA, 'Host': 'interface.bilibili.com', 'Content-Type': 'application/x-www-form-urlencoded', 'Cookie': cookie}
    url = 'http://interface.bilibili.com/dmpost'
    try:
        date = getdate()
        payload = {'fontsize': int(fontsize), 'message': str(message), 'mode': int(mode), 'pool': pool, 'color': int(color), 'date': str(date), 'rnd': int(rnd), 'playTime': playTime, 'cid': int(cid)}
        encoded_args = urllib.parse.urlencode(payload)
        r = requests.post(url, data = encoded_args, headers = headers)
        #print(r.text)
        if int(r.text) <= 0:
            logging.warning('Line failed:')
            logging.warning('Message:' + str(message))
        else:
            print(message)
        #logging.info(message)
    except Exception as e:
        print('ERROR: Line failed: %s' % e)
        print('Payload:' + str(payload))
        pass


#----------------------------------------------------------------------
def timestamp2sec(timestamp):
    """"""
    return (int(timestamp.seconds) + 60 * int(timestamp.minutes) + 3600 * int(timestamp.hours) + float(int(timestamp.hours) / 1000))


#----------------------------------------------------------------------
def read_cookie(cookiepath):
    """str->list
    Original target: set the cookie
    Target now: Set the global header
    From: Biligrab, https://github.com/cnbeining/Biligrab
    MIT License"""
    global BILIGRAB_HEADER
    try:
        cookies_file = open(cookiepath, 'r')
        cookies = cookies_file.readlines()
        cookies_file.close()
        # print(cookies)
        return cookies
    except:
        print('WARNING: Cannot read cookie, may affect some videos...')
        return ['']

#----------------------------------------------------------------------
def main(srt, fontsize, mode, color, cookie, aid, p = 1, cool = 2, pool = 0):
    """str,int,int,int,str,int,int,int,int->None"""
    rnd = int(random.random() * 1000000000)
    cid = int(find_cid_api(aid, p))
    subs = pysrt.open(srt)
    for sub in subs:
        #lasttime = timestamp2sec(sub.stop) - timestamp2sec(sub.start)
        # For future use
        playtime = timestamp2sec(sub.start)
        message = sub.text
        if '\n' in message:
            for line in message.split('\n'):
                post_one(line, rnd, cid, cookie, fontsize, mode, color, playtime, pool)
        else:
            post_one(message, rnd, cid, cookie, fontsize, mode, color, playtime, pool)
        time_old.sleep(int(cool))
    print('INFO: DONE!')


#----------------------------------------------------------------------
def usage():
    """"""
    print('''
    srt2Bilibili
    
    https://github.com/cnbeining/srt2bilibili
    http://www.cnbeining.com/
    
    Beining@ACICFG
    
    WARNING: THIS PROGRAMME CAN BE DANGEROUS IF MISUSED,
    AND CAN LEAD TO UNWANTED CONSEQUNCES,
    INCLUDING (BUT NOT LIMITED TO) TEMPORARY OR PERMANENT BAN OF ACCOUNT AND/OR
    IP ADDRESS, DANMAKU POOL OVERSIZE, RUIN OF NORMAL DANMAKU.
    
    ONLY USE IF YOU KNOW WHAT YOU ARE DOING.
    
    This program is provided **as is**, with absolutely no warranty.
    
    
    Usage:
    
    python3 srt2bilibili.py (-h) (-a 12345678) [-p 1] [-c ./bilicookies] (-s 1.srt) [-f 25] [-m 0] [-o 16777215] [-w 2] [-l 0]
    
    -h: Default: None
        Print this usage file.
        
    -a: Default: None
        The av number.
        
    -p: Default: 1
        The part number.
        
    -c Default: ./bilicookies
        The path of cookies.
        Should looks like:
        
        DedeUserID=123456;DedeUserID__ckMd5=****************;SESSDATA=*******************
            
    -s Default: None
        The srt file you want to post.
        srt2bilibili will post multi danmakues for multi-line subtitle,
        since there's a ban on the use of \n.
        
    -f Default: 25
        The size of danmaku.
        
    -m Default: 4
        The mode of danmaku.
        1: Normal
        4: Lower Bound  *Suggested
        5: Upper Bound
        6: Reverse
        7: Special
        9: Advanced
        
    -o Default: 16777215
        The colour of danmaku, in integer.
        
    -w Default: 2
       The cool time (time to wait between posting danmakues)
       Do not set it too small, which would lead to ban or failure.
       
    -l Default: 0
        The Danmaku Pool to use.
        0: Normal
        1: Subtitle
        2: Special
        If you own the video, please set it to 1 to prevent potential lost of danmaku.
        
    More info avalable at http://docs.bilibili.cn/wiki/API.comment  .
    ''')

if __name__=='__main__':
    argv_list = []
    argv_list = sys.argv[1:]
    aid, part, cookiepath, srt, fontsize, mode, color, cooltime, playtime, pool = 0, 1, './bilicookies', '', 25, 4, 16777215, 2, 0, 0
    try:
        opts, args = getopt.getopt(argv_list, "ha:p:c:s:f:m:o:l:",
                                   ['help', "av", 'part', 'cookie', 'srt', 'fontsize', 'mode', 'color', 'cooltime', 'pool'])
    except getopt.GetoptError:
        usage()
        exit()
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            exit()
        if o in ('-a', '--av'):
            aid = a
            try:
                argv_list.remove('-a')
            except:
                break
        if o in ('-p', '--part'):
            part = a
            try:
                argv_list.remove('-p')
            except:
                part = 1
                break
        if o in ('-c', '--cookie'):
            cookiepath = a
            try:
                argv_list.remove('-c')
            except:
                print('INFO: No cookie path set, use default: ./bilicookies')
                cookiepath = './bilicookies'
                break
        if o in ('-s', '--srt'):
            srt = a
            try:
                argv_list.remove('-s')
            except:
                break
        if o in ('-f', '--fontsize'):
            fontsize = a
            try:
                argv_list.remove('-f')
            except:
                break
        if o in ('-m', '--mode'):
            mode = a
            try:
                argv_list.remove('-m')
            except:
                mode = 1
                break
        if o in ('-o', '--color'):
            color = a
            try:
                argv_list.remove('-o')
            except:
                color = 16777215
                break
        if o in ('-w', '--cooltime'):
            cooltime = a
            try:
                argv_list.remove('-w')
            except:
                cooltime = 2
                break
        if o in ('-l', '--pool'):
            pool = a
            try:
                argv_list.remove('-l')
            except:
                pool = 0
                break
    if aid == 0:
        logging.fatal('No aid!')
        exit()
    if srt == '':
        logging.fatal('No srt!')
        exit()
    if len(cookiepath) == 0:
        cookiepath = './bilicookies'
    cookies = read_cookie(cookiepath)
    logging.debug('Cookies: ' + cookiepath)
    BILIGRAB_UA = 'srt2Bilibili / ' + str(VER) + ' (cnbeining@gmail.com)'
    BILIGRAB_HEADER = {'User-Agent': BILIGRAB_UA, 'Cache-Control': 'no-cache', 'Pragma': 'no-cache', 'Cookie': cookies[0]}
    logging.debug(cookies[0])
    main(srt, fontsize, mode, color, cookies[0], aid, part, cooltime, pool)