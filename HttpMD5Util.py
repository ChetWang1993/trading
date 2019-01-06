# encoding: UTF-8
#用于进行http请求，以及MD5加密，生成签名的工具类
import json
import hashlib
import time
from constants import *
import base64
import requests
import hmac

def signature(secretKey, timestamp, method, request_path, body={}):
    if str(body) == '{}' or str(body) == 'None':
        body = ''
    message = str(timestamp) + str.upper(method) + request_path + str(body)
    if method == 'POST':
        print(message)
    mac = hmac.new(secretKey, message, digestmod=hashlib.sha256)
    d = mac.digest()
    return base64.b64encode(d)

def get_header(api_key, sign, timestamp, passphrase):
    header = dict()
    header[CONTENT_TYPE] = APPLICATION_JSON
    header[OK_ACCESS_KEY] = api_key
    header[OK_ACCESS_SIGN] = sign
    header[OK_ACCESS_TIMESTAMP] = str(timestamp)
    header[OK_ACCESS_PASSPHRASE] = passphrase
    return header
