# encoding: UTF-8
import sys
sys.path.append('./strat')
from dtStrat import *
from func import *
import json
from datetime import datetime

settingFileName = sys.argv[1]
setting = json.load(open('conf/' + settingFileName))
strat = testStrategy(setting)

def tickCB(tick):
    if tick == {}:
        return
    t = VtTickData()   
    # 成交数据
    t.lastPrice = tick['last']           # 最新成交价
    t.volume = 0                 # 今天总成交量
    t.openInterest = 0           # 持仓量
    if not '.' in tick['timestamp']:
        t.datetime = datetime.strptime(tick['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
    else:
        t.datetime = datetime.strptime(tick['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
    strat.onTick(t)

okApi = okApi(setting['apiKey'], setting['secretKey'], '')
while(True):
    try:
    	tickCB(okApi.get_okex("/api/futures/v3/instruments/" + setting['okSymbol'] + "/ticker"))
    except Exception as e:
        print('[ERROR]: get tick {}'.format(e))
        time.sleep(1)
        continue
    time.sleep(1)
