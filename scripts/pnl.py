import sys
import os
pwd = os.path.dirname(os.path.realpath(__file__))
sys.path.append(pwd + '/../')
from func import *
import json
pwd = os.path.dirname(os.path.realpath(__file__))
settingFileName = sys.argv[1]
logName = sys.argv[2]
log = open(pwd + '/../log/' + logName, 'a')
setting = json.load(open(pwd + '/../conf/' + settingFileName))
okApi = okApi(setting['apiKey'], setting['secretKey'], setting['logFile'])
try:
	res1 = okApi.get_okex("/api/futures/v3/accounts/" + setting['currency'])
	res2 = okApi.get_okex("/api/futures/v3/instruments/" + setting['okSymbol'] + "/ticker")
	log.write("%s\t%s\t%s\t%s\n"%(res2['timestamp'], res1['equity'], res1['total_avail_balance'], float(res1['equity']) * float(res2['last'])))
except Exception as e:
	print(e)
