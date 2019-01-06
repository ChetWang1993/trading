# encoding: UTF-8
from datetime import datetime, date, time, timedelta
import time
from pytz import timezone
from func import *
from vnpy.trader.app.ctaStrategy.ctaTemplate import BarGenerator
from vnpy.trader.vtObject import VtBarData, VtTickData
########################################################################
class testStrategy():
    # 策略参数
    fixedSize = 0
    k1 = 0.6
    k2 = 0.4
    order_log_dir = ''
    order_log_name = ''

    initDays = 0
    longPos = 0.0
    shortPos = 0.0
    matchPrice = True
    # 策略变量
    barList = []                # K线对象的列表
    dayOpen = 0.0
    dayHigh = 0.0
    dayLow = 0.0

    range = 0.0
    longEntry = 0.0
    shortEntry = 0.0
    cut_loss = 1
    trade_price = 0.0

    apiKey = ""
    secretKey = ""

    # 参数列表，保存了参数的名称
    paramList = ['apiKey',
                 'secretKey',
                 'order_log_dir',
                 'order_log_name',
                 'symbol',
                 'okSymbol',
                 'k1',
                 'k2',
                 'fixedSize',
                 'cut_loss']

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'range',
               'longEntry',
               'shortEntry']
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']    

    #----------------------------------------------------------------------
    def __init__(self, setting):
        """Constructor"""
        self.bg = BarGenerator(self.onBar)
        self.barList = []
        if setting:
            d = self.__dict__
            for key in self.paramList:
                if key in setting:
                    d[key] = setting[key]
        print('[INFO]: strat init')
        if not os.path.exists(self.order_log_dir):
            os.makedirs(self.order_log_dir)
        self.okApi = okApi(self.apiKey, self.secretKey,
            self.order_log_dir.format(self.symbol) + self.order_log_name.format(datetime.now()))
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        self.initPrice()
        #self.putEvent()
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        #self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)

    def initPrice(self):
        self.updatePos()
        try:
            yyd = (datetime.now() - timedelta(2)).replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
            yd = (datetime.now() - timedelta(1)).replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
            td = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
            klinesY = self.okApi.get_okex("/api/futures/v3/instruments/" + self.okSymbol + "/candles", {'start': yyd, 'end': yd, 'granularity': '86400'})[0]
            klinesT = self.okApi.get_okex("/api/futures/v3/instruments/" + self.okSymbol + "/candles", {'start': yd, 'end': td, 'granularity': '86400'})[0]
            print("[INFO]: %s yesterday kline"%(self.__dict__['okSymbol']))
            print('[INFO]: open: {}\thigh: {}\tlow: {}\tclose: {}'.format(klinesY[1],
                klinesY[2], klinesY[3], klinesY[4]))
            print("[INFO]: %s today kline"%(self.__dict__['okSymbol']))
            print('[INFO]: open: {}\thigh: {}\tlow: {}\tclose: {}'.format(klinesT[1],
                klinesT[2], klinesT[3], klinesT[4]))

            self.dayOpen = float(klinesT[1])
            self.dayHigh = float(klinesT[2])
            self.dayLow = float(klinesT[3])
            self.dayClose = float(klinesT[4])
            self.range = float(klinesY[2]) - float(klinesY[3])
            self.longEntry = float(klinesT[1]) + self.k1 * self.range
            self.shortEntry = float(klinesT[1]) - self.k2 * self.range
        except KeyError:
            print("[ERROR]: %s get kline error"%(self.__dict__['okSymbol']))
            return 0.0 
        return 0.0        

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单
        bar.open = float(bar.open); bar.close = float(bar.close); bar.high = float(bar.high); bar.low = float(bar.low)
        ts = bar.datetime.replace(tzinfo=timezone('GMT')).astimezone(timezone('Asia/Singapore'))

        print("------------------------------------------------------------------")
        print("[INFO]: {}\t{}\tbar close: {}\tlong entry: {}\tshort entry: {}\trange: {}\ttrade price: {}".format(str(ts),
            self.__dict__['okSymbol'], bar.close, self.longEntry, self.shortEntry, self.range, self.trade_price))

        self.cancelAll()
        self.updatePos()
        self.barList.append(bar)
        if len(self.barList) < 2:
            return
        lastBar = self.barList[-2]
        self.barList.pop(0)

        last_bar_date = lastBar.datetime.replace(tzinfo=timezone('GMT')).astimezone(timezone('Asia/Singapore')).date()
        current_bar_date = bar.datetime.replace(tzinfo=timezone('GMT')).astimezone(timezone('Asia/Singapore')).date()
        if last_bar_date != current_bar_date:
            # 如果已经初始化
            if self.dayHigh:
                self.range = self.dayHigh - self.dayLow
                print("[INFO]: bar open: {}\tk1: {}\tk2: {}\trange: {}".format(bar.open, self.k1, self.k2, self.range))
                self.longEntry = bar.open + self.k1 * self.range
                self.shortEntry = bar.open - self.k2 * self.range
            self.dayOpen = bar.open
            self.dayHigh = bar.high
            self.dayLow = bar.low
        else:
            self.dayHigh = max(self.dayHigh, bar.high)
            self.dayLow = min(self.dayLow, bar.low)

        if self.longPos == 0.0 and self.shortPos == 0.0:
            if bar.close > self.dayOpen and bar.close >= self.longEntry:
                self.order(self.longEntry, self.fixedSize, BUY)
            elif bar.close <= self.shortEntry:
                self.order(self.shortEntry, self.fixedSize, SHORT)

        # 持有多头仓位
        elif self.longPos > 0.0:
            # 多头止损单
            is_reverse = bar.close <= self.shortEntry
            is_cut_loss = self.trade_price != 0 and BUY_SIDE * (bar.close - self.trade_price) / bar.close >= self.cut_loss
            if is_reverse or is_cut_loss:
                px = self.shortEntry if is_reverse else bar.close
                self.order(self.longEntry, int(self.longPos), SELL)
            if is_reverse:
                self.order(self.shortEntry, self.fixedSize, SHORT)
        # 持有空头仓位
        elif self.shortPos > 0.0:
            # 空头止损单
            is_reverse = bar.close >= self.longEntry
            is_cut_loss = self.trade_price != 0 and SELL_SIDE * (bar.close - self.trade_price) / bar.close >= self.cut_loss
            if is_reverse or is_cut_loss:
                px = self.longEntry if is_reverse else bar.close
                self.order(self.longEntry, int(self.shortPos), COVER)
            if is_reverse:
                self.order(self.shortEntry, self.fixedSize, BUY)
      # 发出状态更新事件
        #self.putEvent()

    def updatePos(self):
        try:
            balance = self.okApi.get_okex("/api/futures/v3/" + self.okSymbol + "/position");
            self.longPos =  float(balance['holding'][0]['long_avail_qty'])
            self.shortPos = float(balance['holding'][0]['short_avail_qty'])
            if self.longPos != 0:
                self.trade_price = float(balance['holding'][0]['long_avg_cost'])
            elif self.shortPos != 0:
                self.trade_price = float(balance['holding'][0]['short_avg_cost'])
            else:
                self.trade_price = 0
        except IndexError:
            print("[ERROR]: %s get pos error"%(self.__dict__['okSymbol']))
            self.longPos = 0.0
            self.shortPos = 0.0
            self.trade_price = 0
        print("[INFO]: %s long pos: %f short pos %f"%(self.okSymbol, self.longPos, self.shortPos))

    def cancelAll(self):
        res = self.okApi.get_okex("/api/futures/v3/orders/" + self.okSymbol)['order_info']
        orderIds = [x['order_id'] for x in res]
        self.okApi.post_okex("/api/futures/v3/cancel_batch_orders/" + self.okSymbol, {"order_ids": orderIds})

    def order(self, price, size, orderType, matchPrice='1'):
        self.okApi.post_okex("/api/futures/v3/order", {"instrument_id": self.okSymbol, "type": orderType, "price": str(price),"size": str(size),"match_price": matchPrice,"leverage":"10"})
