# coding=utf-8

import requests
import json
import asyncio
import numpy
import time
import datetime


class StockSelector(object):
    def __init__(self, data, commonMAConfig, stockPool):
        '''
        :param data: {name: 股票名称, code: 股票代码, kline: k线数据}
        :param commonMAConfig:
        '''

        '''
        data['kline']是一个股票的k线数据，包含
        包含7个基本数据：[日期,开盘价,收盘价,最高价,最低价,成交量(总手数，一手就是100股),成交额(多少元),振幅]
        example: ["2015-05-28", 13.51, 16.21, 16.21, 13.51, 57, 91451.00, 23.98]
        '''
        self.kline = data['kline']
        # 股票名称
        self.name = data['name']
        # 股票代码
        self.code = data['code']
        '''
        股票基本面数据
        {
            date: "2020-03-31", # 日期
        # 每股指标
            jbmgsy: "-0.0300",  # 基本每股收益(元)
            kfmgsy: "--",       # 扣非每股收益(元)
            xsmgsy: "-0.0300",  # 稀释每股收益(元)
            mgjzc: "3.9506",    # 每股净资产(元)
            mggjj: "0.4976",    # 每股公积金(元)
            mgwfply: "2.3538",  # 每股未分配利润(元)
            mgjyxjl: "-0.0454", # 每股经营现金流(元)
        # 成长能力指标
            yyzsr: "1.64亿",       # 营业总收入(元)
            mlr: "1595万",         # 毛利润(元)
            gsjlr: "-2772万",      # 归属净利润(元)
            kfjlr: "-2784万",      # 扣非净利润(元)
            yyzsrtbzz: "-69.19",   # 营业总收入同比增粘(%)
            gsjlrtbzz: "-120.00",  # 归属净利润同比增长(%)
            kfjlrtbzz: "-120.44",  # 扣非净利润同比增长(%)
            yyzsrgdhbzz: "-18.29", # 营业总收入滚动环比增长(%)
            gsjlrgdhbzz: "-42.63", # 归属净利润滚动环比增长(%)
            kfjlrgdhbzz: "-43.76", # 扣非净利润滚动环比增长(%)
        # 盈利能力指标
            jqjzcsyl: "-0.68",      # 加权净资产收益率(%)
            tbjzcsyl: "-0.68",      # 摊薄净资产收益率(%)
            tbzzcsyl: "-0.41",      # 摊薄总资产收益率(%)
            mll: "10.93",           # 毛利率(%)
            jll: "-17.11",          # 净利率(%)
            sjsl: "--",             # 实际税率(%)
        # 盈利质量指标
            yskyysr: "0.22",        # 预收款/营业收入
            xsxjlyysr: "1.08",      # 销售现金流/营业收入
            jyxjlyysr: "-0.29",     # 经营现金流/营业收入
        # 运营能力指标
            zzczzy: "0.02",         # 总资产周转率(次)
            yszkzzts: "247.13",     # 应收款周转天数(天)
            chzzts: "1639.48",      # 存货周转天数(天)
        # 财务风险指标
            zcfzl: "40.98",         # 资产负债率(%)
            ldzczfz: "80.17",       # 流动负债/总负债(%)
            ldbl: "1.76",           # 流动比率
            sdbl: "0.61"            # 速动比率
        }
        '''
        self.finance = data['finance']
        # self.commonMA一定要在self.getMA之前计算，因为后者依赖了前者
        self.commonMA = self.getCommonMA(commonMAConfig)
        self.stockPool = stockPool

    def getCommonMA(self, commonMAConfig, j=0):
        '''
        计算常用的均线
        :param j: j表示往前数第几天，比如想计算三天前的MA，j传-3，默认j=0
        :return: [MA5, MA10, MA20, MA30, MA60, MA90, MA120, MA250]
        '''
        s = [0]
        for i in range(len(commonMAConfig) - 1):
            s.append(
                sum(d[2] for d in
                    self.kline[-1 - commonMAConfig[i + 1] + j: -1 - commonMAConfig[i] + j]) + s[i])
        MA = list(map(lambda x, y: x / float(y), s[1:], commonMAConfig[1:]))
        return dict(zip(commonMAConfig[1:], MA))

    def getMA(self, N, j=0):
        '''
        通用均线计算
        :param N: N表示想获取多长时间的均线，比如获取5日均线，N传5
        :param j: j表示往前数第几天，比如想计算三天前的MA，j传-3
        :return: [MAn]
        '''
        if j == 0 and N in self.commonMA.keys():
            return self.commonMA[N]
        return sum(d[2] for d in self.kline[-1 - N + j: -1 + j]) / float(N)

    def getBoll(self, N=20, K=2, j=0):
        '''
        一般情况下，设定N=20和K=2，这两个数值也是在布林带当中使用最多的。
        在日线图里，N=20其实就是“月均线”（MA20）。
        依照正态分布规则，约有95%的数值会分布在距离平均值有正负2个标准差(±2σ)的范围内。
        :param N: N代表一个时间段
        :param K: K代表几倍标准差
        :param j: j表示往前数第几天，比如想计算昨天的MA，j传-1
        :return: [中轨值, 上轨值, 下轨值, %b指标, 宽带指标]
        '''
        MB = self.getMA(N)
        delta = K * numpy.std([d[2] for d in self.kline[-1 - N + j: -1 + j]])
        UP = MB + delta
        LB = MB - delta
        PB = (self.kline[-1 + j][2] - LB) / (UP - LB)
        BW = (UP - LB) / MB
        return [MB, UP, LB, PB, BW]

    def getWR(self, N=14, j=0):
        '''
        威廉线，用于判断超买超卖信号
        :param N: 多少天，一般是14天
        :param j: j表示往前数第几天，比如想计算三天前的MA，j传-3
        :return: 威廉线的值
        '''
        Hn = max(d[2] for d in self.kline[-1 - N + j: -1 + j])
        Ln = min(d[2] for d in self.kline[-1 - N + j: -1 + j])
        return (Hn - self.kline[-1 + j][2]) / (Hn - Ln) * 100

    def max(self, arr, start, end, j):
        res = arr[start][j]
        index = start
        for i in range(start, end):
            if res < arr[i][j]:
                res = arr[i][j]
                index = i
        return index

    def method03(self):
        MA100 = self.getMA(100)
        MA200 = self.getMA(200)
        MA400 = self.getMA(400)
        pre50MA100 = self.getMA(100, -50)
        MA10 = self.getMA(10)
        MA20 = self.getMA(20)
        # preMA10 = self.getMA(10, -1)
        # pre2MA10 = self.getMA(10, -2)
        # preMA20 = self.getMA(20, -1)
        # pre2MA20 = self.getMA(20, -2)
        MA5 = self.getMA(5)
        if (MA100 - pre50MA100) / pre50MA100 > 0.03 and (MA5 > MA20 >= MA10) and (MA100 - MA200) / MA200 + (
                MA200 - MA400) / MA400 < 0.42:
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
            })
            return True

    def method04(self):
        MA100 = self.getMA(100)
        MA200 = self.getMA(200)
        MA400 = self.getMA(400)
        pre200MA400 = self.getMA(400, -200)
        pre50MA100 = self.getMA(100, -50)
        MA10 = self.getMA(10)
        MA20 = self.getMA(20)
        preMA10 = self.getMA(10, -1)
        pre2MA10 = self.getMA(10, -2)
        pre3MA10 = self.getMA(10, -3)
        preMA20 = self.getMA(20, -1)
        pre2MA20 = self.getMA(20, -2)
        MA5 = self.getMA(5)
        preSum5 = sum(d[5] for d in self.kline[- 11: -6])
        sum5 = sum(d[5] for d in self.kline[- 6: -1])
        if MA200 > MA400 and (
                MA400 - pre200MA400) / pre200MA400 > 0.09 and MA5 > MA10 >= MA20 and preMA10 <= preMA20 and pre2MA10 < pre2MA20 and sum5 > preSum5 * 1.1 and (
                MA10 - pre3MA10) / pre3MA10 > 0.003:
            self.stockPool.append({
                'method': 1,
                'name': self.name,
                'code': self.code,
            })
            return True

    def method05(self):
        MA5 = self.getMA(5)
        MA10 = self.getMA(10)
        MA20 = self.getMA(20)
        MA50 = self.getMA(50)
        MA100 = self.getMA(100)
        preSum5 = sum(d[5] for d in self.kline[- 11: -6])
        sum5 = sum(d[5] for d in self.kline[- 6: -1])
        if MA5 > MA10 > MA20 and abs(MA20 - MA50) / MA50 + abs(MA50 - MA100) / MA100 < 0.05 and sum5 > preSum5 * 2:
            self.stockPool.append({
                'method': 2,
                'name': self.name,
                'code': self.code,
            })
            return True

    def method06(self):
        MA10 = self.getMA(10)
        MA20 = self.getMA(20)
        pre10MA20 = self.getMA(20, -10)
        pre20MA50 = self.getMA(50, -20)
        pre20MA100 = self.getMA(100, -20)
        MA50 = self.getMA(50)
        MA100 = self.getMA(100)
        MA200 = self.getMA(200)
        MA400 = self.getMA(400)
        condition2 = abs(MA50 - MA100) / MA100
        condition3 = abs(MA100 - MA200) / MA200
        preSum10 = sum(d[5] for d in self.kline[- 21: -11])
        sum10 = sum(d[5] for d in self.kline[- 11: -1])
        if (MA50 > MA100 or MA100 > MA200) and ((MA50 - pre20MA50) / pre20MA50 < 0.04 or (
                MA100 - pre20MA100) / pre20MA100 < 0.02) and condition2 < 0.06 and condition3 < 0.085 and (
                condition2 + condition3) < 0.09 and sum10 > preSum10 * 1.1 and (
                self.kline[-1][2] < MA100 * 1.05 or self.kline[-1][2] < MA50 * 1.05) and (
                MA400 < MA200 or MA400 < MA100 or MA400 < MA50) and MA10 > MA20 and (
                MA20 - pre10MA20) / pre10MA20 > 0.025:
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
            })
            return True

    def method02(self):
        MA20 = self.getMA(20)
        MA35 = self.getMA(35)
        MA70 = self.getMA(70)
        MA140 = self.getMA(140)
        MA210 = self.getMA(210)
        MA420 = self.getMA(420)
        pre100MA210 = self.getMA(210, -100)
        pre3MA20 = self.getMA(20, -3)
        pre3MA35 = self.getMA(35, -3)
        D = (pre100MA210 - MA210) / pre100MA210
        C = (MA140 - MA210) / MA210
        B = (MA70 - MA140) / MA140
        A = (MA35 - MA70) / MA70
        if MA70 > MA140 > MA210 > MA420 and 0.15 < D < 1 and 0.03 < C < 0.3 and -0.02 < A + B < 0.09 and 0.2 < (
                A + B + C) / D < 0.8 and MA20 > MA35 and pre3MA20 < pre3MA35 and 0.4 < D + (A + B + C) / D < 1.2:
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
            })
            return True

    def method01(self):
        MA20 = self.getMA(20)
        MA35 = self.getMA(35)
        MA70 = self.getMA(70)
        MA140 = self.getMA(140)
        MA280 = self.getMA(280)
        MA420 = self.getMA(420)
        MA20_pre20 = self.getMA(20, -20)
        MA35_pre20 = self.getMA(35, -20)
        MA70_pre20 = self.getMA(70, -20)
        max7_vol = self.max(self.kline, 8, -1, 5)
        if MA35 > MA70 > MA140 > MA280 > MA420 and self.kline[-1][5] < self.kline[-2][5] < self.kline[-3][5] and \
                self.kline[-1][2] < self.kline[-2][2] < self.kline[-3][2] < self.kline[-4][2] and MA35 * 0.97 > \
                self.kline[-1][2] < MA20 * 1.04 and (MA20 - MA20_pre20) / MA20_pre20 > 0.06 and (
                MA35 - MA35_pre20) / MA35_pre20 > 0.06 and (MA70 - MA70_pre20) / MA70_pre20 > 0.08 and self.kline[-1][
            5] < self.kline[max7_vol][5] * 0.4:
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
            })
            return True

    def method00(self, j=-10):
        '''
        技术面：
            均线粘合
            成交量比前面三天加起来还多
        :return: 是否符合条件
        '''
        MA10 = self.getMA(10)
        MA20 = self.getMA(20)
        MA35 = self.getMA(35)
        preMA20 = self.getMA(20, -1)
        ppreMA20 = self.getMA(20, -2)
        max_vol_index = self.max(self.kline, -90, -14, 5)
        average_vol = sum(d[5] for d in self.kline[-14:-3]) / 10
        # [MB, UP, LB, PB, BW] = self.getBoll()
        if abs(MA10 - MA20) / MA20 + abs(MA20 - MA35) / MA35 <= 0.04 and average_vol * 1.8 <= sum(
                d[5] for d in self.kline[-3:]) / 3 and sum(
            d[5] for d in self.kline[max_vol_index - 6:max_vol_index + 5]) / 11 >= average_vol * 3 and (
                self.kline[-1][2] - self.kline[-4][2]) / self.kline[-4][
            2] >= 0.04 and MA20 > preMA20 >= ppreMA20:
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
            })
            return True

    def method0(self, j=-10):
        '''
        技术面：
            均线粘合
            成交量比前面三天加起来还多
        :return: 是否符合条件
        '''
        MA10 = self.getMA(10)
        MA20 = self.getMA(20)
        MA35 = self.getMA(35)
        if abs(MA10 - MA20) / MA20 + abs(MA20 - MA35) / MA35 < 0.032 and self.kline[-1][5] >= 0.9 * (
                self.kline[-2][5] + self.kline[-3][5] + self.kline[-4][5]) and (self.kline[-1][2] - self.kline[-2][2]) / \
                self.kline[-2][2] >= 0.04:
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
            })
            return True

    def method1(self, j=-10):
        '''
        技术面：
            布林线收窄+均线粘合
            布林线带宽指标<5%则表示窄，>30%则表示宽
            均线粘合指标<5%表示窄
        基本面：
            去除掉亏损股，市净率(股价/每股净资产)<10
        :return: 是否符合条件
        '''
        if self.kline[-1][0] != time.strftime("%Y-%m-%d", time.localtime()):
            print(self.code)
            return False
        [MB, UP, LB, PB, BW] = self.getBoll()
        MA = self.commonMA
        # WR = self.getWR(250)
        # print(BW)
        if BW <= 0.08 and self.kline[-1][2] >= UP:
            # if float(self.finance['jbmgsy']) > 0:
            x = (self.kline[-1][2] - self.kline[-1 + j][2]) / self.kline[-1 + j][2]
            count = 0
            for i in range(j, 0):
                if (self.kline[i][2] - self.kline[i - 1][2]) / self.kline[i - 1][2] > 0.098:
                    count += 1
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
                'score': round(x * 100, 2),
                'curScore': str(
                    round((self.kline[-1][2] - self.kline[-2][2]) / self.kline[-2][2] * 100, 2)) + '%',
                'count': count,
                'BW': BW
            })
            return True

    def method2(self):
        '''
        基本面：
            市净率小于2
            市盈率小于10
        :return: 是否符合条件
        '''
        # [MB, UP, LB, PB, BW] = self.getBoll()
        # MA = self.commonMA
        # WR = self.getWR(250)
        # if BW <= 0.05 and (MA[20] - MA[90]) / MA[60] <= 0.05:
        #     if self.kline[-1][2] >= UP:
        #         if float(self.finance['jbmgsy']) > 0:
        #             return True
        if 0 < self.kline[-1][2] / float(self.finance['mgjzc']) <= 2 and 0 < self.kline[-1][2] / float(
                self.finance['jbmgsy']) < 10:
            return True

    def method3(self):
        MA150 = self.getMA(150)
        score = 0
        for i in range(-150, 0):
            count = 0
            rate = [0.8, 1, 1.1, 1.3, 1.6, 2, 2.5]
            curScore = 0
            while self.kline[i][2] > self.kline[i - 1][2]:
                i += 1
                count += 1
                if count >= 4 and count <= 10:
                    curScore = count * (count * rate[count - 4])
            score += curScore
        if 400 > score > 140 and self.kline[-1][2] > MA150 and self.kline[-1][2] < 1.4 * MA150:
            return True
        # self.stockPool.append({
        #     'name': self.name,
        #     'code': self.code,
        #     'score': score
        # })

    # j是多少日前
    # 此函数用于每日复盘
    def method4(self, j=-10):
        if self.kline[-1][0] != time.strftime("%Y-%m-%d", time.localtime()):
            return False
        x = (self.kline[-1][2] - self.kline[-1 + j][2]) / self.kline[-1 + j][2]
        if x > 0.25:
            count = 0
            for i in range(j, 0):
                if (self.kline[i][2] - self.kline[i - 1][2]) / self.kline[i - 1][2] > 0.098:
                    count += 1
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
                'score': round(x * 100, 2),
                'curScore': str(round((self.kline[-1][2] - self.kline[-2][2]) / self.kline[-2][2] * 100, 2)) + '%',
                'count': count
            })
            return True

    # j是多少日前
    # 此函数用于每日复盘
    def flourish(self, j=-10):
        data = {
            'name': self.name + '(' + self.code + ')'
        }
        for k in range(-1, 0):
            if self.kline[k][0] > '2020-07-31':
                x = (self.kline[k][2] - self.kline[k + j][2]) / self.kline[k + j][2]
                if x > 0.25:
                    data[self.kline[k][0]] = str(round(x * 100, 2)) + '%'
        if len(data.keys()) > 1:
            self.stockPool.append(data)

    def method5(self):
        MA210 = self.getMA(210)
        MA35 = self.getMA(35)
        MA420 = self.getMA(420)
        sevenUp = False
        for i in range(-100, 0):
            count = 0
            while i < -1 and self.kline[i][2] > self.kline[i - 1][2]:
                i += 1
                count += 1
                if count >= 7:
                    sevenUp = True
            if sevenUp:
                break
        price5m = self.kline[-81][2]
        max15 = max(d[2] for d in self.kline[-16: -1])
        max250 = max(d[2] for d in self.kline[-251: -1])
        if MA210 > MA420 and MA35 < self.kline[-1][
            2] < MA35 * 1.2 and sevenUp and max250 * 1.15 > max15 > max250 * 0.95 and 0 < self.kline[-1][2] / float(
            self.finance['jbmgsy']) < 150 and price5m * 1.4 > self.kline[-1][2] > price5m * 1.15:
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
            })
            return True

    def method6(self):
        max300 = max(d[2] for d in self.kline[-350: -50])
        MA10 = self.getMA(10)
        MA35 = self.getMA(35)
        MA70 = self.getMA(70)
        MA140 = self.getMA(140)
        MA210 = self.getMA(210)
        MA30_70 = self.getMA(70, -30)
        MA30_140 = self.getMA(140, -30)
        score = 0
        for i in range(-150, 0):
            count = 0
            rate = [0.6, 0.4, 0.4, 0.6, 0.6, 0.4]
            curScore = 0
            while self.kline[i][2] > self.kline[i - 1][2]:
                i += 1
                count += 1
                if 9 >= count >= 4:
                    curScore += rate[count - 4]
            score += curScore
        if self.kline[-1][2] > max300 > self.kline[-2][2] and MA10 > MA35 > MA70 > MA140 > MA210 and (
                (MA140 - MA210) / MA210 < 0.02 or abs(MA70 - MA140) < abs(MA30_70 - MA30_140) * 0.7):
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
                'score': round(score, 2)
            })
            return True

    def method7(self, j=-10):
        # if self.kline[-1][0] != time.strftime("%Y-%m-%d", time.localtime()):
        #     return False
        if self.kline[-1][0] != '2020-08-07':
            return False
        x = (self.kline[-1][2] - self.kline[-1 + j][2]) / self.kline[-1 + j][2]
        if (self.kline[-1][2] - self.kline[-2][2]) / self.kline[-2][2] > 0.098 and (
                self.kline[-2][2] - self.kline[-3][2]) / self.kline[-3][2] > 0.098:
            count = 0
            for i in range(j, 0):
                if (self.kline[i][2] - self.kline[i - 1][2]) / self.kline[i - 1][2] > 0.098:
                    count += 1
            lianban = 0
            for i in range(-1, j - 1, -1):
                if (self.kline[i][2] - self.kline[i - 1][2]) / self.kline[i - 1][2] > 0.098:
                    lianban += 1
                else:
                    break
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
                'score': round(x * 100, 2),
                'curScore': str(round((self.kline[-1][2] - self.kline[-2][2]) / self.kline[-2][2] * 100, 2)) + '%',
                'count': count,
                'lianban': lianban
            })
            return True

    def method8(self, j=-10):
        if self.kline[-1][0] != time.strftime("%Y-%m-%d", time.localtime()):
            return False
        x = (self.kline[-1][2] - self.kline[-1 + j][2]) / self.kline[-1 + j][2]
        week1 = sum(d[5] for d in self.kline[-10:-5])
        week2 = sum(d[5] for d in self.kline[-5:-1])
        if week2 > week1 * 2:
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
                'score': round(x * 100, 2),
                'curScore': str(round((self.kline[-1][2] - self.kline[-2][2]) / self.kline[-2][2] * 100, 2)) + '%',
            })
            return True

    def method9(self):
        MA10 = self.getMA(10)
        MA20 = self.getMA(20)
        MA35 = self.getMA(35)
        MA70 = self.getMA(70)
        MA140 = self.getMA(140)
        MA210 = self.getMA(210)
        MA420 = self.getMA(420)
        MA35_20 = self.getMA(35, -20)
        k = 0
        if (MA35 - MA35_20) / MA35_20 >= 0.06:
            k = (MA35 - MA35_20) / MA35_20 * 5
        kaikou = abs((MA10 - MA20) / MA20) + abs((MA20 - MA35) / MA35) + abs((MA35 - MA70) / MA70) + abs(
            (MA70 - MA140) / MA140) + abs((MA140 - MA210) / MA210) - k
        s = abs((MA10 - MA20) / MA20)
        if (MA10 > MA20 > MA35 or MA20 > MA35 > MA70 or MA35 > MA70 > MA140) and MA140 > MA210 and self.kline[-1][
            2] > MA10 and (MA10 > MA20 * 0.99 and MA10 > MA35 and MA10 > MA70) and (
                MA210 - MA420) / MA420 >= 0.04 and kaikou <= 0.25 and (MA10 <= MA20 * 1.03 and MA10 >= MA20 * 0.99):
            self.stockPool.append({
                'name': self.name,
                'code': self.code,
                'score': round(kaikou, 2),
                's': s,
            })
            return True


class Speculator(object):

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.stockKlineBaseURL = 'http://50.push2his.eastmoney.com/api/qt/stock/kline/get?secid={0}&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=101&fqt=0&end=20500101&lmt=1000'
        self.shStockListURL = 'http://15.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10000&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:1+t:2,m:1+t:23'
        self.szStockListURL = 'http://15.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10000&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:13,m:0+t:80'
        self.stockFinanceBaseURL = 'http://f10.eastmoney.com/NewFinanceAnalysis/MainTargetAjax?type=0&code={0}'
        self.commonMAConfig = [0, 5, 10, 20, 30, 35, 60, 70, 90, 100, 120, 140, 150, 200, 210, 250, 400, 420]
        self.message = []
        self.stockPool = []
        self.process()

    def dealData(self, originData):
        '''
        对从股票接口获取的原始数据进行加工
        :param originData: 从股票接口获取的原始数据
        :return:
        '''
        name = originData['name']
        code = originData['code']
        klines = originData['klines']
        data = []
        for kline in klines:
            kline = kline.split(',')
            for i in range(1, len(kline)):
                if i == 5:
                    kline[i] = int(kline[i])
                else:
                    kline[i] = float(kline[i])
            data.append(kline)
        return {
            'name': name,
            'code': code,
            'kline': data
        }

    async def getData(self, url):
        '''
        抓取单只股票的数据
        :param url: 获取股票数据的接口，example:
        {
            rc: 0,
            rt: 17,
            svr: 181216787,
            lt: 1,
            full: 0,
            data: {
                code: "300465",
                market: 0,
                name: "高伟达",
                decimal: 2,
                dktotal: 1142,
                klines: ["2015-05-28,13.51,16.21,16.21,13.51,57,91451.00,23.98",...]
            }
        }
        :return: 只需要data部分
        '''
        futureKline = self.loop.run_in_executor(None, requests.get, url['kline'])
        futureFinance = self.loop.run_in_executor(None, requests.get, url['finance'])
        resKline = await futureKline
        resFinance = await futureFinance
        if resKline.status_code == 200 and resFinance.status_code == 200:
            try:
                klineData = json.loads(resKline.text)
                financeData = json.loads(resFinance.text)
                if klineData['data'] is not None:
                    print(klineData['data']['name'])
                    data = self.dealData(klineData['data'])
                    originData = {
                        'name': data['name'],
                        'code': data['code'],
                        'kline': data['kline'],
                        'finance': financeData[0]
                    }
                    if len(originData['kline']) > 421:
                        stockSelector = StockSelector(originData, self.commonMAConfig, self.stockPool)
                        stockSelector.method05()
                        # self.message.append('买 {0} {1}'.format(stockSelector.name, stockSelector.code))
            except:
                print(url)

    def getAllStockCodes(self):
        '''
        获取所有股票代码
        :return: {'sh': 上交所股票代码列表, 'sz': 深交所股票代码列表}
        '''
        sh = []
        sz = []
        shRes = requests.get(self.shStockListURL)
        szRes = requests.get(self.szStockListURL)
        if shRes.status_code == 200 and szRes.status_code == 200:
            try:
                shStockListData = json.loads(shRes.text)
                szStockListData = json.loads(szRes.text)
                if shStockListData['data']['diff'] is not None:
                    for stockCode in shStockListData['data']['diff']:
                        sh.append(stockCode['f12'])
                if szStockListData['data']['diff'] is not None:
                    for stockCode in szStockListData['data']['diff']:
                        sz.append(stockCode['f12'])
                sh = set(sh)
                sz = set(sz)
            except:
                print('股票列表读取失败')
        # # 读取退市股名单
        # with open("tuishi.txt", "r") as f:
        #     ts = set(f.readlines())  # 读取全部内容 ，并以列表方式返回
        # # 读取上交所股票名单
        # with open("sh.txt", "r") as f:
        #     stockCodes = set(f.readlines())  # 读取全部内容 ，并以列表方式返回
        #     for stockCode in stockCodes:
        #         if stockCode.startswith('60') or stockCode.startswith('30') or stockCode.startswith('00'):
        #             if stockCode not in ts:
        #                 sh.append(stockCode.strip())
        # # 读取深交所股票名单
        # with open("sz.txt", "r") as f:
        #     stockCodes = set(f.readlines())  # 读取全部内容 ，并以列表方式返回
        #     for stockCode in stockCodes:
        #         if stockCode.startswith('60') or stockCode.startswith('30') or stockCode.startswith('00'):
        #             if stockCode not in ts:
        #                 sz.append(stockCode.strip())
        return {
            'sh': sh,
            'sz': sz
        }

    def process(self):
        stockCodes = self.getAllStockCodes()
        # stockCodes = {'sz': ['002878'], 'sh': []}
        urls = []
        for stockCode in stockCodes['sh']:
            urls.append({'kline': self.stockKlineBaseURL.format('1.' + stockCode),
                         'finance': self.stockFinanceBaseURL.format('SH' + stockCode)})
        for stockCode in stockCodes['sz']:
            urls.append({'kline': self.stockKlineBaseURL.format('0.' + stockCode),
                         'finance': self.stockFinanceBaseURL.format('SZ' + stockCode)})
        tasks = [asyncio.ensure_future(self.getData(url)) for url in urls]
        self.loop.run_until_complete(asyncio.wait(tasks))
        self.loop.close()
        # self.stockPool.sort(key=lambda x: x['score'], reverse=False)
        # self.stockPool = self.stockPool[:50]
        # self.stockPool.sort(key=lambda x: x['s'], reverse=False)
        # res = self.split(self.stockPool)
        # ms = []
        # ms.append(self.printFormat(res[0]))
        # ms.append(self.printFormat(res[1]))
        notifyService = NotifyService(self.printFormat(self.stockPool))
        notifyService.sendMessageToWeiXin()
        # print(ms)
        print(self.stockPool)
        # self.jsonDumpToFile('stock.json', self.stockPool)

    def split(self, stockPool):
        res1 = []
        res2 = []
        for i in range(len(stockPool)):
            if stockPool[i]['method'] == 1:
                res1.append(stockPool[i])
            else:
                res2.append(stockPool[i])
        return [res1, res2]

    def split1(self, stockPool, point=3):
        index = 0
        for i in range(len(stockPool)):
            if stockPool[i]['lianban'] < 3:
                index = i
                break
        return [stockPool[0:index], stockPool[index:]]

    # def printFormat(self, arr):
    #     return '\n'.join(
    #         map(lambda x: x['name'] + '(' + x['code'] + ') 得分：' + str(x['score']),
    #             arr)) + '\nsum:{0}'.format(len(arr))

    def printFormat(self, arr):
        return '\n'.join(
            map(lambda x: x['name'] + '(' + x['code'] + ')',
                arr)) + '\nsum:{0}'.format(len(arr))

    def jsonDumpToFile(self, fileName, jsonData):
        with open(fileName, mode='w', encoding='utf-8') as f:
            json.dump(jsonData, f)


class NotifyService(object):
    def __init__(self, message):
        self.message = message

    def sendMessageToWeiXin(self):
        data = {
            "appToken": "AT_U950xOUDtPQmzFNzOLwI99TaDGPvS7rp",
            "content": self.message,
            "contentType": 1,  # 内容类型 1表示文字  2表示html(只发送body标签内部的数据即可，不包括body标签) 3表示markdown
            "topicIds": [  # 发送目标的topicId，是一个数组！！！
                123
            ],
            "uids": [  # 发送目标的UID，是一个数组！！！
                "UID_Hoe5dkX9dnPXf9QyYj51cTGu3suh",
                "UID_QcQLiLQZSxxjKPbM80wTqXOMJkJP",
                "UID_Lzi5IAljUc45Rq27M6zNKdAb9unm",  # 刘春桃
                # "UID_3FScq4H1FgG92RaoRT5Fx5VrnV5p",
                # "UID_S69EAHJVgFPxpUqgzCpGaUHZBnwj",
                # "UID_lSXk2aqmLsHaQoWxTyosPyVegBTZ",
                # "UID_ceA46CD7UBTr1oRqGN7Gd9evieur"
            ]
        }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        requests.post('http://wxpusher.zjiecode.com/api/send/message', data=json.dumps(data), headers=headers)


Speculator()
