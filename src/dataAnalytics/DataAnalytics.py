#!/usr/bin/env python3

from itertools import filterfalse
import logging

from typing      import Dict, List, Union, Any, Tuple
from collections import Counter
from pymongo     import MongoClient
from datetime    import datetime as dt
from datetime    import timedelta

# Класс для аналитической обработки полученных данных,
#   находящихся в MongoDB
class DataAnalytics(object):
    
    # Значения конфигурационного файла по умолчанию
    DefaultConfigParameters = {
        'pathMongoDB'      : 'mongodb://localhost:27017/',
        'databaseName'     : 'userReviews',
        'dataPathFilms'    : 'films',
	    'dataPathReviews'  : 'reviews',
        'dataPathAnalytic' : 'analytic',
        'reviewWindowSize' : 5,
        'reviewValueUp'    : 5
    }

    # Инициализация класса
    def __init__(self):       
        self.configFile         = './src/dataAnalytics/analyticConfigFile.txt'   
        self.configParameters   = self.DefaultConfigParameters
        
        self.collectionFilms    = None
        self.collectionReviews  = None
        self.collectionAnalytic = None

        logging.basicConfig(
            filename = './log/dataAnalytic.log',
            format   = '%(asctime)s | %(levelname)s: %(message)s',
            filemode = 'w'
        )
        self.logger  = logging.getLogger()
    
    # Получение данных из конфигурационного файла
    def splitConfigFile(self):    
        dataParameters = []    
        try:
            with open(self.configFile, 'r') as fileData:
                dataParameters = fileData.readlines()
                
        except FileNotFoundError:
            self.logger.error('Not found config file for Data Analytics!')
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

    # Добавление новой информации в MongoDB
    def infoToMongoDB(self, nameParam: str, info: List[Any]):
        if self.collectionAnalytic.find_one({ 'nameParam' : nameParam }) is None:
            self.collectionAnalytic.insert_one({ 'nameParam' : nameParam, 'valuesParam' : info })
            
        else:
             self.collectionAnalytic.update_one({ 'nameParam' : nameParam },
                                                { '$set' : { 'valuesParam' : info }})

        return

    # Подсчёт количества одного параметра по всем фильмам / сериалам и запись результата в MongoDB
    def countFilmParam(self, param: str, flag = True):       
        paramDict = Counter()
        for film in self.collectionFilms.find():
            if flag:
                for elem in film[param]:               
                    paramDict[elem] += 1
                    
            else:
                paramDict[film[param]] += 1  
        
        self.infoToMongoDB(param, sorted(list(paramDict.items()), 
                                         key = lambda X: X[1], reverse = True))       
        return

    # Подсчёт количества некоторых параметров по всем фильмам / сериалам
    def countFilmParamToDB(self):
        self.countFilmParam('genres')
        self.countFilmParam('countries')
        self.countFilmParam('year', False)
        return

    # Информация по рейтингу фильмов / сериалов
    def countFilmRating(self):       
        filmRating = []
        for film in self.collectionFilms.find():
            filmRating.append((film['nameRU'], film['ratingValue'], film['ratingCount']))
        
        filmRatingValue = sorted(filmRating, key = lambda X: X[1], reverse = True)
        filmRatingCount = sorted(filmRating, key = lambda X: X[2], reverse = True)
        
        self.infoToMongoDB('filmRating', [filmRatingValue, filmRatingCount])
        return
    
    # Информация по продолжительности фильмов / сериалов
    def countFilmTime(self):       
        filmTime = []
        for film in self.collectionFilms.find():
            timeForEpisode = film['timeForEpisode']
            episodesCount  = film['episodesCount']
            filmTime.append((film['nameRU'], timeForEpisode, episodesCount, timeForEpisode * episodesCount))

        timeForEpisodeList = sorted(filmTime, key = lambda elem: elem[1], reverse = True)
        episodesCountList  = sorted(filmTime, key = lambda elem: elem[2], reverse = True)
        allTimeList        = sorted(filmTime, key = lambda elem: elem[3], reverse = True)
        
        self.infoToMongoDB('filmTime', [timeForEpisodeList, episodesCountList, allTimeList])
        return

    # Подсчёт количества средней пользовательской оценки для некоторого участника съёмочной группы
    def countFilmPerson(self, typeOfPersons: str):
        personIDAndName   = {}
        personIDAndRating = {}       
        personRatingList  = []
        for film in self.collectionFilms.find():           
            filmRatingValue = film['ratingValue']
            for person in film[typeOfPersons]:
                personID = person['_id']
                if personID not in personIDAndName:
                    personIDAndName  [personID] = person['name']
                    personIDAndRating[personID] = []
                
                personIDAndRating[personID].append(filmRatingValue)
        
        for (personID, personRating) in personIDAndRating.items():           
            personFilmCount = len(personRating)
            personRatingAvg = round(sum(personRating) / personFilmCount, 3)

            personRatingList.append((personID, personIDAndName[personID],
                                 personRatingAvg, personFilmCount))
        
        personRatingList.sort(key = lambda X: X[2], reverse = True)
        
        self.infoToMongoDB(typeOfPersons, personRatingList)
        return

    # Расчёт средней пользовательской оценки для съёмочной группы
    def countFilmPersonToDB(self):
        self.countFilmPerson('producers')
        self.countFilmPerson('directors')
        self.countFilmPerson('actors')
        return

    # Сохранение информации о пользовательских оценках ко всем фильмам / сериалам
    def countFilmReview(self):
        reviewCount = []
        for review in self.collectionReviews.find():
            reviewPercWithoutNeut = (
                round((review['countGood'] + review['countNeutral'] // 2) / review['reviewMax'] * 100, 3),
                round( review['countGood'] / (review['reviewMax'] - review['countNeutral'])     * 100, 3),
            )
            
            filmName = '?'
            cursorFilmName = self.collectionFilms.find_one({ '_id' : review['_id']})
            if cursorFilmName is not None:
                filmName = cursorFilmName['nameRU']
                
            reviewCount.append((review['_id'], filmName, review['reviewMax'], review['reviewPercent'],
                                review['countGood'], review['countNegative'], reviewPercWithoutNeut))
        
        reviewMax      = sorted(reviewCount, key = lambda elem: elem[2], reverse = True)
        reviewPercent  = sorted(reviewCount, key = lambda elem: elem[3], reverse = True)

        self.infoToMongoDB('reviewCount', [reviewMax, reviewPercent])       
        return 

    # Подсчёт распределения количества пользовательских оценок 
    #    по дням и месяцам для определённого фильма / сериала
    def countReviewDate(self, filmReview: Dict[str, Any]):
        reviewDateCount    = Counter()
        reviewDateDayCount = Counter()
        datetimeMin        = dt.today()
        for review in filmReview['reviews']:              
            reviewDateAndTime = dt.strptime(review['dateAndTime'], '%H:%M|%d.%m.%Y')
            datetimeMin       = min(datetimeMin, reviewDateAndTime)
        
        dateGenerated = [datetimeMin + timedelta(days = day) 
                            for day in range(0, (dt.today() - datetimeMin).days + 1)]

        for date in dateGenerated:
            reviewDateCount[date.strftime('%Y.%m')]       = 0
            reviewDateDayCount[date.strftime('%Y.%m.%d')] = 0
            
        for review in filmReview['reviews']:              
            reviewDateAndTime = dt.strptime(review['dateAndTime'], '%H:%M|%d.%m.%Y')
            reviewDateCount[reviewDateAndTime.strftime('%Y.%m')]       += 1
            reviewDateDayCount[reviewDateAndTime.strftime('%Y.%m.%d')] += 1

        reviewDate = [(dt.strptime(key, '%Y.%m'), value) 
                       for (key, value) in sorted(reviewDateCount.items())]
        
        reviewDateDay = [(dt.strptime(key, '%Y.%m.%d'), value) 
                          for (key, value) in sorted(reviewDateDayCount.items())]
        
        filmID = filmReview['_id']
        self.infoToMongoDB(f'reviewDate/{filmID}', reviewDate)
        self.infoToMongoDB(f'reviewDateDay/{filmID}', reviewDateDay)
        return 

    # Подсчёт распределения количества пользовательских оценок 
    #    по дням и месяцам для всех фильмов / сериалов
    def countReviewDateToDB(self):
        for filmReview in self.collectionReviews.find():
            self.countReviewDate(filmReview)
            
        return 

    # Изменение распределения пользовательских оценок для определённого дня / месяца
    def changeListReviewDate(self, reviewDateName: str, dateDT: dt, key: str, 
                             countMax: int, reviewDateList: List[Tuple[dt, int]]) -> bool:       
        flagOver  = True
        dateToKey = dt.strptime(dateDT.strftime(key), key)
        for i in range(len(reviewDateList)):
            dateKey, value = reviewDateList[i]
            if (dateKey == dateToKey):
                reviewDateList[i] = (dateKey, value + 1)
                if (value + 1) > countMax:
                    flagOver = False
                    
                break
        
        else:
            reviewDateList.append((dateToKey, 1))
        
        self.infoToMongoDB(reviewDateName, reviewDateList)
        return flagOver

    # Обновление распределения пользовательских оценок для определённых дня
    #   и месяца и конкретного фильма / сериала
    def updateReviewDateToDB(self, date: str, filmID: int, valueUp: int) -> bool:
        dateDT             = dt.strptime(date, '%H:%M|%d.%m.%Y')
        
        reviewDateName     = f'reviewDate/{filmID}'
        reviewDateDayName  = f'reviewDateDay/{filmID}'
        reviewDateWWUpName = f'reviewDateWWUp/{filmID}/{valueUp}'
        
        reviewDateList     = self.collectionAnalytic.find_one({ 'nameParam' : reviewDateName })
        reviewDateDayList  = self.collectionAnalytic.find_one({ 'nameParam' : reviewDateDayName })
        reviewDateWWUpList = self.collectionAnalytic.find_one({ 'nameParam' : reviewDateWWUpName })
        
        countMax     = self.configParameters['reviewValueUp'] + 1
        if reviewDateWWUpList is not None:
            countMax = reviewDateWWUpList['valuesParam'][-1][1]
        
        flagDate     = True
        flagDay      = True
        if reviewDateList is not None:
            flagDate = self.changeListReviewDate(reviewDateName, dateDT, '%Y.%m',
                                                 countMax, reviewDateList['valuesParam'])

        if reviewDateDayList is not None:
            flagDay  = self.changeListReviewDate(reviewDateDayName, dateDT, '%Y.%m.%d',
                                                 countMax, reviewDateDayList['valuesParam'])
        
        return (flagDate and flagDay)

    # Подсчёт распределения количества слов в пользовательских оценках
    #   в зависимости от их класса для конкретного фильма / сериала
    def reviewLenText(self, filmReview: Dict[str, Any]):       
        reviews = [[], [], []]
        for review in filmReview['reviews']:
            reviewText = []               
            for symbol in review['reviewText']:
                newSymbol = ' '
                if symbol.isalpha() or symbol.isdigit():
                    newSymbol = symbol.lower()
                        
                reviewText.append(newSymbol)
                                
            reviews[review['reviewClass']].append(len(''.join(reviewText).split()))
        
        fiimID = filmReview['_id']
        self.infoToMongoDB(f'reviewLenText/{fiimID}', reviews)
        return

    # Подсчёт распределения количества слов в пользовательских оценках
    #   в зависимости от их класса для всех фильмов / сериалов
    def reviewLenTextToDB(self):
        for filmReview in self.collectionReviews.find():
            self.reviewLenText(filmReview)
            
        return 

    # Построение распределения с медианной фильтрацией количества
    #    пользовательских оценок по месяцам для конкретного фильма / сериала 
    def reviewDateWW(self, filmID: int, windowSize: int, reviewDate: List[Tuple[dt, int]]):
        reviewValue      = []
        reviewDateMedian = []
        for i in range(len(reviewDate)):
            reviewValue.append(reviewDate[i][1])           
            if i >= windowSize:
                reviewValue.remove(reviewDate[i - windowSize][1])

            reviewValue.sort()
            reviewDateMedian.append(reviewValue[len(reviewValue) // 2])
            
        while len(reviewDateMedian) < len(reviewDate):
            reviewDateMedian.append(reviewDateMedian[-1])
        
        reviewDateAndMedian = [(reviewDate[i][0], reviewDateMedian[i]) for i in range(len(reviewDate))]
        self.infoToMongoDB(f'reviewDateWW/{filmID}/{windowSize}', reviewDateAndMedian)
        return 

    # Построение распределения с медианной фильтрацией количества
    #    пользовательских оценок по месяцам для всех фильмов / сериалов
    def reviewDateWWToDB(self, windowSize: int):
        for filmReview in self.collectionReviews.find():
            filmID         = filmReview['_id']
            reviewDateList = self.collectionAnalytic.find_one({ 'nameParam' : f'reviewDate/{filmID}' })
            if reviewDateList is None:
                continue
            
            self.reviewDateWW(filmReview['_id'], windowSize, reviewDateList['valuesParam'])

        return

    # Построение распределения, поднятого на некоторое значение, количества 
    #   пользовательских оценок по месяцам для конкретного фильма / сериала
    def reviewDateWWUp(self, filmID: int, valueUp: int, reviewDate: List[Tuple[dt, int]]):
        reviewNewValue = [(review[0], (review[1] + valueUp)) for review in reviewDate]
        self.infoToMongoDB(f'reviewDateWWUp/{filmID}/{valueUp}', reviewNewValue)
        return

    # Построение распределения, поднятого на некоторое значение, количества 
    #   пользовательских оценок по месяцам для всех фильмов / сериалов
    def reviewDateWWUpToDB(self, windowSize: int, valueUp: int):
        for filmReview in self.collectionReviews.find():
            filmID           = filmReview['_id']
            reviewDateWWName = f'reviewDateWW/{filmID}/{windowSize}'
            reviewDateWWList = self.collectionAnalytic.find_one({ 'nameParam' : reviewDateWWName })
            if reviewDateWWList is None:
                continue
            
            self.reviewDateWWUp(filmReview['_id'], valueUp, reviewDateWWList['valuesParam'])

        return

    # Обработка и запись в MongoDB информации обо всех фильмах / сериалах
    def filmAnalytics(self):
        self.countFilmParamToDB()
        self.countFilmRating()
        self.countFilmTime()
        self.countFilmPersonToDB()
        return

    # Обработка и запись в MongoDB информации обо всех пользовательских оценках
    def reviewAnalytics(self):        
        self.countFilmReview()
        self.countReviewDateToDB()
        self.reviewLenTextToDB()
        self.reviewDateWWToDB(self.configParameters['reviewWindowSize'])
        self.reviewDateWWUpToDB(self.configParameters['reviewWindowSize'], 
                                self.configParameters['reviewValueUp'])
        return

    # Тестирование системы на корректное определение "атаки"
    def updateAnalytics(self):
        dateNow       = dt.now().strftime('%H:%M|%d.%m.%Y')
        reviewValueUp = self.configParameters['reviewValueUp']        
        for _ in range(reviewValueUp + 1):
            flagOver  = self.updateReviewDateToDB(dateNow, 435, reviewValueUp)
        
        print(flagOver)
        return

    # Последовательный вызов всех необходимых функций
    def main(self):
        self.splitConfigFile()
        
        mongoClient = self.connectionToMongoDB()
        if mongoClient is None:
            return
        
        connectionDB            =  mongoClient[self.configParameters['databaseName']]
        self.collectionFilms    = connectionDB[self.configParameters['dataPathFilms']]
        self.collectionReviews  = connectionDB[self.configParameters['dataPathReviews']]
        self.collectionAnalytic = connectionDB[self.configParameters['dataPathAnalytic']]

        self.filmAnalytics()
        self.reviewAnalytics()

        #self.updateAnalytics()

        return

if __name__ == '__main__':  
    DataAnalytics().main()