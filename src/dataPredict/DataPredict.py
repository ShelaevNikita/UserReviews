#!/usr/bin/env python3

import numpy as np
import logging

from typing                  import List, Union, Any, Tuple
from pymongo                 import MongoClient
from datetime                import datetime as dt

from sklearn.linear_model    import LinearRegression
from sklearn.tree            import DecisionTreeRegressor
from sklearn.preprocessing   import PolynomialFeatures
from sklearn.model_selection import train_test_split
from sklearn.preprocessing   import StandardScaler
from sklearn.metrics         import mean_squared_error, r2_score

# Класс для аналитической обработки полученных данных,
#   находящихся в MongoDB
class DataPredict(object):
    
    # Значения конфигурационного файла по умолчанию
    DefaultConfigParameters = {
        'pathMongoDB'      : 'mongodb://localhost:27017/',
        'databaseName'     : 'userReviews',
        'dataPathFilms'    : 'films',
	    'dataPathReviews'  : 'reviews',
        'dataPathAnalytic' : 'analytic',
        'dataPathPredict'  : 'predict',
        'reviewWindowSize' : 5,
        'reviewValueUp'    : 5,
        'reviewDegree'     : 7
    }

    # Инициализация класса
    def __init__(self):       
        self.configFile         = 'dataPredict/predictConfigFile.txt'   
        self.configParameters   = self.DefaultConfigParameters
        
        self.collectionFilms    = None
        self.collectionReviews  = None
        self.collectionAnalytic = None
        self.collectionPredict  = None

        logging.basicConfig(
            filename = '../log/dataPredict.log',
            format   = '%(asctime)s | %(levelname)s: %(message)s',
            filemode = 'w+'
        )
        self.logger = logging.getLogger()
    
    # Получение данных из конфигурационного файла
    def splitConfigFile(self):    
        dataParameters = []    
        try:
            with open(self.configFile, 'r') as fileData:
                dataParameters = fileData.readlines()
                
        except FileNotFoundError:
            self.logger.error('Not found config file for Data Predict!')
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
        if self.collectionPredict.find_one({ 'nameParam' : nameParam }) is None:
            self.collectionPredict.insert_one({ 'nameParam' : nameParam, 'valuesParam' : info })
            
        else:
             self.collectionPredict.update_one({ 'nameParam' : nameParam },
                                               { '$set' : { 'valuesParam' : info }})
             
        return

    # Подготовка данных для обучения регрессии и Дерева Решений
    def prepareDataToPredict(self, reviewDate: List[Tuple[dt, int]], testSize = 0.2) -> \
            Tuple[List[float], List[float], List[int], List[int]]:
        
        reviewIntTime = []
        reviewValue   = []
        for (date, value) in reviewDate:
            year, month = map(int, date.strftime('%Y.%m').split('.'))
            reviewIntTime.append(year * 100 + month)
            reviewValue.append(value)
        
        reviewIntTime = np.array(reviewIntTime).reshape((-1, 1))
        reviewValue   = np.array(reviewValue)
        
        XTrain, XTest, YTrain, YTest = train_test_split(reviewIntTime, reviewValue,
                                                        test_size = testSize, shuffle = False)
        
        scaler = StandardScaler()
        scaler.fit(XTrain)
        
        XTrain = scaler.transform(XTrain)
        XTest  = scaler.transform(XTest)

        return (XTrain, XTest, YTrain, YTest)

    # Применение Линейной регрессии для распределения пользовательских отзывов 
    #   по месяцам для конкретного фильма / сериала
    def linearRegressionForReview(self, reviewDate: List[Tuple[dt, int]], 
                                  reviewID: int, reviewValueUp: int):
        
        XTrain, XTest, YTrain, YTest = self.prepareDataToPredict(reviewDate, 0.1)
        
        reviewRegression    = LinearRegression().fit(XTrain, YTrain)
        predictReviewValue  = reviewRegression.predict(XTest)
        
        predictReviewValue  = np.append(YTrain, predictReviewValue)
        predictReviewDate   = [(reviewDate[i][0], predictReviewValue[i]) for i in range(len(reviewDate))]

        RMSE    = np.sqrt(mean_squared_error(predictReviewValue, np.append(YTrain, YTest)))
        R2Score = abs(r2_score(predictReviewValue, np.append(YTrain, YTest)))
        
        self.logger.warning(f'linearRegression/{reviewID}/RMSE/{RMSE}')
        self.logger.warning(f'linearRegression/{reviewID}/R2/{R2Score}')

        predictReviewDateUp = []
        for i in range(len(predictReviewValue)):
            if predictReviewValue[i] < reviewValueUp:
                predictReviewDateUp.append((reviewDate[i][0], reviewValueUp))

            else:
                predictReviewDateUp.append((reviewDate[i][0], predictReviewValue[i]))
        
        self.infoToMongoDB(f'LRReviewDate/{reviewID}', predictReviewDate)
        self.infoToMongoDB(f'LRReviewDateUp/{reviewID}/{reviewValueUp}', predictReviewDateUp)
        return

    # Применение Линейной регрессии для распределения пользовательских отзывов 
    #   по месяцам для всех фильмов / сериалов
    def linearRegressionForReviewInDB(self):
        reviewWindowSize = self.configParameters['reviewWindowSize']
        reviewValueUp    = self.configParameters['reviewValueUp']
        for review in self.collectionReviews.find():
            reviewID           = review['_id']
            reviewDateWWKey    = f'reviewDateWW/{reviewID}/{reviewWindowSize}'
            cursorReviewDateWW = self.collectionAnalytic.find_one({ 'nameParam' : reviewDateWWKey })
            if cursorReviewDateWW is None or len(cursorReviewDateWW['valuesParam']) < 5:
                continue
            
            self.linearRegressionForReview(cursorReviewDateWW['valuesParam'], reviewID, reviewValueUp)

        return

    # Применение Полиномиальной регрессии для распределения пользовательских
    #   отзывов по месяцам для конкретного фильма / сериала
    def polynomialRegressionForReview(self, reviewDate: List[Tuple[dt, int]], 
                                      reviewID: int, degree: int, reviewValueUp: int):
        
        XTrain, XTest, YTrain, YTest = self.prepareDataToPredict(reviewDate, 0.05)
        
        polyFeatures       = PolynomialFeatures(degree = degree, include_bias = False) 
        polyX              = polyFeatures.fit_transform(XTrain)
        polyTestX          = polyFeatures.fit_transform(XTest)
        
        reviewRegression   = LinearRegression().fit(polyX, YTrain)
        predictReviewValue = reviewRegression.predict(polyTestX)
        
        predictReviewValue  = np.append(YTrain, predictReviewValue)
        predictReviewDate   = [(reviewDate[i][0], predictReviewValue[i]) for i in range(len(reviewDate))]

        RMSE    = np.sqrt(mean_squared_error(predictReviewValue, np.append(YTrain, YTest)))
        R2Score = abs(r2_score(predictReviewValue, np.append(YTrain, YTest)))
        
        self.logger.warning(f'polynomialRegression/{reviewID}/RMSE/{RMSE}')
        self.logger.warning(f'polynomialRegression/{reviewID}/R2/{R2Score}')

        predictReviewDateUp = []
        for i in range(len(predictReviewValue)):
            if predictReviewValue[i] < reviewValueUp:
                predictReviewDateUp.append((reviewDate[i][0], reviewValueUp))

            else:
                predictReviewDateUp.append((reviewDate[i][0], predictReviewValue[i]))

        self.infoToMongoDB(f'PRReviewDate/{reviewID}/{degree}', predictReviewDate)
        self.infoToMongoDB(f'PRReviewDateUp/{reviewID}/{degree}/{reviewValueUp}', predictReviewDateUp)
        return

    # Применение Полиномиальной регрессии для распределения пользовательских
    #   отзывов по месяцам для всех фильмов / сериалов
    def polynomialRegressionForReviewInDB(self):
        reviewWindowSize = self.configParameters['reviewWindowSize']
        reviewDegree     = self.configParameters['reviewDegree']
        reviewValueUp    = self.configParameters['reviewValueUp']
        for review in self.collectionReviews.find():
            reviewID           = review['_id']
            reviewDateWWKey    = f'reviewDateWW/{reviewID}/{reviewWindowSize}'
            cursorReviewDateWW = self.collectionAnalytic.find_one({ 'nameParam' : reviewDateWWKey })
            if cursorReviewDateWW is None or len(cursorReviewDateWW['valuesParam']) < 5:
                continue
            
            self.polynomialRegressionForReview(cursorReviewDateWW['valuesParam'],
                                               reviewID, reviewDegree, reviewValueUp)

        return

    # Использование Дерева решений для распределения пользовательских
    #   отзывов по месяцам для конкретного фильма / сериала
    def decisionTreeForReview(self, reviewDate: List[Tuple[dt, int]], 
                              reviewID: int, keyToDB: str):
        
        XTrain, XTest, YTrain, YTest = self.prepareDataToPredict(reviewDate)
        
        regressor          = DecisionTreeRegressor(random_state = 0)
        reviewRegression   = regressor.fit(XTrain, YTrain)
        predictReviewValue = reviewRegression.predict(XTest)

        predictReviewValue = np.append(YTrain, predictReviewValue)
        predictReviewDate  = [(reviewDate[i][0], predictReviewValue[i]) for i in range(len(reviewDate))]

        RMSE    = np.sqrt(mean_squared_error(predictReviewValue, np.append(YTrain, YTest)))
        R2Score = abs(r2_score(predictReviewValue, np.append(YTrain, YTest)))
        
        self.logger.warning(f'decisionTree/{reviewID}/RMSE/{RMSE}')
        self.logger.warning(f'decisionTree/{reviewID}/R2/{R2Score}')

        self.infoToMongoDB(f'{keyToDB}/{reviewID}', predictReviewDate)
        return

    # Применение Дерева решений для распределения пользовательских
    #   отзывов по месяцам для всех фильмов / сериалов
    def decisionTreeForReviewInDB(self):
        reviewWindowSize = self.configParameters['reviewWindowSize']
        for review in self.collectionReviews.find():
            reviewID           = review['_id']
            reviewDateWWKey    = f'reviewDateWW/{reviewID}/{reviewWindowSize}'
            cursorReviewDateWW = self.collectionAnalytic.find_one({ 'nameParam' : reviewDateWWKey })
            if cursorReviewDateWW is None or len(cursorReviewDateWW['valuesParam']) < 5:
                continue
            
            self.decisionTreeForReview(cursorReviewDateWW['valuesParam'], reviewID, 'DTReviewDateWW')
            
            reviewDateKey    = f'reviewDate/{reviewID}'
            cursorReviewDate = self.collectionAnalytic.find_one({ 'nameParam' : reviewDateKey })
            if cursorReviewDate is None or len(cursorReviewDate['valuesParam']) < 5:
                continue
            
            self.decisionTreeForReview(cursorReviewDate['valuesParam'], reviewID, 'DTReviewDate')

        return

    # Построение распределения для Дерева решений, поднятого на некоторое значение,
    #   количества пользовательских оценок по месяцам для конкретного фильма / сериала 
    def decisionTreeUp(self, reviewID: int, valueUp: int,
                       reviewDate: List[Tuple[dt, int]], keyToDB: str):
        
        reviewNewValue = [(review[0], (review[1] + valueUp)) for review in reviewDate]
        self.infoToMongoDB(f'{keyToDB}/{reviewID}/{valueUp}', reviewNewValue)
        return

    # Построение распределения для Дерева решений, поднятого на некоторое значение,
    #   количества пользовательских оценок по месяцам для всех фильмов / сериалов
    def decisionTreeUpToDB(self, valueUp: int):
        for filmReview in self.collectionReviews.find():
            filmID             = filmReview['_id']
            decisionTreeNameWW = f'DTReviewDateWW/{filmID}'
            decisionTreeListWW = self.collectionPredict.find_one({ 'nameParam' : decisionTreeNameWW })
            if decisionTreeListWW is None:
                continue
            
            self.decisionTreeUp(filmReview['_id'], valueUp,
                                decisionTreeListWW['valuesParam'], 'DTReviewDateWWUp')
            
            decisionTreeName = f'DTReviewDate/{filmID}'
            decisionTreeList = self.collectionPredict.find_one({ 'nameParam' : decisionTreeName })
            if decisionTreeList is None:
                continue
            
            self.decisionTreeUp(filmReview['_id'], valueUp,
                                decisionTreeList['valuesParam'], 'DTReviewDateUp')

        return

    # Использование различных видов регрессии для предсказания количества
    #   пользовательских оценок по месяцам для всех фильмов / сериалов 
    def regressionForReview(self):
        self.linearRegressionForReviewInDB()
        self.polynomialRegressionForReviewInDB()
        self.decisionTreeForReviewInDB()
        self.decisionTreeUpToDB(self.configParameters['reviewValueUp'])
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
        self.collectionPredict  = connectionDB[self.configParameters['dataPathPredict']]

        self.regressionForReview()

        return

if __name__ == '__main__':  
    DataPredict().main()