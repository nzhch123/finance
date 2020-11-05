

# 导入函数库
from jqdata import *
import warnings
## 初始化函数，设定基准等等
import pandas as pd
import math
import numpy as np
import talib
from sklearn import linear_model
from sklearn.metrics import r2_score, mean_squared_error

warnings.filterwarnings("ignore")

def initialize(context):
    set_params()  # 1设置策参数
    #set_variables()  # 2设置中间变量
    set_backtest()  # 3设置回测条件
    run_weekly(handle, -1, '9:30')
    g.count=0


def set_params():
    g.security = '000300.XSHG'  # 沪深三百
    g.day = 250


def set_backtest():
    # 作为判断策略好坏和一系列风险值计算的基准
    set_benchmark(g.security)
    set_option('use_real_price', True)  # 用真实价格交易
    log.set_level('order', 'error')  # 设置报错等级


def before_trading_start(context):
    set_slip_fee(context)


# 4 根据不同的时间段设置滑点与手续费
def set_slip_fee(context):
    # 将滑点设置为0
    set_slippage(FixedSlippage(0))
    # 根据不同的时间段设置手续费
    dt = context.current_dt

    if dt > datetime.datetime(2013, 1, 1):
        set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5))

    elif dt > datetime.datetime(2011, 1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))

    elif dt > datetime.datetime(2009, 1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))

    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))


def after_trading_end(context):
    return


def handle(context):
    # 获取所有沪深300的股票
    g.count = g.count + 1
    holds = list(context.portfolio.long_positions.keys())
    hs_300=get_price(g.security,end_date=context.previous_date,count=400,skip_paused=True)
    if hs_300['close'].iloc[-1]<get_ma(200,hs_300):
        sell_all(holds)
    else:
        data = renew_rank(context)
    
        sell_list = check_sell(data, holds,context)
        sell_l(sell_list)
        buy_top(data)
    
        if g.count % 2 == 0:
            renew_risk(holds,context)

def sell_all(holds):
    for i in holds:
        order_target(i, 0)






def buy_top(data):
    stocks = data['沪深三百所有'].values
    for i in stocks:
        row = data[data['沪深三百所有'].isin([i])]
        number = row.iloc[0].loc['头寸规模']
        #number=int(round(number/100,0))*100   
        if number:
            order(i, int(number))


def check_sell(data, object,context):
    data = data[:60]
    stocks = data['沪深三百所有'].values
    l = []
    for i in object:
        if_gap = gap(i,context)
        price=get_price(g.security,end_date=context.previous_date,count=200,skip_paused=True)
        mv_100=get_ma(100,price)
        price_today=price['close'].iloc[-1]
        if i not in stocks or if_gap or price_today<mv_100:
            l.append(i)
    return l


def sell_l(l):
    for i in l:
        order_target_value(i, 0)


def renew_risk(holds,context):
    l = {'持仓股票': holds}
    data = pd.DataFrame(l)
    data['atr20'] = data['持仓股票'].apply(get_ATR, args=(context,))
    data['1/atr20'] = data['atr20'].apply(lambda x: 1 / x)

    # data=data.drop('为排名的数据',axis=1)
    data['持仓价值'] = data['持仓股票'].apply(holds_value, args=(context,))
    total_v = data['持仓价值'].sum()
    data['持仓比例'] = data['持仓价值'].apply(holds_pro, args=(total_v,))
    total_r_atr = data['1/atr20'].sum()
    data['合适比例'] = data['1/atr20'].apply(holds_pro, args=(total_r_atr,))
    #print(data)
    if len(data):
        data ['比例差值']= data.apply(lambda x:x.loc['持仓比例']-x.loc['合适比例'],axis=1)
        data['为排名的数据'] = data['比例差值'].apply(change_for_rank)
        data = data.sort_values('为排名的数据', ascending=False)
        for index, row in data.iterrows():
            if row['比例差值'] <= -0.003:
                order_value(row['持仓股票'], total_v * row['比例差值']*(-1))
            elif row['比例差值'] >= 0.003:
                order_value(row['持仓股票'], total_v * row['比例差值']*(-1))
    else:
        return

'''
持仓股票    atr20   1/atr20     为排名的数据      持仓价值    持仓比例                合适比例                比例差值
中国银行                  按照此依据从大到小排名  持仓市值   该股票占所有的市值比例   根据1/atr20计算应该比例  持仓比例-合适比例
万科                         正数降序，之后是负数，
                             负数按照绝对值降序

'''


def holds_pro(value, total):
    return value / total


def holds_value(security,context):
    return context.portfolio.positions[security].total_amount


def change_for_rank(x):
    if x >= 0:
        return x
    else:
        return x * (-1) * 0.001


def renew_rank(context):
    hs_stocks = get_index_stocks('000300.XSHG')  # 沪深三百股票列表
    l = {'沪深三百所有': hs_stocks}
    data = pd.DataFrame(l)
    data['排名依据'] = data['沪深三百所有'].apply(get_rank, args=(context,))
    data = data.sort_values('排名依据',ascending=False)
    value = context.portfolio.total_value  # 账户总价值
    data['atr20'] = data['沪深三百所有'].apply(get_ATR, args=(context,))
    data['头寸规模'] = data['atr20'].apply(position, args=(value,))
    data['缺口'] = data['沪深三百所有'].apply(gap, args=(context,)) 
    data['缺口']=data['缺口'].apply(lambda x:not x)
    data = data[data['缺口']]
    data = data.reset_index()
    return data
    '''
    data
      沪深三百所有    排名依据    atr20   头寸规模                    缺口
    0  股票代码       收益率*r2   atr20   账户总价值*0.001/ATR20    True
    1             按照此依据从大到小排名                            False
    2
    3


    '''


def get_rank(stock,context,days=250):
    data = get_price(stock, end_date=context.previous_date,count=g.day,skip_paused=True)
    return_rate, r2 = get_return_rate(data, days=g.day)
    return float(return_rate * r2)


def get_ma(days, data):
    # days=number,data=pandas
    data['ave'] = data['close'].rolling(days).mean()
    return data['ave'].iloc[-1]


def get_ATR(stock,context,days=20):
    data = get_price(stock, end_date=context.previous_date,count=42,skip_paused=True)
    close_ATR = data['close']
    high_ATR = data['high']
    low_ATR = data['low']
    atr_l= talib.ATR(high_ATR, low_ATR, close_ATR, days)
    atr = atr_l[-1]
    return atr


def get_return_rate(data, days=250):
    k, r2 = linear_regression(data)
    return_rate = (1+k)** days-1
    return return_rate, r2


def linear_regression(data, days=7):
    days = (-1) * days
    data = data[days:]
    data=data.fillna(data.mean())
    y = data['close']
    x=range(len(y))
    x=np.asarray(x)
    x=x.reshape(-1,1)
    y=np.asarray(y)
    y=np.asarray(list(map(math.log, y)))
    y=y.reshape(-1,1)
    reg = linear_model.LinearRegression().fit(x, y)
    k = reg.coef_[0]
    r2 = reg.score(x, y)
    return k, r2


def gap( stock,context,depth=0.12,days=7):
    data = get_price(stock,end_date=context.previous_date, count=days,skip_paused=True)
    max_price = data['high'].max()
    new_price = data['close'].iloc[-1]
    if new_price <= max_price * (1 - depth):
        return True


def position(atr, total, rate=0.002):
    pos = total * rate / atr
    return pos
