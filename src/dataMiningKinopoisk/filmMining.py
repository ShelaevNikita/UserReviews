#!/usr/bin/env python3

import requests
import json
import threading

from time import sleep
from bs4 import BeautifulSoup as bs

class FilmMining(object):
    
    Proxies = {'http' :'http://10.10.1.10:3128',
               'https':'http://10.10.1.10:1080'}

    KinopoiskURL = 'https://www.kinopoisk.ru/film/'

    def __init__(self, dataPathFilms, threads, maxID):
        self.dataPathFilms = dataPathFilms
        self.threads       = threads
        self.maxID         = maxID
    
        self.lock = threading.Lock() 

    def urlFilmParsing(self, IDArray):
        for ID in IDArray:
            
            sleep(5.0)

            try:
                response = requests.get(self.KinopoiskURL + f'{ID}/',
                                        headers = {'User-Agent':'YaBrowser/24.1.3.809'})
                
            except requests.ConnectionError:
                print('\n\t Error: Connection is broken!...')
                break
            
            if response.status_code != 200:
                continue
            
            pageKinopoisk = bs(response.content, features = 'html.parser')
            jsonFind = pageKinopoisk.find('script', type = 'application/ld+json')                        
            dataJSON = json.loads(jsonFind.text)
            
            #print(pageKinopoisk)

            if dataJSON is None:
                continue

            film = {
                'ID'            : ID,
                'type'          : dataJSON['@type'],
                'URL'           : dataJSON['url'],
                'name'          : dataJSON['name'],
                'headline'      : dataJSON['alternativeHeadline'],
                'alternateName' : dataJSON['alternateName'],
                'genre'         : dataJSON['genre'],
                'country'       : dataJSON['countryOfOrigin'],
                'year'          : dataJSON['datePublished'],
                'ratingValue'   : dataJSON['aggregateRating']['ratingValue'],
                'ratingCount'   : dataJSON['aggregateRating']['ratingCount'],
                'contentRating' : dataJSON['contentRating'],
                'family'        : dataJSON['isFamilyFriendly'],
                'producer'      : dataJSON['producer'],
                'director'      : dataJSON['director'],
                'actor'         : dataJSON['actor'],
                'description'   : dataJSON['description']
            }
            
            with self.lock:
                with open(self.dataPathFilms, 'w', encoding = 'utf-8') as file:
                    json.dump(film, file, indent = 4, ensure_ascii = False, separators = (',', ': '))

        return
    
    def main(self):

        print(f'\n\t The data is downloading to the file \"{self.dataPathFilms}\"...')

        parts = self.threads
        threadFilmArray = []
        
        #IDArray = list(range(self.maxID + 1))
        IDArray  = list(range(self.maxID, self.maxID + 1))
        IDArrays = [IDArray[i::parts] for i in range(parts)]

        for i in range(parts):
            thr = threading.Thread(target = self.urlFilmParsing, args = (IDArrays[i],))
            threadFilmArray.append(thr)
            thr.start()
        
        for thr in threadFilmArray:
            thr.join()
        
        print('\n\t The data was downloaded successfully!')

        return

if __name__ == '__main__':
    
    dataPathFilms = '../../data/films.json'
    threads       = 4
    maxID         = 700000 

    FilmMining(dataPathFilms, threads, maxID).main()