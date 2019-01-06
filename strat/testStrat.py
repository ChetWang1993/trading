# encoding: UTF-8
from func import *
from vnpy.trader.app.ctaStrategy.ctaTemplate import BarGenerator
from vnpy.trader.vtObject import VtBarData, VtTickData
########################################################################
class testStrategy():
    # 策略参数
    fixedSize = 100
    k1 = 0.6
    k2 = 0.4

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

    apiKey = ""
    secretKey = ""
    logFile = ""
    # 参数列表，保存了参数的名称
    paramList = ['apiKey',
                 'secretKey',
                 'logFile',
                 'author',
                 'vtSymbol',
                 'okSymbol',
                 'k1',
                 'k2',
                 'initDays',
                 'fixedSize']

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

        print(u'策略初始化')
        self.okApi = okApi(self.apiKey, self.secretKey, self.logFile)
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        self.initPrice()
        #self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' %self.name)
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
        return 0.0        

    #----------------------------------------------------------------------
    def onBarInit(self, bar):
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单
        print("--------------")
        self.cancelAll()
        self.updatePos()
        print("%s h: %s, l: %s, o: %s, c: %s" % (self.__dict__['okSymbol'], bar.high, bar.low, bar.open, bar.close))
        #print("%s long entry: %f, short entry: %f" % (self.__dict__['okSymbol'], self.longEntry, self.shortEntry))

        if self.longPos == 0 and self.shortPos == 0:
            self.order(self.longEntry, self.fixedSize, BUY)
        elif self.longPos > 0:
            self.order(self.longEntry, int(self.longPos), SELL)
            self.order(self.shortEntry, self.fixedSize, SHORT)
        elif self.shortPos > 0:
            self.order(self.longEntry, int(self.shortPos), COVER)
            self.order(self.shortEntry, self.fixedSize, BUY)          
      # 发出状态更新事件
        #self.putEvent()

    def updatePos(self):
        try:
            balance = self.okApi.get_okex("/api/futures/v3/" + self.okSymbol + "/position")
            self.longPos =  float(balance['holding'][0]['long_avail_qty'])
            self.shortPos = float(balance['holding'][0]['short_avail_qty'])
        except IndexError:
            print("%s get pos error"%(self.__dict__['okSymbol']))
            self.longPos = 0.0
            self.shortPos = 0.0
        print("%s long pos: %f short pos %f"%(self.okSymbol, self.longPos, self.shortPos))

    def cancelAll(self):
        res = self.okApi.get_okex("/api/futures/v3/orders/" + self.okSymbol)['order_info']
        orderIds = [x['order_id'] for x in res]
        print('order ids: %s' % str(orderIds))
        self.okApi.post_okex("/api/futures/v3/cancel_batch_orders/" + self.okSymbol, {"order_ids": orderIds})

    def order(self, price, size, orderType, matchPrice='1'):
        self.okApi.post_okex("/api/futures/v3/order", {"instrument_id": self.okSymbol, "type": orderType, "price": str(price),"size": str(size),"match_price": matchPrice,"leverage":"10"})