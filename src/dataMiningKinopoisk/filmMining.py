#!/usr/bin/env python3

import requests
import json
import threading

from random import random, shuffle
from time import sleep
from bs4 import BeautifulSoup as bs

class FilmMining(object):
    
    Proxies = {
        'http'  : 'http://10.10.1.10:3128',
        'https' : 'http://10.10.1.10:1080'
    }

    KinopoiskURL = 'https://www.kinopoisk.ru/film/'
    
    URLHeaders   = {
        'User-Agent' : 'Chrome/120.0.0.0 YaBrowser/24.1.0.0',
        'Referer'    : 'https://sso.kinopoisk.ru/'
    }

    def __init__(self, configParameters):

        self.dataPathFilms = configParameters['dataPathFilms']
        self.threads       = configParameters['threads']
        self.maxID         = configParameters['maxID']
        self.takeFilms     = configParameters['takeFilms']
    
        self.lock = threading.Lock()
        
        self.filmMissing   = []
        self.IDNotUsed     = []
        self.filmJSONArray = []
        
    def checkKeyInDataStr(self, dataJSON, dataKey):
        return dataJSON[dataKey].replace(u'\x39', '\'') if (dataKey in dataJSON) else '???'
    
    def checkKeyInDataArr(self, dataJSON, dataKey):
        return dataJSON[dataKey] if (dataKey in dataJSON) else []

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
            'nameEN'         : self.checkKeyInDataStr(dataJSON, 'alternateName'),
            'headline'       : self.checkKeyInDataStr(dataJSON, 'alternativeHeadline'),
            'contentRating'  : self.checkKeyInDataStr(dataJSON, 'contentRating'),
            
            'family'         : dataJSON['isFamilyFriendly'] if ('isFamilyFriendly' in dataJSON) else None,
            
            'timeForEpisode' : int(dataJSON['timeRequired']) if ('timeRequired' in dataJSON)      else -1,
            'episodesCount'  : dataJSON['numberOfEpisodes']  if (dataJSON['@type'] == 'TVSeries') else -1
        }
        
        filmJSON['allTime'] = filmJSON['timeForEpisode'] * filmJSON['episodesCount'] \
            if (filmJSON['episodesCount'] > 0) else filmJSON['timeForEpisode']
         
        if ('aggregateRating' in dataJSON):
            filmJSON['ratingValue'] = dataJSON['aggregateRating']['ratingValue']                                    
            filmJSON['ratingCount'] = dataJSON['aggregateRating']['ratingCount']

        else:
            filmJSON['ratingValue'] = 0.0
            filmJSON['ratingCount'] = 0

        filmJSON['year']        = int(dataJSON['datePublished'])
        
        filmJSON['description'] = \
            dataJSON['description'].replace('\n', '').replace(u'\xa0', ' ').replace(u'\x97', '--') \
                if ('description' in dataJSON) else '???'
        
        filmJSON['genre']       = [genre.capitalize() for genre in dataJSON['genre']]
        filmJSON['country']     = self.checkKeyInDataArr(dataJSON, 'countryOfOrigin')
        filmJSON['awards']      = self.checkKeyInDataArr(dataJSON, 'award')
        
        filmJSON['producer']    = [self.personNameAndID(person) for person in dataJSON['producer']]
        filmJSON['director']    = [self.personNameAndID(person) for person in dataJSON['director']]
        filmJSON['actor']       = [self.personNameAndID(person) for person in dataJSON['actor']]     
        
        with self.lock:
            self.filmJSONArray.append(filmJSON)

        return

    def urlFilmParsing(self, IDArray):
        
        firstID = IDArray[0]

        for ID in IDArray:
            
            if (firstID != ID):
                sleep(30.0 + random() * 15.0)

            try:
                response = requests.get(self.KinopoiskURL + f'{ID}/',
                                        headers = self.URLHeaders)
                
            except requests.ConnectionError:
                with self.lock:
                    print('\n Error: Connection is broken!...')
                break
            
            if response.status_code != 200:
                with self.lock:
                    self.IDNotUsed.append(ID)
                continue
            
            pageKinopoisk = bs(response.content, features = 'html.parser')
            jsonFind = pageKinopoisk.find('script', type = 'application/ld+json')

            if jsonFind is None:               
                with self.lock:
                    print(' Warning: Not fount JSON on the site...')
                    self.filmMissing.append(ID)
                continue

            self.makeFilmJSON(json.loads(jsonFind.text))

        return
    
    def main(self):

        print(f'\n\t The data about films is downloading to the file \"{self.dataPathFilms}\"...\n')

        parts = self.threads
        threadFilmArray = []
        
        IDArray = list(range(self.maxID + 1))
        shuffle(IDArray)
        IDArray = IDArray[:self.takeFilms] if self.takeFilms > 0 else IDArray
        
        # IDArray.append(435)
        # IDArray.append(258687)
        # IDArray.append(326)
        # IDArray.append(448)
        # IDArray.append(535341)       
        # IDArray.append(404900)
        # IDArray.append(89540)
        # IDArray.append(464963)
        # IDArray.append(79848)
        # IDArray.append(253245)

        IDArrays = [IDArray[i::parts] for i in range(parts)]

        for i in range(parts):
            thr = threading.Thread(target = self.urlFilmParsing, args = (IDArrays[i],))
            threadFilmArray.append(thr)
            thr.start()
        
        for thr in threadFilmArray:
            thr.join()
        
        allFilmJSON = {
            'filmCount'     : len(self.filmJSONArray),
            'filmIDNotUsed' : self.IDNotUsed,
            'filmMissing'   : self.filmMissing,
            'filmArray'     : self.filmJSONArray
        }

        with open(self.dataPathFilms, 'w', encoding = 'utf-8') as file:
            json.dump(allFilmJSON, file, indent = 4,
                      ensure_ascii = False, separators = (',', ': '))

        print('\n\t The data about films was downloaded successfully!\n')

        return

if __name__ == '__main__':
    
    defaultConfigParameters = {
        'dataPathFilms' : '../../data/movies.json',
        'threads'       : 4,
        'maxID'         : 700000,
        'takeFilms'     : 100
    }

    FilmMining(defaultConfigParameters).main()