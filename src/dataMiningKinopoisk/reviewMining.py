#!/usr/bin/env python3

import requests
import json
import threading

from time import sleep
from bs4 import BeautifulSoup as bs

class ReviewMining(object):
    
    Proxies = {'http' :'http://10.10.1.10:3128',
               'https':'http://10.10.1.10:1080'}

    KinopoiskURL = 'https://www.kinopoisk.ru/film/'

    def __init__(self, dataPathFilms, dataPathReviews, threads):
        self.dataPathFilms   = dataPathFilms
        self.dataPathReviews = dataPathReviews
        self.threads         = threads
    
        self.lock = threading.Lock() 

    def getIDFilms(self):
        with open(self.dataPathFilms, 'r', encoding = 'utf-8') as file:
            resultJSON = json.loads(file.read(), strict = False)
            
        IDArray = []
        for film in resultJSON:
            IDArray.append(film['ID'])
            
        return IDArray

    def urlReviewParsing(self, IDArray):
        for ID in IDArray:
            
            sleep(5.0)

            try:
                response = requests.get(self.KinopoiskURL + f'{ID}/reviews/ord/date/status/all/perpage/50/page/1/',
                                        headers = {'User-Agent':'YaBrowser/24.1.3.809'})
                
            except requests.ConnectionError:
                print('\n\t Error: Connection is broken!...')
                break
            
            if response.status_code != 200:
                continue
            
            pageKinopoisk   = bs(response.content, features = 'html.parser')
            reviewCountFind = pageKinopoisk.find('li', class_ = 'all').find('b')                    
            reviewCount     = int(reviewCountFind.text)
            
            reviewPages = reviewCount // 50 + 1

            for page in reviewPages:

                sleep(5.0)
            
                try:
                    pageReviews = requests.get(self.KinopoiskURL + f'{ID}/reviews/ord/date/status/all/perpage/50/page/{page}/',
                                            headers = {'User-Agent':'YaBrowser/24.1.3.809'})
                
                except requests.ConnectionError:
                    print('\n\t Error: Connection is broken!...')
                    break
            
                if pageReviews.status_code != 200:
                    continue

                for elem in pageReviews.findAll('div', itemprop = 'reviews'):
                    
                    reviewClass  = elem['class'].text.split()[1].capitalize()                   
                    reviewAuthor = elem.find('a', itemprop = 'name').text
                    reviewTitle  = elem.find('p', class_ = 'sub_title').text
                    reviewText   = elem.find('table').find('span', itemprop = 'reviewBody').text
                    
                    review = {
                        'filmID'     : ID, 
                        'author'     : reviewAuthor, 
                        'class'      : reviewClass,
                        'title'      : reviewTitle, 
                        'reviewText' : reviewText
                    }
            
                    with self.lock:
                        with open(self.dataPathReviews, 'w', encoding = 'utf-8') as file:
                            json.dump(review, file, indent = 4, ensure_ascii = False, separators = (',', ': '))

        return
    
    def main(self):

        print(f'\n\t The data is downloading to the file \"{self.dataPath}\"...')

        parts = self.threads
        threadReviewArray = []
        
        IDArrays = [self.getIDFilms()[i::parts] for i in range(parts)]

        for i in range(parts):
            thr = threading.Thread(target = self.urlReviewParsing, args = (IDArrays[i],))
            threadReviewArray.append(thr)
            thr.start()
        
        for thr in threadReviewArray:
            thr.join()
        
        print('\n\t The data was downloaded successfully!')

        return

if __name__ == '__main__':
    
    dataPathFilms   = '../../data/films.json'
    dataPathReviews = '../../data/reviews.json'
    threads         = 4

    ReviewMining(dataPathFilms, dataPathReviews, threads).main()