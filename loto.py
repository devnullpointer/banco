# -*- coding: utf-8 -*-

import os, sys, re, urllib, urlparse, json, base64, datetime, math, array, itertools, calendar
from dateutil.relativedelta import relativedelta

import client

now = datetime.datetime.utcnow()

class Ref:
    BANCO = 'https://loteries.lotoquebec.com/fr/loteries/banco?annee=%s&widget=resultats-anterieurs&noProduit=208#res'
    BANCO_CUR = 'https://loteries.lotoquebec.com/fr/loteries/banco?date=%s'
    DATAFILE = 'banco.json'


class Logger:
    def log(self, message, header=False):
        if header:
            print '--------------------------------------------------------'
            print '  Banco Draw Generator :: %s' % message
            print '--------------------------------------------------------'
        else:
            print 'Loto Banco: %s' % message


class Banco:
    def __init__(self):
        self.data = []
        self.dow = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        lastYear = (datetime.date.today() - relativedelta(years=1)).year
        self.freq = {1: 'This Month', 2: 'Last 3 Months', 3: 'This Year', 4: 'Last Year (%s)' % lastYear, 5: 'All Time'}
        self.full = {8: 'This Week', 9: 'This Month', 10: 'Last 3 Months', 11: 'Between 2 Dates'}
        self.logger = Logger()


    def loadBancoDataFromLQ(self):
        try:
            self.logger.log('Loading data from 1989...')
            for year in range(1989, now.year):
                url = Ref.BANCO % year
                result = client.request(url)
                
                result = client.parseDOM(result, 'tr')
                for entry in result:
                    drawdate = client.parseDOM(entry, 'td', attrs={'class': 'date'})[0]
                    numeros = client.parseDOM(entry, 'div', attrs={'class': 'numerosGangnants principal'})
                    numeros = client.parseDOM(numeros, 'span')
                    
                    self.data.append({'draw': drawdate, 'numbers': numeros})
        
        except:
            self.logger.log('Exception. Historical data not loaded.')


    def loadMissingDraws(self):
        self.logger.log('Loading missing results...', header=True)
        today = datetime.date.today()
        curr = today - relativedelta(years=1)

        try:
            while (curr != today):
                if not self.checkForData(curr.strftime('%Y-%m-%d')):
                    self.logger.log('Loading draw data for %s' % curr)
                    url = Ref.BANCO_CUR % curr
                    result = client.request(url)
                    result = client.parseDOM(result, 'div', attrs={'class': 'lqZoneProduit principal banco'})
                    numeros = client.parseDOM(result, 'span', attrs={'class': 'num'})
                    self.data.append({'draw': curr.strftime('%Y-%m-%d'), 'numbers': numeros})

                curr = curr + relativedelta(days=1)
        except:
            self.logger.log('ooops')
        
        # write draw data to file
        with open(Ref.DATAFILE, 'w') as outfile:
            json.dump(self.data, outfile)
        
        self.logger.log('%d Available Draws' % len(self.data), header=True)


    def checkForData(self, drawDate):
        drawFlag = False
        for d in self.data:
            if d['draw'] == drawDate:
                drawFlag = True
                break

        return drawFlag

    def showMenu(self):
        print ''
        print ''
        print '1:  Monday'
        print '2:  Tuesday'
        print '3:  Wednesday'
        print '4:  Thursday'
        print '5:  Friday'
        print '6:  Saturday'
        print '7:  Sunday'
        print '8:  Last 7 days'
        print '9:  This Month'
        print '10: Last 3 Months'
        print '11: Between Dates'
        print ''
        print '0: Exit'


    def chooseFrequency(self):
        print ''
        print ''
        print '1: This Month'
        print '2: Last 3 Months'
        print '3: This Year'
        print '4: Last Year (%s)' % (datetime.date.today() - relativedelta(years=1)).year
        print '5: All Time'
        print ''
        print '0: Return'

    def processRequests(self):
        self.loadMissingDraws()
        
        while True:
            self.showMenu()
            nb = raw_input('Select a Draw Day: ')

            try:
                if (int(nb) == 0):
                    break
                elif (int(nb) > 0 and int(nb) < 8):
                    self.chooseFrequency()
                    fr = raw_input('Select Draw Frequency: ')
                    if (int(fr) == 0):
                        raise ValueError('Return To Previous Menu')
                    self.generateStats(int(nb), int(fr))
                else:
                    self.generateStats(int(nb))
            except ValueError: pass


    def generateStats(self, option, freq=0):
        today = datetime.date.today()
        stats = {}
        startDate = None
        endDate = None
        
        for i in range(1, 71):
            stats[i] = 0

        if (option < 8):
            option = option - 1

            if freq == 1:
                _, num_days = calendar.monthrange(today.year, today.month)
                startDate = datetime.date(today.year, today.month, 1)
                endDate = datetime.date(today.year, today.month, num_days)
            elif freq == 2:
                endDate = today
                startDate = today - relativedelta(months=3)
            elif freq == 3:
                startDate = datetime.date(today.year, 1, 1)
                endDate = today
            elif freq == 4:
                startDate = datetime.date(today.year - 1, 1, 1)
                endDate = datetime.date(today.year - 1, 12, 31)

            for entry in self.data:
                currDate = datetime.datetime.strptime(entry['draw'], '%Y-%m-%d').date()
                if startDate is not None and endDate is not None:
                    if startDate < currDate < endDate:
                        if (currDate.weekday() == option):
                            numeros = entry['numbers']
                            for i in numeros:
                                stats[int(i)] += 1
                else:
                    if (currDate.weekday() == option):
                        numeros = entry['numbers']
                        for i in numeros:
                            stats[int(i)] += 1

            self.logger.log('%s Banco Most Drawn Numbers ' % self.dow[option] if freq == 0 else self.freq[freq])

        else:
            if (option == 8):
                endDate = today
                startDate = today - relativedelta(days=7)

            elif (option == 9):
                endDate = today
                startDate = today - relativedelta(months=1)

            elif (option == 10):
                endDate = today
                startDate = today - relativedelta(months=3)
            
            elif (option == 11):
                startDate = raw_input('Enter Start Date (YYYY-MM-DD): ')
                startDate = datetime.datetime.strptime(startDate, '%Y-%m-%d').date()
                
                endDate = raw_input('Enter End Date (YYYY-MM-DD): ')
                endDate = datetime.datetime.strptime(endDate, '%Y-%m-%d').date()
            

            for entry in self.data:
                currDate = datetime.datetime.strptime(entry['draw'], '%Y-%m-%d').date()
                if startDate < currDate < endDate:
                    numeros = entry['numbers']
                    for i in numeros:
                        stats[int(i)] += 1
                            
            self.logger.log('Banco Most Drawn Numbers %s' % self.full[option])

        self.logger.log(stats)
        numList = sorted(stats, key=stats.__getitem__, reverse=True)
        self.logger.log('Top 10 Drawn Numbers: %s' % numList[:10])
        self.logger.log('Bottom 10 Drawn Numbers: %s' % numList[-10:])

        self.permutations(numList)


    def readDataFile(self):
        # Load data from JSON file
        with open(Ref.DATAFILE) as dataFile:
            self.data = json.load(dataFile)

    def permutations(self, numList):
        while True:
            print ''
            print 'Do you want combinations on:'
            print ''
            print '1: Stats Generated List on Top 10'
            print '2: Stats Generated List on Bottom 10'
            print '3: Manual List'
            print ''
            perm = raw_input('Choose: ')

            if int(perm) in [1, 2]:
                print ''
                while True:
                    mise = raw_input('Entry your bet (2, 3, 4, 5, 6, 7, 8, 9, or 10): ')
                    if 1 < int(mise) < 11:
                        break
                self.logger.log('Showing Bet %s Combinations on top 6 played numbers.' % int(mise))
                if (int(perm) == 1):
                    combo = list(itertools.combinations(numList[:10], int(mise)))
                elif (int(perm) == 2):
                    combo = list(itertools.combinations(numList[-10:], int(mise)))
                self.logger.log('%s Combos: %s' % (len(combo), combo))
                break
            elif int(perm) == 3:
                manual = raw_input('Please enter your numbers seperated by <space>: ')
                manual = manual.split()
                manual = [int(x) for x in manual]

                while True:
                    mise = raw_input('Entry your bet (2, 3, 4, 5, 6, 7, 8, 9, or 10): ')
                    if (1 < int(mise) < 11) and mise >= len(manual):
                        break
                self.logger.log('Showing Bet %s Combinations on %s entered numbers.' % (int(mise), len(manual)))
                combo = list(itertools.combinations(manual, int(mise)))
                self.logger.log('%s Combos: %s' % (len(combo), combo))
                break
            else:
                print 'Please select either 1, 2 or 3.'


banco = Banco()

if (os.path.isfile(Ref.DATAFILE)):
    banco.readDataFile()
    banco.processRequests()
else:
    banco.loadBancoDataFromLQ()
    banco.processRequests()


