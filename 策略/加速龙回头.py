# 克隆自聚宽文章：https://www.joinquant.com/post/27429
# 标题：2020年效果很好的策略-龙回头策略v3.0
# 作者：橘座量化

#2020年效果很好的策略-龙回头策略v3.0
# 连板-回调-冲高-阉割上传版本-Clone
# 克隆自聚宽文章：https://www.joinquant.com/post/27429
# 标题：2020年效果很好的策略-龙回头策略v3.0
# 作者：橘座量化

# 选股条件
# 近期有进入龙湖板的股票
# 连板次数大于等于2次
# 回调天数大于等于2天
# 回调过程中必须有大资金介入
# 回调有涨幅限制
# 等等细节条件

# 买入条件
# 早盘放量冲高买入

# 卖出条件
# 不涨停卖出

# 总结
# 2020年效果不错，资金偏好2+n模式
# 导入函数库
import jqdata
from jqlib.technical_analysis import *
import operator
import datetime
import talib
import numpy as np
import pandas as pd


#连板后回调，中间有一次冲高机会
def market_cap(): 
      wholeA= get_fundamentals(query(
            valuation.code
        ).filter(
            valuation.market_cap<500
            ))
      wholeAList=list(wholeA['code'])
      return wholeAList
      
# 这是过滤开盘价等于high_limit的
def filter_stock_limit(stock_list):
    curr_data = get_current_data()
    for stock in stock_list:
        price = curr_data[stock].day_open
        if (price >= curr_data[stock].high_limit):
            stock_list.remove(stock)
    return stock_list

def remove_new_stocks(security_list,context):
    for stock in security_list:
        days_public = (context.current_dt.date()-get_security_info(stock).start_date).days
        if days_public<100:
            security_list.remove(stock)
    return security_list

def filter_stock_ST(stock_list):
    curr_data = get_current_data()
    for stock in stock_list:
        if (curr_data[stock].is_st) or \
        ('ST' in curr_data[stock].name) or \
        ('*' in curr_data[stock].name) or \
        ('退' in curr_data[stock].name):
            stock_list.remove(stock)
    return stock_list
    

def check_stocks(context):
    # 返回市值小于500亿
    g.check_out_lists = market_cap()
    # g.check_out_lists = filter_stock_limit(g.check_out_lists)
    g.check_out_lists = remove_new_stocks(g.check_out_lists,context)
    g.check_out_lists = filter_stock_ST(g.check_out_lists)
    longhu = get_billboard_list(stock_list=g.check_out_lists, end_date = None, count =30)
    
    longhu_lst = list(longhu['code'])
    #t()
    #log.info('?',len(g.check_out_lists))
    #for stock in g.check_out_lists:
        #if len(longhu[longhu['code'] == stock]) > 0:
    #    if stock in longhu_lst:
    #        finallist.append(stock)
    g.check_out_lists = [stock for stock in g.check_out_lists if stock in longhu_lst]
    #g.check_out_lists = finallist
    #t('check_stocks 5',False)
    # print(str(len(g.check_out_lists)))
    # print(str(get_current_data()['603005.XSHG'].day_open))

# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    set_option("avoid_future_data", True)

    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    
    #run_daily(func, time='09:31')

import time
def t(info = '',start = True):
    if start:
        g.t = time.time()
    else:
        log.info("%s ===》 %.2f",info,time.time() - g.t)

#盘前
def before_trading_start(context):
    
    #t()
    #股票次
    # todo 过滤st，停牌
    check_stocks(context)
    #t('before_trading_start 1',False)
    #t()
    # 今天计划买入的股票
    g.preorderlist = []
    # print(len(g.check_out_lists))
    #今天计划卖出的票
    g.selllist = {}
    for sec in context.portfolio.positions:
        historys = attribute_history(sec,fields=['close', 'pre_close'],count=1)
        sellitem = {}
        sellitem['pre_close'] = historys['pre_close'][-1]
        sellitem['sec'] = sec
        g.selllist[sec] = sellitem
    #t('before_trading_start 2',False)
    #t()
    #今天计划跟钟的票
    g.tracklist = zhangting(context, 2, 12)
    
    #t('before_trading_start 3',False)



# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    if g.tracklist:
        # print("跟钟数量" + str(len(g.tracklist)))
        cash = context.portfolio.available_cash
        # 10000 就不买了
        if cash > 1000:
            #t()
            count = decisionOrder(context, g.tracklist,data)
            #t('decisionOrder',False)
            if count > 0:
                print("可以买的数量" + str(count))

    selllogic(context,data)
    buying(context,data)
    

# ===============================================
#决定是否卖出股票

def selllogic(context,data):
    hour = context.current_dt.hour
    minute = context.current_dt.minute
    # 13:42开始操作?
    if hour == 13 and minute == 42:
        #t()
        for sec in g.selllist.copy():
            print(sec)
            lastprice = get_bars(sec, count=1, include_now = False,fields=['low','close','date'])
            secprice = get_bars(sec, end_dt=context.current_dt, count=1, fields=['date','low','close','high','open'],include_now=True)
           
            openprice = secprice['open'][0]
            lowprice = secprice['low'][0]
            closeprice = secprice['close'][0]
            precloseprice = lastprice['close'][0]
            if (closeprice - precloseprice) / precloseprice >= 0.096:
                # print("涨幅超过9% 今天不卖了 " + sec)
                continue
            print("will sell" + sec)
            order_target(sec, 0)
            del(g.selllist[sec])  
        #t('selllogic',False)
            
    
# ===============================================
#决定是否购买和评分排行
def decisionOrder(context, tracklistbottom, data):
    if not tracklistbottom:
        return 0
    hour = context.current_dt.hour
    minu = context.current_dt.minute
    # 10点不交易?
    if hour > 10:
        return 0
    mincount = 20
    # mincount为9:30后过了多少分,9:50后返回20
    if hour == 9:
        # 取9
        mincount = min(max(minu - 30,1), mincount)
    else:
        mincount = mincount
    count = 0
    for bottom in tracklistbottom.copy():
        # print context.current_price(bottom.stock)
        # todo nick 的价格在确定一下
        currentprice = get_current_data()[bottom.stock].last_price
        if currentprice == data[bottom.stock].high_limit:
            print("涨停不与买入" + bottom.stock)
            # tracklistbottom.remove(bottom)
            continue
        # 下跌不与买入
        open_price = get_current_data()[bottom.stock].day_open
        if open_price > currentprice:
            continue
        # 获取今天的涨幅
        open_price = get_current_data()[bottom.stock].day_open
        rate = (currentprice - bottom.last_close_price) / bottom.last_close_price
        # 涨幅小于0.05不与买入
        if (rate < 0.05):
            continue
        # 将通过评测的股票加入购买清单
        g.preorderlist.append(bottom)
        tracklistbottom.remove(bottom)
        count = count + 1
    # 购买股票数量
    return count
    
#====================================================
# 决定是否购买
def buying(context,data):
    if context.current_dt.hour > 13 and context.current_dt.minute > 45:
        return
    
    #t()
    #先遍历1.2倍动能的票
    for item in g.preorderlist.copy():
        currentprice = data[item.stock].close
        if currentprice < data[item.stock].high_limit:
            print("直接买它!!!!!!!!!!!!!buy "+item.stock + "买它!!!!!!!!!!==================================" + str(context.current_dt) + " " + str(currentprice))
            buy(context, item.stock)
            g.preorderlist.remove(item)
            break
    #t('buying',False)
            

def buy(context, stock):
    count = 2
    if stock in context.portfolio.positions:
        print("已经有这个票了" + stock)
        return
    if len(context.portfolio.positions) >= count:
        print("仓位满了" + stock)
        return
    buy_cash = context.portfolio.total_value /count
    order_target_value(stock, buy_cash)

    
# =========================================================================
#m天涨停次数大于等n
def zhangting(context, n, m):
    print("================="+ str(context.current_dt) + "=================")
    
    ztlist = [] #满足条件的涨停列表
    g.tracklist = []
    finalbuylist = []
    finalbuylistobject = {}
    for sec in g.check_out_lists:
        count = 0
        historys = attribute_history(sec,fields=['close', 'pre_close', 'high','low','open','high_limit'],count=m,df=False)

        close = historys['close'][-1]
        last_data_close =  historys['pre_close'][-1]

        # 剔除昨天和前天闭市价格差距大于前天的0.03的股票
        if  (close - last_data_close) / last_data_close > 0.03:
            continue
        # 是否有连续涨停
        haslianxu = False
        islastzt = False
        lianxuid = 0
        isok = False
        alllen = m
        for i in range(m-1, 0,-1):
            # todo 检查数据是否有效，isnan
            limit = historys['high_limit'][i]
            close =  historys['close'][i]
            limit1 = historys['high_limit'][i-1]
            close1 =  historys['close'][i-1]
            # 连续12天中有两天连续涨停
            if limit == close and limit1 == close1:
                isok = True
                # 获取连续涨停结束日 
                lianxuid = i
        # 剔除没有连续涨停的股票
        if not isok:
            continue
        # 获取连续涨停后,最高和最低价以及日期
        max_id, max_price = max(enumerate(historys['high'][lianxuid:]), key=operator.itemgetter(1))
        min_id, min_price = min(enumerate(historys['low'][lianxuid:]), key=operator.itemgetter(1))
        max_id = max_id + lianxuid
        min_id = min_id + lianxuid
        # 剔除连续涨停后的最低价离今天大于2天的股票
        if alllen - min_id > 2:
            print(sec + "最后最小离今天太远 " + str(min_id))
            continue
        # 剔除回调小于最低价0.2(连涨后最高价与最低价回调不到0.2)
        if (max_price - min_price) / min_price < 0.2:
            print(sec + "回调不够" + str(max_price) + " " + str(min_price))
            continue
        # 剔除连涨后的最高价日离今天不到3天的股票
        if alllen - max_id < 3:
            print(sec + "回调时间不够")
            continue
        
        # 连涨后的某天最高价与前一天收盘之差比前一天收盘价大0.045的股票
        haschonggao = False
        for i in range(max_id+1, alllen):
            last_data_close = historys['pre_close'][i]
            limit = historys['high_limit'][i]
            close =  historys['close'][i]
            high = historys['high'][i]
            if (high - last_data_close) / last_data_close  > 0.045:
                haschonggao = True
        # 剔除没有冲高 既连涨后最高价与收盘价的差没有大于前一天收盘价的0.045
        if not haschonggao:
            print(sec + " 没有冲高")
            continue
        
        yanxiancount = 0
        for ix in range(max_id+1, alllen):
            last_data_close = historys['pre_close'][i]
            close_today =  historys['close'][i]
            open_today = historys['open'][i]
            # 剔除连涨后某天收盘价小于开盘价 或 收盘价小于前一天收盘价的股票
            if close_today < open_today or close_today < last_data_close:
                continue
            # 获取日内涨幅
            day_gain = (close_today - last_data_close) / last_data_close
            # 如果日内涨幅大于0.052为阳线并加入计数
            if day_gain >= 0.052:
                hasyanxian = True
                yanxiancount = yanxiancount + 1
                xianyanid = i
        # 剔除阳线大于1的股票
        if yanxiancount > 1:
            print(sec + " 阳线过多")
            continue       
        isok = False
        # 获取前两天数据
        for i in range(-1,-3,-1):
            lastopenprice = historys['close'][i]
            lastopenprice = historys['open'][i]
            lasthighprice = historys['high'][i]
            lastlowprice = historys['low'][i]
            lastcloseprice = historys['close'][i]
            lastpreclose = historys['pre_close'][i]
            # 是否是实体大阴线（跌幅大于4%）,实体大于3%
            isyingxian = yingxian(lastopenprice, lastcloseprice,lasthighprice,lastlowprice,lastpreclose)
        
            if  isyingxian:
                isok = True
                break
        if isok:
            bottom = CWBotton()
            bottom.inix(historys['close'][-1],sec)
            finalbuylist.append(sec)
            g.tracklist.append(bottom)
        else:
            print(sec + " 最后几天不符合要求")
        
    
    print("符合要求的数量" + str(len(g.tracklist)))
    print(finalbuylist)
    return g.tracklist
    
#====================================================
class CWBotton:
    
    def inix(self,last_close_price,stock):
        self.last_close_price = last_close_price
        self.stock = stock

# 是否是实体大阴线（跌幅大于4%）,实体大于3%
def yingxian(open, close, high, low, preclose):
    if close > open or close > preclose:
        return False
    # 跌幅小于4%
    if (preclose - close) / preclose < 0.03:
        return False
    
    return True
    
# 上影线大于2%
def shangyingxian(open, close, high, low):
    if (high - max(open, close)) / max(open, close) > 0.02:
        return True
    return False

#判断是否是T线
#下影线大于实体1.2倍，上影线小于等于实体
def Txian(open, close, high, low):
    # 0.001是异常处理0的情况
    shiti = round( max(abs(open - close),0.001),3)
    shangyin = round(max(abs(high - max(close,open)),0.001),3)
    xiaying = round(max(abs(min(open,close) - low),0.001),3)
    # 下影线不能太长参考600800,震幅过大
    if ((high - low) / open) > 0.9:
        print("震幅过大")
        return False
    if xiaying / shiti >=  1.9 and xiaying / shangyin >= 2:
        return True
    return False
        
    
def bdebugprint(str):
    if 1:
        print(str)
        
def buyprint(str):
    if 1:
        print(str)
    
