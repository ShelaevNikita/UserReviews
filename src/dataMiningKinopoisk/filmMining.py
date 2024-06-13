#!/usr/bin/env python3

import requests
import threading
import logging

from typing  import Dict, List, Union
from random  import random
from time    import sleep
from json    import loads
from bs4     import BeautifulSoup as bs
from pymongo import MongoClient

from dataClass.FilmDataClass import Person, Film

# Класс для скачивания данных с помощью Web-Scrapping
#   о различных фильмах / сериалах с сервиса "КиноПоиск"
class FilmMining(object):
    
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

    # Инициализация класса
    def __init__(self, configParameters: Dict[str, Union[int, str]],
                 mongoClient: MongoClient, IDArray: List[int]):
        
        self.dataPathFilms = configParameters['dataPathFilms']
        self.databaseName  = configParameters['databaseName']
        self.threads       = configParameters['threads']
        self.sleepTime     = configParameters['sleepTime']
        
        self.collection    = mongoClient[self.databaseName][self.dataPathFilms]

        self.IDArray       = IDArray

        self.lock = threading.Lock()
        
        logging.basicConfig(
            filename = './log/dataMining.log',
            format   = '%(asctime)s | %(levelname)s: %(message)s',
            filemode = 'w'
        )       
        self.logger  = logging.getLogger()
    
    # Поиск информации по ключу в найденном JSON и возвращение строки
    def checkKeyInDataStr(self, dataJSON: Dict[str, str], dataKey: str) -> str:
        return dataJSON[dataKey].replace(u'\x39', '\'') if (dataKey in dataJSON) else '?'
    
    # Поиск информации по ключу в найденном JSON и возвращение списка строк
    def checkKeyInDataArr(self, dataJSON: Dict[str, str], dataKey: str) -> List[str]:
        return dataJSON[dataKey] if (dataKey in dataJSON) else []

    # Преобразование словаря с информацией о человеке в класс Person
    def dictToPerson(self, personDict: Dict[str, str]) -> Person:
        newPerson            = Person()
        newPerson._id        = int(personDict['url'].split('/')[2])
        newPerson.personType = True if (personDict['@type'] == 'Person') else False
        newPerson.name       = personDict['name']
        return newPerson

    # Преобразование скаченного JSON в класс Film
    def JSONToFilm(self, dataJSON: Dict[str, str]) -> Film:
        newFilm                = Film()
        newFilm._id            = int(dataJSON['url'].split('/')[4])
        newFilm.filmType       = True if (dataJSON['@type'] == 'Movie') else False
        newFilm.URL            = dataJSON['url']
        
        newFilm.nameRU         = self.checkKeyInDataStr(dataJSON, 'name')        
        newFilm.nameEN         = self.checkKeyInDataStr(dataJSON, 'alternateName')
        newFilm.headline       = self.checkKeyInDataStr(dataJSON, 'alternativeHeadline')
        newFilm.contentRating  = self.checkKeyInDataStr(dataJSON, 'contentRating')
        
        newFilm.family         = int(dataJSON['isFamilyFriendly']) if ('isFamilyFriendly' in dataJSON) else 2
        newFilm.timeForEpisode = int(dataJSON['timeRequired'])     if ('timeRequired' in dataJSON)     else 0
        newFilm.episodesCount  = int(dataJSON['numberOfEpisodes']) if ('numberOfEpisodes' in dataJSON) else 1
        
        newFilm.year           = int(dataJSON['datePublished'])
                 
        if ('aggregateRating' in dataJSON):
            newFilm.ratingValue = float(dataJSON['aggregateRating']['ratingValue'])            
            newFilm.ratingCount = int(dataJSON['aggregateRating']['ratingCount'])     
        
        newFilm.description = dataJSON['description'].replace(u'\xa0', ' ').replace(u'\x97', '--') \
                                if ('description' in dataJSON) else '?'
        
        newFilm.genres    = [genre.capitalize() for genre in dataJSON['genre']]
        newFilm.countries = self.checkKeyInDataArr(dataJSON, 'countryOfOrigin')
        newFilm.awards    = self.checkKeyInDataArr(dataJSON, 'award')
        
        newFilm.producers = [self.dictToPerson(person) for person in dataJSON['producer']]
        newFilm.directors = [self.dictToPerson(person) for person in dataJSON['director']]
        newFilm.actors    = [self.dictToPerson(person) for person in dataJSON['actor']]

        return newFilm

    # Добавление новой записи в MongoDB
    def filmToMongoDB(self, film: Film):
        with self.lock:
            checkFilm = self.collection.find_one({ '_id' : film._id })
            if checkFilm is None:
                self.collection.insert_one(film.toDict())
                
            print(' Film:', film._id)
        return

    # Скачивание необходимых данных с сервиса "КиноПоиск"
    def urlFilmParsing(self, IDArray: int):
        for ID in IDArray:
            if ID != IDArray[0]:
                sleep((1 + random()) * self.sleepTime)
                
            try:
                response = requests.get(self.KinopoiskURL + f'{ID}/',
                                        headers = self.URLHeaders)
                
            except requests.ConnectionError:
                with self.lock:
                    self.logger.error(f'{ID} -> Connection is broken! | film')
                    
                break
            
            if response.status_code != 200:
                continue
            
            pageKinopoisk = bs(response.content, features = 'html.parser')
            jsonFind      = pageKinopoisk.find('script', type = 'application/ld+json')
            if jsonFind is None:               
                with self.lock:
                    self.logger.warning(f'{ID} -> Not found JSON on the site! | film')
                    
                continue

            self.filmToMongoDB(self.JSONToFilm(loads(jsonFind.text)))

        return
    
    # Главная функция класса, запускающая несколько параллельных потоков на скачивание данных
    def main(self):
        print('\t The data about films is downloading...')
        self.logger.debug('The data about films is downloading...')

        threadFilmArray = []        
        IDArrays        = [self.IDArray[i::self.threads] for i in range(self.threads)]
        
        for i in range(self.threads):
            thr = threading.Thread(target = self.urlFilmParsing, args = (IDArrays[i],))
            threadFilmArray.append(thr)
            thr.start()
        
        for thr in threadFilmArray:
            thr.join()

        print('\t The data about films was downloaded successfully!')
        self.logger.debug('The data about films was downloaded successfully!')
        return

if __name__ == '__main__':
    
    defaultConfigParameters = {
        'databaseName'  : 'userReviews',
        'dataPathFilms' : 'films',
        'threads'       : 4,
        'sleepTime'     : 30
    }

    mongoClient = MongoClient('mongodb://localhost:27017/')
    IDArray     = [435, 258687, 326, 448, 535341, 
                   404900, 89540, 464963, 79848, 253245]

    FilmMining(defaultConfigParameters, mongoClient, IDArray).main()