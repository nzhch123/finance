import random
import pandas as pd
import numpy as np
import talib
import re
def initialize(context):
    # 设置参数
    set_info(context)
    # 不设定基准，在多品种的回测当中基准没有参考意义
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
    ### 期货相关设定 ###
    # 设定账户为金融账户
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.starting_cash, type='futures')])
    # 期货类每笔交易时的手续费是：买入时万分之2.5,卖出时万分之2.5,平今仓为万分之2.5
    set_order_cost(OrderCost(open_commission=0.00025, close_commission=0.00025,close_today_commission=0.00025), type='index_futures')
    # 设定保证金比例15%
    set_option('futures_margin_rate', 0.15)
    # 开盘前运行
    run_daily( before_market_open, time='open', reference_security=get_future_code('RB'))
    # 开盘时运行
    run_daily( market_open, time='open', reference_security=get_future_code('RB'))
    # 收盘后运行
    
    # 设置滑点（单边万5，双边千1）
    set_slippage(PriceRelatedSlippage(0.001),type='future')
def set_info(context):
    
    #######变量设置########
    g.future_list = []  # 设置期货品种列表
    g.TradeLots = {}  # 各品种的交易手数信息
    g.MappingReal = {} # 真实合约映射（key为symbol，value为主力合约）
    g.MappingIndex = {} # 指数合约映射 （key为 symbol，value为指数合约
    #######参数设置########
    g.margin_rate = 0.15 # 定义保证金率
    # 交易的期货品种信息
    g.instruments = ['AG','PB','AU','RB','AL','RU','BU','SN',
    'CU','WR','FU','ZN','HC','NI','CY','RM','CF','FG','SF',
    'SM','MA','SR','TA','J','I','JM','L','PP','V']
    g.trade_date={}
    # 价格列表初始化
    set_future_list(context)
def set_future_list(context):
    for ins in g.instruments:
        idx = get_future_code(ins)
        dom = get_dominant_future(ins)
        # 填充映射字典
        g.MappingIndex[ins] = idx
        g.MappingReal[ins] = dom
      

## 开盘前运行函数
def before_market_open(context):
    # 输出运行时间
    
    # 过滤无主力合约的品种，传入并修改期货字典信息
    for ins in g.instruments:
        dom = get_dominant_future(ins)
        if dom == '':
            pass
        else:
            # 判断是否执行replace_old_futures
            if dom == g.MappingReal[ins]:
                pass
            else:
                replace_old_futures(context,ins,dom)
              
        
            
## 开盘时运行函数
def market_open(context):
    # 输出函数运行时间
    #log.info('函数运行时间(market_open):'+str(context.current_dt.time()))
    # 以下是主循环
    hold_long=list(context.portfolio.long_positions.keys())
    hold_short=list(context.portfolio.short_positions.keys())
    for i in hold_long:
        content= re.match ('^[a-zA-Z]+', i).group()
        start_d=g.trade_date[content]
        hold_max=get_price(i,start_date=start_d,end_date=context.previous_date)['high'].max()
        now_price=get_new_price(i,context)
        atr=get_ATR(i,context,days=50) 
        if atr:
            if now_price<=hold_max-3*atr:
                order_target(i, 0)
    # for i in hold_short:
        # content=re.match ('^[a-zA-Z]+', i).group()
        # start_d=g.trade_date[content]
        # hold_min=get_price(i,start_date=start_d,end_date=context.previous_date)['high'].min()
        # now_price=get_new_price(i,context)
        # atr=get_ATR(i,context,days=50)        
        # if atr:
            # if now_price>=hold_min+3*atr:
                # order_target(i, 0)    
    
    
    
    
    random.shuffle(g.instruments)
    for ins in g.instruments:
        # 过滤空主力合约品种
        if g.MappingReal[ins] != '':
            IndexFuture = g.MappingIndex[ins]
            RealFuture = g.MappingReal[ins]
            # 获取当月合约交割日期
            end_date = get_CCFX_end_date(RealFuture)
            # 当月合约交割日当天不开仓
            if (context.current_dt.date() == end_date):
                return
            else:
                # 如果没有数据，返回
                holds=list(context.portfolio.long_positions.keys())+list(context.portfolio.short_positions.keys())
                ma_50=get_ma(IndexFuture,context=context,days=50)
                ma_100=get_ma(IndexFuture,context=context,days=100)
                atr_100=get_ATR(IndexFuture,context=context,days=100)
                if atr_100:
                    now_price=get_new_price(IndexFuture,context=context)
                    price_max=get_price_max(IndexFuture,context=context,days=20)
                    price_min=get_price_min(IndexFuture,context=context)
                    if RealFuture not in holds and ma_50>=ma_100 and now_price>=price_max:
                        position=get_position(atr_100,total=context.portfolio.total_value)
                        order_value(RealFuture,position)
                        g.trade_date[ins]=context.current_dt.date()
                    # if RealFuture not in holds and ma_50<=ma_100 and now_price<=price_min:  
                        # position=get_position(atr_100,total=context.portfolio.total_value)
                        # order_value(RealFuture,position,side='short')
                        # g.trade_date[ins]=context.current_dt.date()
                else :
                    return
                
                
                
                
                
                
                
                       
    
def replace_old_futures(context,ins,dom):
    
    LastFuture = g.MappingReal[ins]
    
    if LastFuture in list(context.portfolio.long_positions.keys()):
        lots_long = context.portfolio.long_positions[LastFuture].total_amount
        order_target(LastFuture,0,side='long')
        order_target(dom,lots_long,side='long')
        print('主力合约更换，平多仓换新仓')
    
    if LastFuture in list(context.portfolio.short_positions.keys()):
        lots_short = context.portfolio.short_positions[LastFuture].total_amount
        order_target(LastFuture,0,side='short')
        order_target(dom,lots_short,side='short')
        print('主力合约更换，平空仓换新仓')

    g.MappingReal[ins] = dom     
            
        
        
# 获取当天时间正在交易的期货主力合约函数
def get_future_code(symbol):
    future_code_list = {'IC':'IC9999.CCFX','SC':'SC9999.XINE','AG':'AG9999.XSGE','PB':'PB9999.XSGE',
                        'AU':'AU9999.XSGE','RB':'RB9999.XSGE',
                        'AL':'AL9999.XSGE','RU':'RU9999.XSGE','BU':'BU9999.XSGE','SN':'SN9999.XSGE',
                        'CU':'CU9999.XSGE','WR':'WR9999.XSGE','FU':'FU9999.XSGE','ZN':'ZN9999.XSGE',
                        'HC':'HC9999.XSGE','NI':'NI9999.XSGE','CY':'CY9999.XZCE','RM':'RM9999.XZCE','CF':'CF9999.XZCE',
                        'FG':'FG9999.XZCE','SF':'SF9999.XZCE','SM':'SM9999.XZCE',
                        'MA':'MA9999.XZCE','SR':'SR9999.XZCE','TA':'TA9999.XZCE','J':'J9999.XDCE',
                        'I':'I9999.XDCE','JM':'JM9999.XDCE','L':'L9999.XDCE','PP':'PP9999.XDCE','V':'V9999.XDCE'}
    try:
        return future_code_list[symbol]
    except:
        return 'WARNING: 无此合约'




# 获取金融期货合约到期日
def get_CCFX_end_date(fature_code):
    # 获取金融期货合约到期日
    return get_security_info(fature_code).end_date
    
def get_ATR(stock,context,days=20):
    data = get_price(stock, end_date=context.previous_date,count=days*2+2,skip_paused=True)
    data=data.dropna()
    try:    
        if len(data)==(days*2+2):
            close_ATR = data['close']
            high_ATR = data['high']
            low_ATR = data['low']
            atr_l= talib.ATR(high_ATR, low_ATR, close_ATR, days)
            atr = atr_l[-1]
            return atr
        else:
            return
    except Exception as e:
        return
def get_ma(stock,days,context):
    # days=number,data=pandas
    data=get_price(stock, end_date=context.previous_date,count=days*2+2,skip_paused=True)
    data['ave'] = data['close'].rolling(days).mean()
    return data['ave'].iloc[-1]
    
    
    
def get_position(atr, total, rate=2):
    pos = total*rate/ atr
    return pos
    
    
def get_new_price(stock,context):
        price=get_price(stock, end_date=context.previous_date,count=1,skip_paused=True)['close'].iloc[-1]
        return price
        
def get_price_max(stock,context,days=20):
    price=get_price(stock, end_date=context.previous_date,count=days,skip_paused=True)['close'][:-1].max()
    return price
    
    
def get_price_min(stock,context,days=20):
    price=get_price(stock, end_date=context.previous_date,count=days,skip_paused=True)['close'][:-1].min()
    return price