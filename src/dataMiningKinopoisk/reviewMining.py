#!/usr/bin/env python3

import requests
import json
import threading

from random import random
from time import sleep
from datetime import datetime as dt
from bs4 import BeautifulSoup as bs

class ReviewMining(object):
    
    Proxies = {
        'http'  : 'http://10.10.1.10:3128',
        'https' : 'http://10.10.1.10:1080'
    }

    KinopoiskURL = 'https://www.kinopoisk.ru/film/'
    
    URLHeaders   = {
        'User-Agent' : 'Chrome/120.0.0.0 YaBrowser/24.1.0.0',
        'Referer'    : 'https://sso.kinopoisk.ru/'
    }
    
    Month = {
        'января'   : '01',
        'февраля'  : '02',
        'марта'    : '03',
        'апреля'   : '04',
        'мая'      : '05',
        'июня'     : '06',
        'июля'     : '07',
        'августа'  : '08',
        'сентября' : '09',
        'октября'  : '10',
        'ноября'   : '11',
        'декабря'  : '12'
    }

    def __init__(self, configParameters):      
        self.dataPathFilms   = configParameters['dataPathFilms']
        self.dataPathReviews = configParameters['dataPathReviews']
        self.threads         = configParameters['threads']
        self.reviewInPage    = min(100, configParameters['reviewInPage'])
        self.sleepTime       = configParameters['sleepTime']
    
        self.lock = threading.Lock()
        
        self.reviewCount     = 0
        self.reviewMissing   = []
        self.reviewJSONArray = []

    def getIDFilms(self):       
        IDArray = []        
        try:
            with open(self.dataPathFilms, 'r', encoding = 'utf-8') as file:
                resultJSON = json.loads(file.read(), strict = False)
                
        except FileNotFoundError:
            print(f'\n Error: Not found file \"{self.dataPathFilms}\"!')
            return IDArray           
        
        for film in resultJSON['filmArray']:
            IDArray.append(film['ID'])
            
        return IDArray

    def reviewDateAndTime(self, textDate):    
        monthKey       = textDate.split(' ')[1]     
        dateAndTimeStr = textDate.replace(monthKey, self.Month[monthKey])        
        dateAndTimeDt  = dt.strptime(dateAndTimeStr, '%d %m %Y | %H:%M')
        return dateAndTimeDt.strftime('%H:%M|%d.%m.%Y')

    def reviewParsingForPage(self, pageReviews):     
        reviewInPageArray = []
        for elem in pageReviews.findAll('div', itemprop = 'reviews'):
                    
            review = {
                'author'      : elem.find('a', itemprop = 'name').text, 
                'class'       : elem['class'][1].capitalize(),
                'title'       : elem.find('p', class_ = 'sub_title').text.replace(u'\xa0', ' '),
                'dateAndTime' : self.reviewDateAndTime(elem.find('span', class_ = 'date').text),
                'reviewText'  : elem.find('span', itemprop = 'reviewBody').text.replace('\r', ' ').replace('\n', ' ')
            }
            
            reviewInPageArray.append(review)            

        return reviewInPageArray

    def userReviewClass(self, pageContent, reviewClass):        
        return int(pageContent.find('li', class_ = reviewClass).find('b').text)

    def urlReviewParsing(self, IDArray):      
        firstID = IDArray[0]
        for ID in IDArray:          
            if (ID != firstID):
                sleep(self.sleepTime + random() * self.sleepTime)

            try:
                response = requests.get(self.KinopoiskURL + f'{ID}/reviews',
                                        headers = self.URLHeaders)
                
            except requests.ConnectionError:
                with self.lock:
                    print('\n Error: Connection is broken!...')
                break
            
            if response.status_code != 200:
                continue
            
            pageKinopoisk   = bs(response.content, features = 'html.parser')
            reviewCountFind = pageKinopoisk.find('li', class_ = 'all')
            
            if reviewCountFind is None:                
                with self.lock:
                    print(' Warning: Not fount user reviews for this film...')
                    self.reviewMissing.append(f'{ID}|0')
                continue

            reviewCountFilm = int(reviewCountFind.find('b').text)
            
            reviewCountPos  = self.userReviewClass(pageKinopoisk, 'pos')
            reviewCountNeg  = self.userReviewClass(pageKinopoisk, 'neg')
            reviewCountNeut = self.userReviewClass(pageKinopoisk, 'neut')
            
            reviewPosAndNeg = float(pageKinopoisk.find('li', class_ = 'perc').find('b').text[:-1])
            
            reviewsForFilm  = []

            for page in range(1, reviewCountFilm // self.reviewInPage + 2):
                sleep(self.sleepTime + random() * self.sleepTime)           
                try:
                    response = requests.get(self.KinopoiskURL + 
                                            f'{ID}/reviews/ord/date/status/all/' + 
                                            f'perpage/{self.reviewInPage}/page/{page}/',
                                            headers = self.URLHeaders)
                
                except requests.ConnectionError:
                    with self.lock:
                        print('\n Error: Connection is broken!...')
                    break
            
                if response.status_code != 200:
                    continue

                pageReviews = bs(response.content, features = 'html.parser')

                reviewsInPage = self.reviewParsingForPage(pageReviews)
                
                if len(reviewsInPage) == 0:  
                    with self.lock:
                        self.reviewMissing.append(f'{ID}|{page}')
                        
                reviewsForFilm += reviewsInPage
            
            reviewCountForFilm = len(reviewsForFilm)

            with self.lock:
                self.reviewJSONArray.append({
                    'filmID'        : ID,
                    'reviewMax'     : reviewCountFilm,
                    'reviewPercent' : reviewPosAndNeg,
                    'reviewClass'   : (reviewCountPos, reviewCountNeg, reviewCountNeut),
                    'reviewForFilm' : reviewCountForFilm,
                    'reviews'       : reviewsForFilm
                })

            with self.lock:
                self.reviewCount += reviewCountForFilm

        return
    
    def main(self):
        print(f'\n\t The data about reviews is downloading to the file \"{self.dataPathReviews}\"...\n')
        parts             = self.threads
        threadReviewArray = []
        
        IDArrays = [self.getIDFilms()[i::parts] for i in range(parts)]

        for i in range(parts):
            thr = threading.Thread(target = self.urlReviewParsing, args = (IDArrays[i],))
            threadReviewArray.append(thr)
            thr.start()
        
        for thr in threadReviewArray:
            thr.join()
        
        allReviewJSON = {
            'reviewCount'   : self.reviewCount,
            'reviewMissing' : self.reviewMissing,
            'reviewArray'   : self.reviewJSONArray
        }

        with open(self.dataPathReviews, 'w', encoding = 'utf-8') as file:
            json.dump(allReviewJSON, file, indent = 4,
                      ensure_ascii = False, separators = (',', ': '))
        
        print('\n\t The data about reviews was downloaded successfully!\n')

        return

if __name__ == '__main__':
    
    defaultConfigParameters = {
        'dataPathFilms'   : '../../data/movies.json',
        'dataPathReviews' : '../../data/reviews.json',
        'threads'         : 4,
        'reviewInPage'    : 100,
        'sleepTime'       : 30
    }
    
    ReviewMining(defaultConfigParameters).main()