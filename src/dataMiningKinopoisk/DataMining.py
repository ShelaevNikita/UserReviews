#!/usr/bin/env python3

import logging

from typing import Union, List, Tuple, Dict
from pymongo import MongoClient
from random import shuffle

import dataMiningKinopoisk.FilmMining   as FilmMining
import dataMiningKinopoisk.ReviewMining as ReviewMining

# Класс для получения данных, связанных с фильмами / сериалами
#    и их пользовательскими оценками, с сервиса "КиноПоиск"
class ClassDataMining(object):
    
    # Значения конфигурационного файла по умолчанию
    DefaultConfigParameters = {
        'pathMongoDB'     : 'mongodb://localhost:27017/',
        'databaseName'    : 'userReviews',
        'dataPathFilms'   : 'films',
	    'dataPathReviews' : 'reviews',    
	    'threads'         : 4,
	    'maxID'           : 5000000,
	    'sleepTime'       : 120,
	    'takeFilms'       : 10000
    }
    
    # Инициализация класса
    def __init__(self):       
        self.configFile        = 'dataMiningKinopoisk/miningConfigFile.txt'   
        self.configParameters  = self.DefaultConfigParameters
        
        self.collectionFilms   = None
        self.collectionReviews = None

        logging.basicConfig(
            filename = '../log/dataMining.log',
            format   = '%(asctime)s | %(levelname)s: %(message)s',
            filemode = 'w+'
        )
        self.logger     = logging.getLogger()   
    
    # Получение данных из конфигурационного файла
    def splitConfigFile(self):    
        dataParameters = []    
        try:
            with open(self.configFile, 'r') as fileData:
                dataParameters = fileData.readlines()
                
        except FileNotFoundError:
            self.logger.error('Not found config file for Data Mining!')
            return
        
        for line in dataParameters[3:]:        
            splitParameter = line.split('=')
            parameterName  = splitParameter[0].strip()
            parameterValue = splitParameter[1].strip()
            if parameterValue.isdigit():
                parameterValue = int(parameterValue)
            
            self.configParameters[parameterName] = parameterValue
            
        return

    # Подключение к MongoDB
    def connectionToMongoDB(self) -> Union[MongoClient, None]:
        mongoClient = None
        try:
            mongoClient = MongoClient(self.configParameters['pathMongoDB'])
            
        except ConnectionError:
            self.logger.error('Not connection to MongoDB!')
                
        return mongoClient

    # Получение массива ID фильмов / сериалов, находящихся в MongoDB
    def getFilmIDInMongoDB(self) -> List[Tuple[int, int]]:
        return [(record['_id'], record['ratingCount']) for record in self.collectionFilms.find()]

    # Создание массива ID фильмов / сериалов, которых ещё нет в MongoDB
    def createFilmIDArray(self) -> List[int]:
        listAllID = list(range(self.configParameters['maxID'] + 1))      
        for (filmID, _) in self.getFilmIDInMongoDB():
            listAllID.remove(filmID)
            
        shuffle(listAllID)
        return listAllID[:self.configParameters['takeFilms']]

    # Создание массива пользовательских отзывов, которых ещё нет в MongoDB
    def createReviewIDArray(self) -> Dict[int, List[int]]:
        listFilmIDAndCount = self.getFilmIDInMongoDB()
        listReviews        = [record['_id'] for record in self.collectionReviews.find()]
        reviewFilmPage     = {}
        for (filmID, reviewCount) in listFilmIDAndCount:
            if filmID not in listReviews and reviewCount > 0:
                reviewFilmPage[filmID] = []
            
        for review in self.collectionReviews.find():
            if len(review['pages']) < ((review['reviewMax'] + 199) // 200):
                listPages = list(range(1, (review['reviewMax'] + 199) // 200 + 1))
                for page in review['pages']:
                    listPages.remove(page)
                    
                reviewFilmPage[review['_id']] = listPages

        return reviewFilmPage
    
    # Последовательный вызов всех необходимых функций
    def main(self):
        self.splitConfigFile()
        
        mongoClient = self.connectionToMongoDB()
        if mongoClient is None:
            return
        
        connectionDB           =  mongoClient[self.configParameters['databaseName']]
        self.collectionFilms   = connectionDB[self.configParameters['dataPathFilms']]
        self.collectionReviews = connectionDB[self.configParameters['dataPathReviews']]

        filmID         = self.createFilmIDArray()
        FilmMining.FilmMining(self.configParameters, mongoClient, filmID).main()
        
        reviewFilmPage = self.createReviewIDArray()
        ReviewMining.ReviewMining(self.configParameters, mongoClient, reviewFilmPage).main()
        
        return

if __name__ == '__main__':
    ClassDataMining().main()
