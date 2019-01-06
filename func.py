# encoding: UTF-8
from HttpMD5Util import signature, get_header
import time
import json
from pytz import timezone
from constants import *
import math
import requests
from datetime import datetime, timedelta
import os
pwd = os.path.dirname(os.path.realpath(__file__))
class okApi():
    def __init__(self, apiKey, secretKey, logFile):
        self.apiKey = str(apiKey)
        self.secretKey = str(secretKey)
        self.logFile = pwd + '/log/' + logFile

    def get_okex(self, requestPath, params = {}):
        paramStr = ''
        if params != {}:
            paramStr += '?'
            for key in params:
                paramStr += (key + '=' + params[key] + '&')
            paramStr = paramStr[:-1]
        print(requestPath)
        timestamp = requests.get(base_url + '/api/general/v3/time').json()['iso']
        print(timestamp)
        #max_times = 10
        # for i in range(max_times):
        #     try:
                 # timestamp = datetime.now().replace(tzinfo = timezone('Asia/Singapore')).astimezone(timezone('GMT')).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            # except:
            #     continue
            # finally:
            #     break
        header = get_header(self.apiKey, signature(self.secretKey, timestamp, 'GET', requestPath), timestamp, passphrase)

        res = requests.get(base_url + requestPath + paramStr, headers=header).json()
        return res

    def post_okex(self, requestPath, params = {}):
        log = open(self.logFile, "a")
        timestamp = requests.get(base_url + '/api/general/v3/time').json()['iso']
        body = json.dumps(params)
        header = get_header(self.apiKey, signature(self.secretKey, timestamp, 'POST', requestPath, body), timestamp, passphrase)
        res = requests.post(base_url + requestPath, headers=header, data=body).json()
        ts = datetime.strptime(timestamp.split('.')[0],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone('GMT')).astimezone(timezone('Asia/Singapore'))
        if order_str in requestPath:
            log.write(str(ts) + '\tPOST' + requestPath + str(body) + '\n' + str(res) + '\n')
        log.close()
        return res

#startTime = (datetime.now() - timedelta(1)).replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
#endTime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
#params = {'start': startTime, 'end': endTime, 'granularity': '86400'}
#okApi = okApi('f4437433-0378-4535-8ba6-1fdffce6cea5', '589CCC3715DE217F935343DD2F4EE06E')
#print(okApi.get_okex("/api/futures/v3/instruments/" + 'EOS-USD-181116' + "/candles", params))
#okApi.get_okex("/api/futures/v3/" + 'BTC-USD-181116' + "/position")
#post_okex("/api/futures/v3/order", {"instrument_id":"EOS-USD-181116", "type":"1","price":"432.11","size":"10","match_price":"1","leverage":"10"})
#get_okex("/api/futures/v3/orders/BTC-USD-181116")

