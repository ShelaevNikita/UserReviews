#!/usr/bin/env python3

import requests
import threading
import logging

from typing   import Dict, List, Tuple, Union, Any
from random   import random
from time     import sleep
from datetime import datetime as dt
from bs4      import BeautifulSoup as bs
from pymongo  import MongoClient

from dataClass.ReviewDataClass import Review, ReviewForFilm

# Класс для скачивания данных с помощью Web-Scrapping
#   о пользовательских отзывах к различным фильмам / сериалам с сервиса "КиноПоиск"
class ReviewMining(object):
    
    # Proxy-сервера для обхода блокировки сайта
    Proxies = {
        'http'  : 'http://10.10.1.10:3128',
        'https' : 'http://10.10.1.10:1080'
    }

    # URL-адрес сервиса "КиноПоиск"
    KinopoiskURL = 'https://www.kinopoisk.ru/film/'
    
    # Используемые заголовки HTTPS-запроса
    URLHeaders   = {
        'User-Agent' : 'Chrome/120.0.0.0 YaBrowser/24.1.0.0',
        'Referer'    : 'https://sso.kinopoisk.ru/'
    }
    
    # Словарь для преобразования названия месяца в его порядковый номер
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

    # Инициализация класса
    def __init__(self, configParameters: Dict[str, Union[int, str]],
                 mongoClient: MongoClient, reviewFilmPage: Dict[int, List[int]]):
        
        self.databaseName    = configParameters['databaseName']
        self.dataPathReviews = configParameters['dataPathReviews']
        self.threads         = configParameters['threads']
        self.sleepTime       = configParameters['sleepTime']
    
        self.collection      = mongoClient[self.databaseName][self.dataPathReviews]

        self.reviewFilmPage  = reviewFilmPage
        
        self.lock = threading.Lock()
        
        logging.basicConfig(
            filename = '../log/dataMining.log',
            format   = '%(asctime)s | %(levelname)s: %(message)s',
            filemode = 'w+'
        )       
        self.logger = logging.getLogger()
    
    # Преобразование строки с временем пользовательского отзыва в нужный формат
    def reviewDateAndTime(self, textDate: str) -> str:    
        monthKey       = textDate.split(' ')[1]     
        dateAndTimeStr = textDate.replace(monthKey, self.Month[monthKey])        
        dateAndTimeDt  = dt.strptime(dateAndTimeStr, '%d %m %Y | %H:%M')
        return dateAndTimeDt.strftime('%H:%M|%d.%m.%Y')

    # Получение нового пользовательского отзыва
    def createNewReview(self, pageElem: Any) -> Review:
        reviewTitleInit       = pageElem.find('p', class_ = 'sub_title').text.replace(u'\xa0', ' ')
        reviewTextInit        = pageElem.find('span', itemprop = 'reviewBody').text

        newReview             = Review()
        newReview.author      = pageElem.find('a', itemprop = 'name').text
        newReview.title       = reviewTitleInit if (len(reviewTitleInit) > 0) else '?'
        newReview.dateAndTime = self.reviewDateAndTime(pageElem.find('span', class_ = 'date').text)
        newReview.reviewText  = reviewTextInit.encode('utf-8', errors = 'replace').decode('utf-8').replace('\r', '')
        
        reviewClass = pageElem['class'][1]
        if   reviewClass == 'neutral':
            newReview.reviewClass = 1
         
        elif reviewClass == 'bad':
            newReview.reviewClass = 2

        return newReview

    # Скачивание всех пользовательских отзывов со страницы сайта
    def reviewParsingForPage(self, pageReviews: bs) -> List[Review]:
        reviewInPageArray = []
        for elem in pageReviews.findAll('div', itemprop = 'reviews'):
            reviewInPageArray.append(self.createNewReview(elem))            

        return reviewInPageArray

    # Заполнение общих полей в классе ReviewForFilm
    def getCommonReviewInfo(self, filmID: int) -> Tuple[ReviewForFilm, List[int]]:
        try:
            response = requests.get(self.KinopoiskURL + f'{filmID}/reviews',
                                    headers = self.URLHeaders)
                
        except requests.ConnectionError:
            with self.lock:
                self.logger.error(f'{filmID} -> Connection is broken! | review')
            
            return [ReviewForFilm(), []]
            
        if response.status_code != 200:
            return [ReviewForFilm(), []]
            
        pageKinopoisk   = bs(response.content, features = 'html.parser')
        reviewCountFind = pageKinopoisk.find('li', class_ = 'all')
            
        if reviewCountFind is None:                
            with self.lock:
                self.logger.warning(f'{filmID} -> Not found JSON on the site! | review')

            return [ReviewForFilm(), []]

        reviewCountMax = int(reviewCountFind.find('b').text)

        newReviewForFilm               = ReviewForFilm()
        newReviewForFilm._id           = filmID
        newReviewForFilm.reviewMax     = reviewCountMax
        
        newReviewForFilm.countGood     =   int(pageKinopoisk.find('li', class_ = 'pos').find('b').text)
        newReviewForFilm.countNeutral  =   int(pageKinopoisk.find('li', class_ = 'neg').find('b').text)
        newReviewForFilm.countNegative =   int(pageKinopoisk.find('li', class_ = 'neut').find('b').text)
        newReviewForFilm.reviewPercent = float(pageKinopoisk.find('li', class_ = 'perc').find('b').text[:-1])
        
        return [newReviewForFilm, list(range(1, (reviewCountMax + 99) // 100 + 1))]

    # Добавление новой записи в MongoDB
    def reviewToMongoDB(self, review: ReviewForFilm, flagCreate: bool):
        reviewToDict = review.toDict()
        with self.lock:
            if flagCreate:
                self.collection.insert_one(reviewToDict)
                
            else:               
                self.collection.update_one({ '_id'  : reviewToDict['_id'] },
                                           { '$set' : { 'pages'  : reviewToDict['pages'],
                                                       'reviews' : reviewToDict['reviews'] }})                
            print(' Review:', reviewToDict['_id'])           
        return

    # Скачивание необходимых данных с сервиса "КиноПоиск"
    def urlReviewParsing(self, reviewFilmPage: List[Tuple[int, List[int]]]):
        for (filmID, pages) in reviewFilmPage:
            if filmID != reviewFilmPage[0][0]:
                sleep((1 + random()) * self.sleepTime)
                
            listPages  = pages
            flagCreate = True
            if len(pages) == 0:
                newReviewForFilm, listPages = self.getCommonReviewInfo(filmID)
                
            else:
                flagCreate = False
                with self.lock:
                    newReviewForFilm = ReviewForFilm(**self.collection.find_one({ '_id' : filmID }))
                    
            for page in listPages:
                if page != listPages[0]:
                    sleep((1 + random()) * self.sleepTime)
                    
                try:
                    response = requests.get(self.KinopoiskURL + 
                                            f'{filmID}/reviews/ord/date/status/all/' + 
                                            f'perpage/200/page/{page}/',
                                            headers = self.URLHeaders)
                
                except requests.ConnectionError:
                    with self.lock:
                        self.logger.error(f'{filmID} -> Connection is broken! | review')
                    
                    return
            
                if response.status_code != 200:
                    continue

                pageReviews   = bs(response.content, features = 'html.parser')               
                reviewsInPage = self.reviewParsingForPage(pageReviews)
                if len(reviewsInPage) == 0:  
                    with self.lock:
                        self.logger.warning(f'{filmID} -> Not found JSON on the page {page}! | review')
                        
                    continue

                newReviewForFilm.pages.append(page)
                newReviewForFilm.reviews += reviewsInPage
                
            self.reviewToMongoDB(newReviewForFilm, flagCreate)

        return
    
    # Главная функция класса, запускающая несколько параллельных потоков на скачивание данных
    def main(self):
        print('\t The data about reviews is downloading...')
        self.logger.debug('The data about reviews is downloading...')

        threadReviewArray = []
        reviewFilmPageArr = list(self.reviewFilmPage.items())
        reviewFilmPageThr = [reviewFilmPageArr[i::self.threads] for i in range(self.threads)]

        for i in range(self.threads):
            thr = threading.Thread(target = self.urlReviewParsing, args = (reviewFilmPageThr[i],))
            threadReviewArray.append(thr)
            thr.start()
        
        for thr in threadReviewArray:
            thr.join()
        
        print('\t The data about reviews was downloaded successfully!')
        self.logger.debug('The data about reviews was downloaded successfully!')
        return

if __name__ == '__main__':
    
    defaultConfigParameters = {
        'databaseName'    : 'userReviews',
        'dataPathReviews' : 'reviews',
        'threads'         : 4,
        'sleepTime'       : 30
    }

    mongoClient = MongoClient('mongodb://localhost:27017/')
    IDArray     = {435:[], 258687:[], 326:[], 448:[], 535341:[], 
                   404900:[], 89540:[], 464963:[], 79848:[], 253245:[]}
    
    ReviewMining(defaultConfigParameters, mongoClient, IDArray).main()