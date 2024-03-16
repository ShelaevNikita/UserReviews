#!/usr/bin/env python3

import requests
import json
import threading

from random import random
from time import sleep
from bs4 import BeautifulSoup as bs

class FilmMining(object):
    
    Proxies = {'http' :'http://10.10.1.10:3128',
               'https':'http://10.10.1.10:1080'}

    KinopoiskURL = 'https://www.kinopoisk.ru/film/'
    
    URLHeaders   = {
        'User-Agent' : 'Chrome/120.0.0.0 YaBrowser/24.1.0.0',
        'Referer'    : 'https://sso.kinopoisk.ru/'
    }

    def __init__(self, dataPathFilms, threads, maxID):
        self.dataPathFilms = dataPathFilms
        self.threads       = threads
        self.maxID         = maxID
    
        self.lock = threading.Lock()
        
        self.filmMissing   = []
        self.filmJSONArray = []

    def personNameAndID(self, personDict):
        return {
            'ID'   : int(personDict['url'].split('/')[2]),
            'name' : personDict['name']
        }

    def makeFilmJSON(self, dataJSON):

        filmJSON = {
            'ID'             : int(dataJSON['url'].split('/')[4]),
            'type'           : dataJSON['@type'],
            'URL'            : dataJSON['url'],
            'nameRU'         : dataJSON['name'],
            'nameEN'         : dataJSON['alternateName'],
            'headline'       : dataJSON['alternativeHeadline'],
            'contentRating'  : dataJSON['contentRating']
                                if (dataJSON['@type'] == 'Movies') else '-',
                                
            'family'         : dataJSON['isFamilyFriendly'],
            
            'ratingValue'    : dataJSON['aggregateRating']['ratingValue'],
            'ratingCount'    : dataJSON['aggregateRating']['ratingCount'],
            
            'timeForEpisode' : int(dataJSON['timeRequired']),
            'episodesCount'  : dataJSON['numberOfEpisodes'] 
                                if (dataJSON['@type'] == 'TVSeries') else 0
        }
        
        filmJSON['allTime'] = filmJSON['timeForEpisode'] \
            if (filmJSON['episodesCount'] == 0) else (filmJSON['timeForEpisode'] * filmJSON['episodesCount'])
            
        filmJSON['year']        = int(dataJSON['datePublished'])
        
        filmJSON['description'] = dataJSON['description'].replace(u'\xa0', ' ').replace(u'\x97', '--')
        
        filmJSON['genre']       = [genre.capitalize() for genre in dataJSON['genre']]
        filmJSON['country']     = dataJSON['countryOfOrigin']
        filmJSON['awards']      = dataJSON['award'] if ('award' in dataJSON) else []
        
        filmJSON['producer']    = [self.personNameAndID(person) for person in dataJSON['producer']]
        filmJSON['director']    = [self.personNameAndID(person) for person in dataJSON['director']]
        filmJSON['actor']       = [self.personNameAndID(person) for person in dataJSON['actor']]     
        
        with self.lock:
            self.filmJSONArray.append(filmJSON)

        return

    def urlFilmParsing(self, IDArray):
        
        for ID in IDArray:
            
            sleep(7.5 + random() * 10.0)

            try:
                response = requests.get(self.KinopoiskURL + f'{ID}/',
                                        headers = self.URLHeaders)
                
            except requests.ConnectionError:
                print('\n Error: Connection is broken!...')
                break
            
            if response.status_code != 200:
                continue
            
            pageKinopoisk = bs(response.content, features = 'html.parser')
            jsonFind = pageKinopoisk.find('script', type = 'application/ld+json')

            if jsonFind is None:
                print('\n Warning: Not fount JSON on the site...')
                with self.lock:
                    self.filmMissing.append(ID)
                continue

            self.makeFilmJSON(json.loads(jsonFind.text))

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
        
        allFilmJSON = {
            'filmCount'   : len(self.filmJSONArray),
            'filmMissing' : self.filmMissing,
            'filmArray'   : self.filmJSONArray
        }

        with open(self.dataPathFilms, 'w', encoding = 'utf-8') as file:
            json.dump(allFilmJSON, file, indent = 4,
                      ensure_ascii = False, separators = (',', ': '))

        print('\n\t The data was downloaded successfully!\n')

        return

if __name__ == '__main__':
    
    dataPathFilms = '../../data/movies.json'
    threads       = 4
    maxID         = 700000 

    FilmMining(dataPathFilms, threads, maxID).main()