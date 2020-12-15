# coding=utf-8

import requests
import json
import asyncio
import time
import numpy

buyMessage = {'上攻10日线：\n', '低位启动：\n', '低位强势启动：\n', '上攻30日线：\n', '方法9：\n', '上攻20日线：\n', '强势股上攻10日线：\n', '上升中的缩量整理：\n',
              '冲破60日线：\n', "if data[i-1][3]>MA60 and data[i-2][2]<preMA60 and data[i-3][2]<ppreMA60 \
        and data[i-4][2]<pppreMA60 and (MA5>=MA10 and preMA5>=preMA10 and ppreMA5>=ppreMA10)  \
        and data[i-1][3]>data[i-2][2]*1.09 \
        and (MA5>=preMA5 and MA10>=preMA10>=ppreMA10):   60：\n"}
right = []
fault = []
rate = []
for i in range(0, 10):
    right.append(0)
    fault.append(0)

stockRecord = []
stockPool = []
sellMessage = ''
outOfData = '超过5日：\n'
holdMessage = ''
warnMessage = ''
dangerMessage = ''







def sendMessage(message):
    data = {
        "appToken": "AT_U950xOUDtPQmzFNzOLwI99TaDGPvS7rp",
        "content": message,
        "contentType": 1,  # 内容类型 1表示文字  2表示html(只发送body标签内部的数据即可，不包括body标签) 3表示markdown
        "topicIds": [  # 发送目标的topicId，是一个数组！！！
            123
        ],
        "uids": [  # 发送目标的UID，是一个数组！！！
            "UID_Hoe5dkX9dnPXf9QyYj51cTGu3suh",
            "UID_QcQLiLQZSxxjKPbM80wTqXOMJkJP",
            # "UID_Lzi5IAljUc45Rq27M6zNKdAb9unm",
            # "UID_3FScq4H1FgG92RaoRT5Fx5VrnV5p",
            # "UID_S69EAHJVgFPxpUqgzCpGaUHZBnwj",
            # "UID_lSXk2aqmLsHaQoWxTyosPyVegBTZ",
            # "UID_ceA46CD7UBTr1oRqGN7Gd9evieur"
        ]
    }
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    re = requests.post('http://wxpusher.zjiecode.com/api/send/message', data=json.dumps(data), headers=headers)


def warn(name, symbol):
    global warnMessage
    warnMessage += '预警 ' + name + ' ' + symbol + '\n'


def danger(name, symbol):
    global dangerMessage
    dangerMessage += '危险 ' + name + ' ' + symbol + '\n'


def buy(which, i, name, symbol):
    global buyMessage
    buyMessage[which] += '时间：' + str(i) + '买 ' + name + ' ' + symbol + '\n'
    stockPool.append(symbol)


def sell(name, symbol):
    global sellMessage
    global stockRecord
    sellMessage += '卖 ' + name + ' ' + symbol + '\n'
    stockRecord.remove(symbol)


def hold(name, symbol):
    global holdMessage
    holdMessage += '持有 ' + name + ' ' + symbol + '\n'


def getABC(data, i, n):
    length = len(data)
    sum = 0
    for j in range(length - n + i, length + i):
        sum += data[j][2]
    MA10_1 = sum / n
    sum = sum - data[length - 1 + i][2] + data[length - n - 1 + i][2]
    MA10_2 = sum / n
    sum = sum - data[length - 2 + i][2] + data[length - n - 2 + i][2]
    MA10_3 = sum / n
    sum = sum - data[length - 3 + i][2] + data[length - n - 3 + i][2]
    MA10_4 = sum / n
    a = MA10_1 - MA10_2
    b = MA10_2 - MA10_3
    c = MA10_3 - MA10_4
    return [a, b, c]


# 持仓条件
def holdRule(MA, preMA, ppreMA, pppreMA):
    MA5, MA10, MA20, MA30, MA60, MA250 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60, preMA250 = preMA
    ppreMA5, ppreMA10, ppreMA20, ppreMA30, ppreMA60, ppreMA250 = ppreMA
    pppreMA5, pppreMA10, pppreMA20, pppreMA30, pppreMA60, pppreMA250 = pppreMA
    if MA250 >= preMA250 >= ppreMA250 >= pppreMA250:
        return True
    return False


# 方法一：买进
def buyRule1(data, MA, preMA, ppreMA, pppreMA, ABC5, ABC10, i, stock):
    MA5, MA10, MA20, MA30, MA60, MA250 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60, preMA250 = preMA
    ppreMA5, ppreMA10, ppreMA20, ppreMA30, ppreMA60, ppreMA250 = ppreMA
    pppreMA5, pppreMA10, pppreMA20, pppreMA30, pppreMA60, pppreMA250 = pppreMA
    A5, B5, C5 = ABC5
    A10, B10, C10 = ABC10
    A30, B30, C30 = getABC(data, i, 30)
    if holdRule(MA, preMA, ppreMA, pppreMA) and -0.02 < (MA20 - MA30) / MA30 < 0.02 and -0.005 < (
            MA30 - MA60) / MA60 < 0.02 \
            and MA5 > MA10 and data[i - 1][5] > (data[i - 2][5] + data[i - 3][5] + data[i - 4][5]) \
            and A5 > B5 and A5 > C5 and C5 <= 0.004 and A5 > 0.01 and A5 > (
            B5 + C5) and A10 > B10 and B10 > C10 and A10 > 0.005 \
            and MA60 > preMA60 > ppreMA60:
        # and (MA5*1.035>data[i][4] or MA5*1.035>data[i+1][4]):
        stock['buyPrice'] = MA5 * 1.035
        if MA5 * 1.035 > data[i][4]:
            stock['buyDay'] = i
        else:
            stock['buyDay'] = i + 1
        return True
    return False


# 方法一：卖出
def sellRule1(data, MA, preMA, ppreMA, pppreMA, ABC5, ABC10, i, stock):
    if data[i - 1][2] < data[i - 2][2]:
        stock['income'] = (data[i - 1][2] - stock['buyPrice']) / stock['buyPrice']
        return True
    return False


def buySuccess2(data, j, stock):
    for i in range(0, 10):
        if data[j + i][2] < getMA(data, j - i)[1]:
            stock['buyPrice'] = data[j + i][2]
            stock['buyDay'] = j + i
            return True
    return False


# 方法二：买进
def buyRule2(data, MA, preMA, ppreMA, pppreMA, ABC5, ABC10, i, stock):
    MA5, MA10, MA20, MA30, MA60, MA250 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60, preMA250 = preMA
    ppreMA5, ppreMA10, ppreMA20, ppreMA30, ppreMA60, ppreMA250 = ppreMA
    pppreMA5, pppreMA10, pppreMA20, pppreMA30, pppreMA60, pppreMA250 = pppreMA
    A5, B5, C5 = ABC5
    A10, B10, C10 = ABC10
    if holdRule(MA, preMA, ppreMA, pppreMA) and -0.06 < MA5 > MA10 and (MA10 - MA250) / MA250 < 0.15 and -0.016 < (
            MA20 - MA30) / MA30 < 0 and -0.016 < (MA30 - MA60) / MA60 < 0 \
            and (data[i - 1][5] + data[i - 2][5] + data[i - 3][5]) > (
            data[i - 4][5] + data[i - 5][5] + data[i - 6][5]) * 2.7 \
            and (A5 + B5 + C5) > 0.075 and (A10 + B10 + C10) > 0.05:
        return True
    return False


# 方法三：买进
def buyRule3(data, MA, preMA, ppreMA, pppreMA, ABC5, ABC10, i, stock):
    MA5, MA10, MA20, MA30, MA60, MA250 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60, preMA250 = preMA
    ppreMA5, ppreMA10, ppreMA20, ppreMA30, ppreMA60, ppreMA250 = ppreMA
    pppreMA5, pppreMA10, pppreMA20, pppreMA30, pppreMA60, pppreMA250 = pppreMA
    A5, B5, C5 = ABC5
    A10, B10, C10 = ABC10
    A20, B20, C20 = getABC(data, i, 20)
    if A10 > 0.007 and B10 > 0.007 and (A10 + B10) > 0.018 and -0.005 < (ppreMA10 - ppreMA20) / ppreMA20 < 0.005 \
            and (MA10 - MA20) / MA20 > (ppreMA10 - ppreMA20) / ppreMA20 + 0.011 and MA60 >= preMA60 > ppreMA60 \
            and data[i - 1][2] < data[i - 2][2] and (MA10 - MA60) / MA60 < 0.15 and (MA30 - MA60) / MA60 < 0.07:
        stock['buyPrice'] = data[i - 1][2]
        stock['buyDay'] = i - 1
        return True
    return False


# 拉升中的回踩
def buyRule4(data, MA, preMA, ppreMA, pppreMA, ABC5, ABC10, i, stock):
    MA5, MA10, MA20, MA30, MA60, MA250 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60, preMA250 = preMA
    ppreMA5, ppreMA10, ppreMA20, ppreMA30, ppreMA60, ppreMA250 = ppreMA
    pppreMA5, pppreMA10, pppreMA20, pppreMA30, pppreMA60, pppreMA250 = pppreMA
    pre5MA5, pre5MA10, pre5MA20, pre5MA30, pre5MA60, pre5MA250 = getMA(data, i - 5)
    A5, B5, C5 = ABC5
    A10, B10, C10 = ABC10
    A20, B20, C20 = getABC(data, i, 20)
    if MA60 < MA30 < MA60 * 1.02 and MA20 > pre5MA20 * 1.025 and MA10 > pre5MA10 * 1.07 and MA20 < data[i - 1][
        2] < MA20 * 1.02 and MA60 >= preMA60 and A20 > 0.002:
        return True
    return False


# 上攻10日线
def rule1(data, MA, preMA, ppreMA, i):
    MA5, MA10, MA20, MA30, MA60, MA250 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60, preMA250 = preMA
    if data[i - 1][1] <= MA10 and data[i - 1][2] >= MA10 * 0.995 and MA20 > MA30 > MA60 and (MA10 - MA20) / MA20 < 0.05 \
            and (MA30 - MA60) / MA60 < 0.06 and data[i - 1][5] > data[i - 2][5] * 1.4 and (
            MA10 - preMA10) / preMA10 > -0.003 and newRule8(data, MA, preMA, i):
        return True
    return False


# 低位启动
def rule2(data, MA, preMA, ppreMA, i):
    MA5, MA10, MA20, MA30, MA60 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60 = preMA
    if (abs(MA20 - MA30) / MA30 < 0.015 or MA20 > MA30 > MA60) and (preMA10 - preMA20) / preMA20 < (
            MA10 - MA20) / MA20 * 0.6 \
            and (MA10 - preMA10) / preMA10 > 0.016 and data[i - 1][1] < MA5 and data[i - 1][2] > MA5 and abs(
        MA30 - MA60) / MA60 < 0.015:
        return True
    return False


# 低位强势启动
def rule3(data, MA, preMA, ppreMA, i):
    MA5, MA10, MA20, MA30, MA60 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60 = preMA
    if (MA10 - preMA10) / preMA10 > 0.15 and (MA10 - MA20) / MA20 < 0.025 and MA10 > MA20:
        return True
    return False


# 上攻30日线
def rule4(data, MA, preMA, ppreMA, i):
    MA5, MA10, MA20, MA30, MA60 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60 = preMA
    if MA30 > MA60 and MA30 > MA20 and abs(MA10 - MA20) / MA20 < 0.02 \
            and (MA5 - preMA5) / preMA5 > 0.01 and 0.001 <= (MA10 - preMA10) / preMA10 < (MA5 - preMA5) / preMA5 \
            and MA30 < preMA30 and MA60 < preMA60 and data[i - 1][2] > MA30 * 0.99 and data[i - 2][
        2] < preMA30 and newRule8(data, MA, preMA, i):
        return True
    return False


# 方法9
def rule5(data, MA, preMA, ppreMA, i):
    MA5, MA10, MA20, MA30, MA60 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60 = preMA
    ppreMA5, ppreMA10, ppreMA20, ppreMA30, ppreMA60 = ppreMA
    if MA5 > MA10 > MA20 and (MA10 - MA20) / MA20 + (MA20 - MA30) / MA30 + (MA30 - MA60) / MA60 < 0.09 and data[i - 1][
        2] < MA10 \
            and (MA10 - preMA10) / preMA10 > 0.002 and (MA20 - preMA20) / preMA20 > 0.002 and newRule8(data, MA, preMA,
                                                                                                       i):
        return True
    return False


# 上攻20日线
def rule6(data, MA, preMA, ppreMA, i):
    MA5, MA10, MA20, MA30, MA60 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60 = preMA
    if MA20 > MA10 and MA20 > MA30 > MA60 and MA5 > MA10 and (MA10 - preMA10) / preMA10 >= 0 \
            and (MA30 - preMA30) / preMA30 >= 0.006 and (MA5 - preMA5) / preMA5 >= 0.009 \
            and data[i - 1][2] > MA20 and data[i - 2][2] < preMA20 and abs(MA10 - MA30) / MA30 > 0.015 \
            and (MA5 - MA10) / MA10 >= (preMA5 - preMA10) / preMA10 * 2 and newRule8(data, MA, preMA, i):
        return True
    return False


# 强势股上攻10日线
def rule7(data, MA, preMA, ppreMA, i):
    MA5, MA10, MA20, MA30, MA60 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60 = preMA
    ppreMA5, ppreMA10, ppreMA20, ppreMA30, ppreMA60 = ppreMA
    if MA20 > MA30 > MA60 and MA10 < preMA10 and (MA5 - preMA5) / preMA5 > 0.0009 and 0 <= (
            preMA5 - ppreMA5) / ppreMA5 < (MA5 - preMA5) / preMA5 * 0.5 \
            and data[i - 1][2] > MA10 and data[i - 2][2] < MA10 and (MA30 - MA60) / MA60 > 0.11 and newRule8(data, MA,
                                                                                                             preMA, i):
        return True
    return False


# 上升中的缩量整理
def rule8(data, MA, preMA, ppreMA, i):
    MA5, MA10, MA20, MA30, MA60 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60 = preMA
    if MA5 > MA10 and MA20 > MA30 > MA60 and data[i - 2][2] > MA10 and data[i - 3][2] > MA10 and data[i - 1][
        2] < MA5 * 1.004 and data[i - 1][2] < MA10 * 1.02 \
            and data[i - 1][2] < data[i - 2][2] * 0.99 and data[i - 1][2] < data[i - 3][2] * 0.99 and (
            MA10 - MA20) / MA20 < 0.05 and (MA30 - MA60) / MA60 < 0.05 \
            and (MA5 - preMA5) / preMA5 > 0.002 and data[i - 1][5] < data[i - 2][5] and data[i - 2][5] < data[i - 3][
        5] and newRule8(data, MA, preMA, i):
        return True
    return False


# 冲破60日线
def rule9(data, MA, preMA, ppreMA, i):
    MA5, MA10, MA20, MA30, MA60 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60 = preMA
    ppreMA5, ppreMA10, ppreMA20, ppreMA30, ppreMA60 = ppreMA
    if (MA10 - preMA10) / preMA10 > 0.006 and MA10 > MA60 and preMA10 <= preMA60 * 1.002 and \
            (MA5 - preMA5) / preMA5 > (MA10 - preMA10) / preMA10 * 0.75 and newRule8(data, MA, preMA, i):
        return True
    return False


def max(data, start, end):
    max = data[start][3]
    for i in range(start, end + 1):
        if data[i][3] > max:
            max = data[i][3]
    return max


# 牛股
def rule10(data, MA, preMA, ppreMA, pppreMA, i):
    MA5, MA10, MA20, MA30, MA60, MA250 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60, preMA250 = preMA
    ppreMA5, ppreMA10, ppreMA20, ppreMA30, ppreMA60, ppreMA250 = ppreMA
    pppreMA5, pppreMA10, pppreMA20, pppreMA30, pppreMA60, pppreMA250 = pppreMA
    if data[i - 1][3] > MA60 and data[i - 2][2] < preMA60 and data[i - 3][2] < ppreMA60 \
            and data[i - 4][2] < pppreMA60 \
            and holdRule(MA, preMA, ppreMA, pppreMA) \
            and data[i - 1][3] > data[i - 2][2] * 1.095 \
            and (MA5 > preMA5 > ppreMA5 and MA10 > preMA10) \
            and newRule8(data, MA, preMA, i):
        return True
    return False


def rule11(data, MA, preMA, ppreMA, pppreMA, i):
    MA5, MA10, MA20, MA30, MA60, MA250 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60, preMA250 = preMA
    ppreMA5, ppreMA10, ppreMA20, ppreMA30, ppreMA60, ppreMA250 = ppreMA
    pppreMA5, pppreMA10, pppreMA20, pppreMA30, pppreMA60, pppreMA250 = pppreMA
    if holdRule(MA, preMA, ppreMA, pppreMA) \
            and data[i - 1][2] > data[i - 2][2] * 1.09 > data[i - 3][2] * 1.09 > data[i - 4][2] * 1.09 > data[i - 5][
        2] * 1.09 > data[i - 6][2] * 1.09 \
            and newRule8(data, MA, preMA, i):
        return True
    return False


def rule12(data, MA, preMA, ppreMA, pppreMA, ABC5, ABC10, i, stock):
    MA5, MA10, MA20, MA30, MA60, MA250 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60, preMA250 = preMA
    ppreMA5, ppreMA10, ppreMA20, ppreMA30, ppreMA60, ppreMA250 = ppreMA
    pppreMA5, pppreMA10, pppreMA20, pppreMA30, pppreMA60, pppreMA250 = pppreMA
    A5, B5, C5 = ABC5
    A10, B10, C10 = ABC10
    A20, B20, C20 = getABC(data, i, 20)
    if data[i - 1][2] > MA60 * 0.985 and data[i - 1][2] < MA60 * 1.05 and (
            A20 > 0.007 or (A20 > 0.005 and A10 < 0.005)) and MA60 >= preMA60:
        return True
    return False


def max1(data, start, end):
    max = data[end][3]
    for i in range(start - 1, end):
        if (max < data[i][3]):
            max = data[i][3]
    return max


def min1(data, start, end):
    min = data[end][4]
    for i in range(start - 1, end):
        if (min > data[i][4]):
            min = data[i][4]
    return min


def wR(data, day, offset):
    Hn = max1(data, -day - offset, -1 - offset)
    Ln = min1(data, -day - offset, -1 - offset)
    return (Hn - data[-1 - offset][2]) / (Hn - Ln) * 100


def wR1(data):
    if wR(data, 21, 0) >= 98 and wR(data, 42, 0) >= 98:
        # and wR(data,21,1)<=80 and wR(data,42,1)<=80:
        print(wR(data, 21, 2))
        print(wR(data, 42, 2))
        print(wR(data, 21, 1))
        print(wR(data, 42, 1))
        return True


# 卖出条件
def ruleSell(MA, ABC10, ABC5, i):
    MA5, MA10, MA20, MA30, MA60 = MA
    a10, b10, c10 = ABC10
    a5, b5, c5 = ABC5
    if a10 < b10 < c10 and a5 < b5 < c5 and (MA10 - MA20) / MA20 > 0.04:
        return True
    return False


# 穿头破脚
def newRule8(data, MA, preMA, i):
    MA5, MA10, MA20, MA30, MA60, MA250 = MA
    preMA5, preMA10, preMA20, preMA30, preMA60, preMA250 = preMA
    if data[i - 1][1] < data[i - 2][4] * 1.007 and data[i - 1][2] > data[i - 2][3] * 0.995 and (
            MA10 - MA20) / MA20 > 0.03 \
            and (MA10 - preMA10) / preMA10 > 0.014 and (MA10 - MA20) / MA20 + (MA10 - preMA10) / preMA10 > 0.06:
        return False
    return True


rules = [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10]
qualify = [[3, 0.1], [30, 0.3], [40, 0.4], [20, 0.2], [5, 0.15], [20, 0.2], [20, 0.2], [3, 0.1], [40, 0.3], [60, 0.4]]


def qualified(data, i, j, day, inc, name, symbol, stock):
    global rules, right, fault
    r = False
    # i = stock['buyDay']
    for k in range(4, day):
        if (max(data, i + 1, i + k + 1) - data[i][2]) / data[i][2] >= 0.005 * k:
            # buy(j, data[i - 1][0], name, symbol)
            right[j] += 1
            r = True
            break
    if not r:
        fault[j] += 1


def dealData(data, name, symbol, doWhat, stock):
    global rules, right, fault
    length = len(data)
    if length >= 300:
        # for i in range(-1000, -70):
        i = 0
        # MA = getMA(data, i, 0)
        # preMA = getMA(data, i, 1)
        # ppreMA = getMA(data, i, 2)
        # pppreMA = getMA(data, i, 3)
        # A = getA(data)
        # ABC10 = getABC(data,i,10)
        # ABC5 = getABC(data,i,5)
        # MA10a, MA20a = A
        # if rule6(data) and rule5(data, MA, ABC) and rule4(data, MA):
        #     return buy(name, symbol)
        # MA5 = MA[0]
        if doWhat == 'sell':
            # if ruleSell(MA, ABC10, ABC5,i) or not newRule8(data, MA, preMA, i):
            # return sell(name, symbol)
            pass
        else:
            # if not ruleSell(MA, ABC10, ABC5,i):
            #     for j in range(0, len(rules)):
            #         if buyRule3(data, MA, preMA, ppreMA,pppreMA, ABC5, ABC10, i, stock):
            if wR1(data):
                j = 9
                print(name + data[i - 1][0] + '\t' + str(data[i - 1][2]) + '\t' + data[i - 2][0] + '\t' + str(
                    data[i - 2][2]) + '\t' + data[i - 3][0] + '\t' + str(data[i - 3][2]) + '\t' + data[i - 4][
                          0] + '\t' + str(data[i - 4][2]) + '\t' + data[i - 5][0] + '\t' + str(data[i - 5][2]) + '\t')
                # day, inc = qualify[j]
                # qualified(data, i, j, day, inc,name,symbol,stock)
                # if j==9:
                buy(j, data[i - 1][0], name, symbol)


async def getData(stockCode, dealData, doWhat):
    url0 = 'http://img1.money.126.net/data/hs/kline/day/history/2014/' + stockCode + '.json'
    url1 = 'http://img1.money.126.net/data/hs/kline/day/history/2015/' + stockCode + '.json'
    url2 = 'http://img1.money.126.net/data/hs/kline/day/history/2016/' + stockCode + '.json'
    url3 = 'http://img1.money.126.net/data/hs/kline/day/history/2017/' + stockCode + '.json'
    url4 = 'http://img1.money.126.net/data/hs/kline/day/history/2018/' + stockCode + '.json'
    url5 = 'http://img1.money.126.net/data/hs/kline/day/history/2019/' + stockCode + '.json'
    url6 = 'http://img1.money.126.net/data/hs/kline/day/history/2020/' + stockCode + '.json'
    future0 = loop.run_in_executor(None, requests.get, url0)
    future1 = loop.run_in_executor(None, requests.get, url1)
    future2 = loop.run_in_executor(None, requests.get, url2)
    future3 = loop.run_in_executor(None, requests.get, url3)
    future4 = loop.run_in_executor(None, requests.get, url4)
    future5 = loop.run_in_executor(None, requests.get, url5)
    future6 = loop.run_in_executor(None, requests.get, url6)
    re0 = await future0
    re1 = await future1
    re2 = await future2
    re3 = await future3
    re4 = await future4
    re5 = await future5
    re6 = await future6
    if re0.status_code == 200 and re1.status_code == 200 and re2.status_code == 200 and re3.status_code == 200 and re4.status_code == 200 and re5.status_code == 200 and re6.status_code == 200:
        data0 = json.loads(re0.text)
        data1 = json.loads(re1.text)
        data2 = json.loads(re2.text)
        data3 = json.loads(re3.text)
        data4 = json.loads(re4.text)
        data5 = json.loads(re5.text)
        data6 = json.loads(re6.text)
        name = data5['name']
        symbol = data5['symbol']
        print(name)
        data = data0['data'] + data1['data'] + data2['data'] + data3['data'] + data4['data'] + data5['data'] + data6[
            'data']
        stock = {}
        dealData(data, name, symbol, doWhat, stock)


def getData1(stockCode, dealData, doWhat):
    if stockCode.startswith('60'):
        stockCode = '0' + stockCode
    else:
        stockCode = '1' + stockCode
    data = []
    name = ''
    symbol = ''
    for i in range(0, 7):
        url1 = 'http://img1.money.126.net/data/hs/kline/day/history/20' + str(14 + i) + '/' + stockCode + '.json'
        # future1 = loop.run_in_executor(None, requests.get, url1)
        # future2 = loop.run_in_executor(None, requests.get, url2)
        # re1 = await future1
        # re2 = await future2
        re1 = requests.get(url1)
        # re2 = requests.get(url2)
        if re1.status_code == 200:
            data1 = json.loads(re1.text)
            name = data1['name']
            symbol = data1['symbol']
            print(name)
            data = data1['data'] + data
    dealData(data, name, symbol, doWhat)


# with open('record4.txt', "r") as f:
#     stockCodes = f.readlines()
#     for stockCode in stockCodes:
#         outOfData += '卖 '+stockCode
#
# for i in range(3, -1, -1):
#     stockRecord = []
#     with open('record'+str(i)+'.txt', "r") as f:
#         stockCodes = f.readlines()
#         for stockCode in stockCodes:
#                 stockRecord.append(stockCode.strip())
#     if len(stockRecord)>0:
#         tasks = [(getData1(stockCode, dealData, 'sell')) for stockCode in stockRecord]
#         # loop = asyncio.get_event_loop()
#         # loop.run_until_complete(asyncio.wait(tasks))
#         # loop.close()
#     with open('record'+str(i+1)+'.txt', "w") as f:
#         f.write('\n'.join(stockRecord))


globalStockCodes = []

with open("sh.txt", "r") as f:
    stockCodes = f.readlines()  # 读取全部内容 ，并以列表方式返回
    for stockCode in stockCodes:
        if stockCode.startswith('60') or stockCode.startswith('30') or stockCode.startswith('00'):
            globalStockCodes.append('0' + stockCode.strip())

with open("sz.txt", "r") as f:
    stockCodes = f.readlines()  # 读取全部内容 ，并以列表方式返回
    for stockCode in stockCodes:
        if stockCode.startswith('60') or stockCode.startswith('30') or stockCode.startswith('00'):
            globalStockCodes.append('1' + stockCode.strip())

tasks = [asyncio.ensure_future(getData(stockCode, dealData, 'buy')) for stockCode in globalStockCodes]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))
loop.close()

# getData('0600521', dealData)
# with open('stockList.txt', 'r', encoding='utf-8') as f:
#     lines = f.readlines()
#     for line in lines:
#         stockCode = line[line.find(' '):].strip()
#         # stockCode = '000733'
#         if stockCode[:2]=='60':
#             stockCode = '0' + stockCode
#         else:
#             stockCode = '1' + stockCode
#         getData(stockCode, dealData)

tips = '达标条件：20天20%\n样本：最近100天数据'
message = tips + warnMessage + '\n\n' + dangerMessage + '\n\n'
for i in range(0, len(buyMessage)):
    if (right[i] + fault[i]) == 0:
        rate = 0
    else:
        rate = right[i] / (right[i] + fault[i])
    message += buyMessage[i] + '正确：' + str(right[i]) + '\n' + '错误：' + str(fault[i]) + '\n正确率' + str(rate) + '\n\n'
message += sellMessage + '\n\n' + holdMessage + '\n\n' + outOfData
sendMessage(message)

with open('record0.txt', "w") as f:
    f.write('\n'.join(stockPool))
