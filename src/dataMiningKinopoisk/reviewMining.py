#!/usr/bin/env python3

import requests
import json
import threading

from random import random
from time import sleep
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

    def __init__(self, dataPathFilms, dataPathReviews, threads, reviewInPage):
        self.dataPathFilms   = dataPathFilms
        self.dataPathReviews = dataPathReviews
        self.reviewInPage    = reviewInPage
        self.threads         = threads
    
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

    def reviewParsingForPage(self, pageReviews):
        
        reviewInPageArray = []

        for elem in pageReviews.findAll('div', itemprop = 'reviews'):
                    
            review = {
                'author'     : elem.find('a', itemprop = 'name').text, 
                'class'      : elem['class'][1].capitalize(),
                'title'      : elem.find('p', class_ = 'sub_title').text.replace(u'\xa0', ' '), 
                'reviewText' : elem.find('span', itemprop = 'reviewBody').text.replace('\n\r\n', ' ')
            }
            
            reviewInPageArray.append(review)            

        return reviewInPageArray

    def urlReviewParsing(self, IDArray):
        
        for ID in IDArray:
            
            sleep(7.5 + random() * 10.0)

            try:
                response = requests.get(self.KinopoiskURL + f'{ID}/reviews',
                                        headers = self.URLHeaders)
                
            except requests.ConnectionError:
                print('\n Error: Connection is broken!...')
                break
            
            if response.status_code != 200:
                continue
            
            pageKinopoisk   = bs(response.content, features = 'html.parser')
            reviewCountFind = pageKinopoisk.find('li', class_ = 'all').find('b')

            if reviewCountFind is None:
                print('\n Warning: Not fount count of reviews on the site...')
                with self.lock:
                    self.reviewMissing.append(f'{ID}|0')
                continue

            reviewCountFilm = int(reviewCountFind.text)
            reviewsForFilm  = []

            for page in range(1, 2):

            #for page in range(1, reviewCountFilm // self.reviewInPage + 1):

                sleep(7.5 + random() * 10.0)
            
                try:
                    response = requests.get(self.KinopoiskURL + 
                                            f'{ID}/reviews/ord/date/status/all/' + 
                                            f'perpage/{self.reviewInPage}/page/{page}/',
                                            headers = self.URLHeaders)
                
                except requests.ConnectionError:
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
                    'reviewForFilm' : reviewCountForFilm,
                    'reviews'       : reviewsForFilm
                })

            with self.lock:
                self.reviewCount += reviewCountForFilm

        return
    
    def main(self):

        print(f'\n\t The data is downloading to the file \"{self.dataPathReviews}\"...')

        parts = self.threads
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
        
        print('\n\t The data was downloaded successfully!\n')

        return

if __name__ == '__main__':
    
    dataPathFilms   = '../../data/movies.json'
    dataPathReviews = '../../data/reviews.json'
    threads         = 4
    reviewInPage    = 10

    ReviewMining(dataPathFilms, dataPathReviews, threads, reviewInPage).main()