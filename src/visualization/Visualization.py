#!/usr/bin/env python3

import plotly.graph_objects as go
import logging

from typing            import List, Union, Any, Tuple
from dash              import Dash, dcc, html, Input, Output, no_update
from pymongo           import MongoClient
from pymemcache.client import base

# Класс для визуализации полученных и обработанных
#   данных, находящихся в MongoDB
class VisualizationReviews():
    
    # Значения конфигурационного файла по умолчанию
    DefaultConfigParameters = {
        'pathMongoDB'      : 'mongodb://localhost:27017/',
        'databaseName'     : 'userReviews',
        'dataPathAnalytic' : 'analytic',
        'dataPathPredict'  : 'predict',
        'reviewWindowSize' : 5,
        'reviewValueUp'    : 5,
        'lastDays'         : 15,
        'timeCache'        : 60
    }

    # Значения ключей для отображения требуемой информации
    FilterKeys = [
        'Распределение фильмов/сериалов по жанрам',
        'Распределение фильмов/сериалов по странам',
        'Распределение фильмов/сериалов по году производства',       
        'Фильмы/сериалы с самым высоким рейтингом пользователей',
        'Фильмы/сериалы с самой высокой продолжительностью',
        'Актёрский состав с самым высоким рейтингом',
        'Фильмы/сериалы с самым большим количеством отзывов',
        'Среднее количество слов в отзыве в зависимости от его класса',
        'Распределение отзывов к фильму/сериалу по месяцам',
        'Линейная регрессия для распределения отзывов к фильму/сериалу по месяцам',
        'Полиномиальная регрессия для распределения отзывов к фильму/сериалу по месяцам',
        'Дерево решений для распределения отзывов к фильму/сериалу по месяцам',
        'Случайный лес для распределения отзывов к фильму/сериалу по месяцам',
        'Градиентный бустинг для распределения отзывов к фильму/сериалу по месяцам',
        'Распределение отзывов к фильму/сериалу за последние N дней (1-3)',
        'Распределение отзывов к фильму/сериалу за последние N дней (4-5)'
    ]

    # Инициализация класса
    def __init__(self):
        self.app = Dash('UserReviews')
        
        self.configFile         = './src/visualization/visualizationConfigFile.txt'   
        self.configParameters   = self.DefaultConfigParameters
        
        self.collectionAnalytic = None
        self.collectionPredict  = None
        
        self.innerCache = {}
        #self.memClient = base.Client('localhost:11211')
        
        logging.basicConfig(
            filename = './log/visualization.log',
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
            self.logger.error('Not found config file for Visualization!')
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

    # Разделение полученных данных на 2 координаты
    def splitArrToXAndY(self, tupleList: List[Any], first = 0, second = 1) -> Tuple[List[Any], List[Any]]:
        X = []
        Y = []
        for elem in tupleList:
            X.append(elem[first])
            Y.append(elem[second])

        return (X, Y)

    # Разделение полученных данных о съёмочной группе на 2 координаты и описание
    def splitPersonToBar(self, personList: List[Any]) -> Tuple[List[str], List[float], List[str]]:
        X      = []
        Y      = []
        textXY = []
        for person in personList:
            X.append(person[1])
            Y.append(person[2])
            textXY.append(f'{person[2]} {person[3]}')

        return (X, Y, textXY)
    
    # Поиск записей по ключу в Memcached и в MongoDB
    def getCursorFromCacheDB(self, findKey: str, flagAnalytic = True) -> Union[Any, None]:
        # cursors = self.memClient.get(findKey)
        cursors   = self.innerCache.get(findKey, None)        
        if cursors is None:
            if flagAnalytic:
                cursors = self.collectionAnalytic.find_one({ 'nameParam' : findKey })
             
            else:
                cursors = self.collectionPredict.find_one({ 'nameParam' : findKey })

            if cursors is None:
                return
            
            self.innerCache[findKey] = cursors
            #self.memClient.set(findKey, cursors, expire = self.configParameters['timeCache'])

        return cursors['valuesParam']

    def layout(self):
        self.app.layout = html.Div([
            html.H1('Сервис для определения степени объективности пользовательского рейтинга',
                    style = {'textAlign':'center'}),                    
            html.Hr(),            
            html.Div([                
                html.Div([    
                    dcc.Dropdown(
                        self.FilterKeys,
                        self.FilterKeys[0],
                        id = 'indicator'
                    )], style = {
                        'width'     : '100%',                    
                        'position'  : 'relative',
                        'display'   : 'inline-block',
                        'textAlign' : 'center',
                        'padding'   : 35,
                        'flex'      : 5
                    }),
                html.Div([
                    html.Label('Top-'),
                    dcc.Input(
                        id    = 'count',
                        type  = 'number',
                        value = 10,
                        min   = 1,
                        max   = 25,
                        step  = 1,
                        style = {'textAlign':'center', 'font-size':'large'},
                    )], style = {'padding':40, 'flex':1})                              
            ], style = {'display':'flex', 'flexDirection':'row'}),
            dcc.Graph(id = 'graph'),
        ])

        @self.app.callback(
            Output('graph', 'figure'),
            Input('count', 'value'),
            Input('indicator', 'value'))
        def updateGraph(takeElem: int, indicator: str):
            if (indicator is None or takeElem is None):
                return no_update

            if (indicator == self.FilterKeys[0]):
                filmGenres = self.getCursorFromCacheDB('genres')
                if filmGenres is None:
                    return no_update

                X, Y = self.splitArrToXAndY(filmGenres[:takeElem])

                fig = go.Figure(go.Bar(x = X, y = Y, text = Y, textposition = 'auto'))
                fig.update_layout(title = indicator,
                                  yaxis_title = 'Количество фильмов/сериалов',
                                  xaxis_title = 'Название жанра')
            
            elif (indicator == self.FilterKeys[1]):
                filmCountry = self.getCursorFromCacheDB('countries')
                if filmCountry is None:
                    return no_update

                X, Y = self.splitArrToXAndY(filmCountry[:takeElem])

                fig = go.Figure(go.Bar(x = X, y = Y, text = Y, textposition = 'auto'))                
                fig.update_layout(title = indicator,
                                  yaxis_title = 'Количество фильмов/сериалов',
                                  xaxis_title = 'Страна производства')

            elif (indicator == self.FilterKeys[2]):
                filmYear = self.getCursorFromCacheDB('year')
                if filmYear is None:
                    return no_update

                X, Y = self.splitArrToXAndY(filmYear[:takeElem])

                fig = go.Figure(go.Bar(x = X, y = Y, text = Y, textposition = 'auto'))                
                fig.update_layout(title = indicator, yaxis_title = 'Количество фильмов/сериалов')
                
            elif (indicator == self.FilterKeys[3]):
                filmRating = self.getCursorFromCacheDB('filmRating')
                if filmRating is None:
                    return no_update

                xValue, yValue = self.splitArrToXAndY(filmRating[0][:takeElem])
                xCount, yCount = self.splitArrToXAndY(filmRating[1][:takeElem], second = 2)

                fig = go.Figure([
                    go.Bar(x = xCount, y = yCount, text = yCount,
                           textposition = 'auto', name = 'По количеству'),
                    go.Bar(x = xValue, y = yValue, text = yValue,
                           textposition = 'auto', name = 'По значению')    
                ])                
                fig.update_layout(barmode = 'stack', title = indicator,
                                  yaxis_title = 'Значение / Количество')

            elif (indicator == self.FilterKeys[4]):
                filmTime = self.getCursorFromCacheDB('filmTime')
                if filmTime is None:
                    return no_update

                xTime, yTime         = self.splitArrToXAndY(filmTime[0][:takeElem])
                xEpisodes, yEpisodes = self.splitArrToXAndY(filmTime[1][:takeElem], second = 2)
                xAllTime, yAllTime   = self.splitArrToXAndY(filmTime[2][:takeElem], second = 3)

                fig = go.Figure([
                    go.Bar(x = xTime, y = yTime, text = yTime,
                           textposition = 'auto', name = 'Продолжительность фильма или 1-й серии сериала'),
                    go.Bar(x = xEpisodes, y = yEpisodes, text = yEpisodes,
                           textposition = 'auto', name = 'Количество серий'),
                    go.Bar(x = xAllTime, y = yAllTime, text = yAllTime,
                           textposition = 'auto', name = 'Общая продолжительность')
                ])               
                fig.update_layout(barmode = 'stack', title = indicator,
                                  yaxis_title = 'Время / Количество')
            
            elif (indicator == self.FilterKeys[5]):
                filmProd = self.getCursorFromCacheDB('producers')
                filmDirs = self.getCursorFromCacheDB('directors')
                filmActs = self.getCursorFromCacheDB('actors')
                if filmProd is None or filmDirs is None or filmActs is None:
                    return no_update

                xProd, yProd, textProd = self.splitPersonToBar(filmProd[:takeElem])
                xDir,  yDir,  textDir  = self.splitPersonToBar(filmDirs[:takeElem])
                xAct,  yAct,  textAct  = self.splitPersonToBar(filmActs[:takeElem])

                fig = go.Figure([
                    go.Bar(x = xProd, y = yProd, text = textProd,
                           textposition = 'auto', name = 'Продюсеры'),
                    go.Bar(x = xDir,  y = yDir,  text = textDir,
                           textposition = 'auto', name = 'Режиссеры'),
                    go.Bar(x = xAct,  y = yAct,  text = textAct,
                           textposition = 'auto', name = 'Актеры / Актриссы')
                ])               
                fig.update_layout(barmode = 'group', title = indicator,
                                  yaxis_title = 'Рейтинг')
            
            elif (indicator == self.FilterKeys[6]):
                reviewCount = self.getCursorFromCacheDB('reviewCount')
                if reviewCount is None:
                    return no_update

                xCount, yCount = self.splitArrToXAndY(reviewCount[0][:takeElem], first = 1, second = 2)               
                xPerc,  yPerc  = self.splitArrToXAndY(reviewCount[1][:takeElem], first = 1, second = 3)

                fig = go.Figure([
                    go.Bar(x = xCount, y = yCount, text = yCount,
                           textposition = 'auto', name = 'По количеству'),
                    go.Bar(x = xPerc,  y = yPerc,  text = yPerc,
                           textposition = 'auto', name = 'По % положительных')    
                ])                
                fig.update_layout(barmode = 'group', title = indicator,
                                  yaxis_title = 'Количество / %')
            
            elif (indicator == self.FilterKeys[7]):
                reviewCount = self.getCursorFromCacheDB('reviewCount')
                if reviewCount is None:
                    return no_update
                
                reviewID = reviewCount[0][(min(takeElem, len(reviewCount[0])) - 1)][0]
                
                reviewClass = self.getCursorFromCacheDB(f'reviewLenText/{reviewID}')
                if reviewClass is None:
                    return no_update

                minReviews  = [min(reviewClass[i]) for i in range(3)]
                maxReviews  = [max(reviewClass[i]) for i in range(3)]
                lenReviews  = [len(reviewClass[i]) for i in range(3)]
                
                X      = ['Положительные', 'Нейтральные', 'Отрицательные']
                Y      = [round(sum(reviewClass[i]) / lenReviews[i], 1) for i in range(3)]
                textXY = [f'{Y[i]}: от {minReviews[i]} до {maxReviews[i]} из {lenReviews[i]}' for i in range(3)]

                fig = go.Figure(go.Bar(x = X, y = Y, text = textXY, textposition = 'auto'))

                fig.update_layout(title = indicator + f' для фильма / сериала с ID {reviewID}',
                                  yaxis_title = 'Среднее количество слов в отзыве')

            elif (indicator == self.FilterKeys[8]):
                reviewCount = self.getCursorFromCacheDB('reviewCount')
                if reviewCount is None:
                    return no_update

                reviewID          = reviewCount[0][(min(takeElem, len(reviewCount[0])) - 1)][0]
                
                reviewWindowSize  = self.configParameters['reviewWindowSize']
                reviewValueUp     = self.configParameters['reviewValueUp']
                
                reviewDateWWKey   = f'reviewDateWW/{reviewID}/{reviewWindowSize}'
                reviewDateWWUpkey = f'reviewDateWWUp/{reviewID}/{reviewValueUp}'
                
                reviewDate     = self.getCursorFromCacheDB(f'reviewDate/{reviewID}')
                reviewDateWW   = self.getCursorFromCacheDB(reviewDateWWKey)
                reviewDateWWUp = self.getCursorFromCacheDB(reviewDateWWUpkey)
                
                if reviewDate is None or reviewDateWW is None or reviewDateWWUp is None:
                    return no_update

                initX, initY = self.splitArrToXAndY(reviewDate)
                mediX, mediY = self.splitArrToXAndY(reviewDateWW)
                meUpX, meUpY = self.splitArrToXAndY(reviewDateWWUp)

                fig = go.Figure([
                    go.Scatter(x = initX, y = initY, name = 'Исходные данные'),
                    go.Scatter(x = mediX, y = mediY, name = 'Медианная фильтрация'),
                    go.Scatter(x = meUpX, y = meUpY, name = 'Медиана, поднятая на K')    
                ])                
                title = f'Распределение отзывов к фильму c ID {reviewID} по месяцам'
                fig.update_layout(title = title, yaxis_title = 'Количество отзывов в месяц')
            
            elif (indicator == self.FilterKeys[9]):
                reviewCount = self.getCursorFromCacheDB('reviewCount')
                if reviewCount is None:
                    return no_update

                reviewID      = reviewCount[0][(min(takeElem, len(reviewCount[0])) - 1)][0]
                
                reviewValueUp = self.configParameters['reviewValueUp']

                LRpredictDateKey   = f'LRReviewDate/{reviewID}'
                LRpredictDateKeyUp = f'LRReviewDateUp/{reviewID}/{reviewValueUp}'
                
                reviewDate      = self.getCursorFromCacheDB(f'reviewDate/{reviewID}')
                LRpredictDate   = self.getCursorFromCacheDB(LRpredictDateKey, False)
                LRpredictDateUp = self.getCursorFromCacheDB(LRpredictDateKeyUp, False)
                
                if reviewDate is None or LRpredictDate is None or LRpredictDateUp is None:
                    return no_update

                initX, initY = self.splitArrToXAndY(reviewDate)
                mediX, mediY = self.splitArrToXAndY(LRpredictDate)
                meUpX, meUpY = self.splitArrToXAndY(LRpredictDateUp)

                fig = go.Figure([
                    go.Scatter(x = initX, y = initY, name = 'Исходные данные'),
                    go.Scatter(x = mediX, y = mediY, name = 'Линейная регрессия'),
                    go.Scatter(x = meUpX, y = meUpY, name = 'Линейная регрессия с K-уровнем')    
                ])                
                title = f'Распределение отзывов к фильму c ID {reviewID} по месяцам'
                fig.update_layout(title = title, yaxis_title = 'Количество отзывов в месяц')
            
            elif (indicator == self.FilterKeys[10]):
                reviewCount = self.getCursorFromCacheDB('reviewCount')
                if reviewCount is None:
                    return no_update

                reviewID      = reviewCount[0][(min(takeElem, len(reviewCount[0])) - 1)][0]
                
                reviewValueUp = self.configParameters['reviewValueUp']

                PRpredictDateKey   = f'PRReviewDate/{reviewID}'
                PRpredictDateKeyUp = f'PRReviewDateUp/{reviewID}/{reviewValueUp}'
                
                reviewDate      = self.getCursorFromCacheDB(f'reviewDate/{reviewID}')
                PRpredictDate   = self.getCursorFromCacheDB(PRpredictDateKey, False)
                PRpredictDateUp = self.getCursorFromCacheDB(PRpredictDateKeyUp, False)
                
                if reviewDate is None or PRpredictDate is None or PRpredictDateUp is None:
                    return no_update

                initX, initY = self.splitArrToXAndY(reviewDate)
                mediX, mediY = self.splitArrToXAndY(PRpredictDate)
                meUpX, meUpY = self.splitArrToXAndY(PRpredictDateUp)

                fig = go.Figure([
                    go.Scatter(x = initX, y = initY, name = 'Исходные данные'),
                    go.Scatter(x = mediX, y = mediY, name = 'Полиномиальная регрессия'),
                    go.Scatter(x = meUpX, y = meUpY, name = 'Полиномиальная регрессия c K-уровнем')
                ])                
                title = f'Распределение отзывов к фильму c ID {reviewID} по месяцам'
                fig.update_layout(title = title, yaxis_title = 'Количество отзывов в месяц')

            elif (indicator == self.FilterKeys[11]):
                reviewCount = self.getCursorFromCacheDB('reviewCount')
                if reviewCount is None:
                    return no_update

                reviewID      = reviewCount[0][(min(takeElem, len(reviewCount[0])) - 1)][0]

                reviewValueUp = self.configParameters['reviewValueUp']

                DTpredictDateKey     = f'DTReviewDate/{reviewID}'
                DTpredictDateWWKey   = f'DTReviewDateWW/{reviewID}'
                DTpredictDateUpKey   = f'DTReviewDateUp/{reviewID}/{reviewValueUp}'
                DTpredictDateWWUpKey = f'DTReviewDateWWUp/{reviewID}/{reviewValueUp}'
                
                reviewDate        = self.getCursorFromCacheDB(f'reviewDate/{reviewID}')
                DTpredictDate     = self.getCursorFromCacheDB(DTpredictDateKey, False)
                DTpredictDateWW   = self.getCursorFromCacheDB(DTpredictDateWWKey, False)
                DTpredictDateUp   = self.getCursorFromCacheDB(DTpredictDateUpKey, False)
                DTpredictDateWWUp = self.getCursorFromCacheDB(DTpredictDateWWUpKey, False)
                
                if reviewDate is None or DTpredictDate is None or DTpredictDateWW is None or \
                        DTpredictDateUp is None or DTpredictDateWWUp is None:
                    return no_update

                initX,   initY   = self.splitArrToXAndY(reviewDate)
                DTX,     DTY     = self.splitArrToXAndY(DTpredictDate)
                DTWWX,   DTWWY   = self.splitArrToXAndY(DTpredictDateWW)
                DTUpX,   DTUpY   = self.splitArrToXAndY(DTpredictDateUp)
                DTWWUpX, DTWWUpY = self.splitArrToXAndY(DTpredictDateWWUp)

                fig = go.Figure([
                    go.Scatter(x = initX,   y = initY,   name = 'Исходные данные'),
                    go.Scatter(x = DTX,     y = DTY,     name = 'Дерево решений на исходных данных'),
                    go.Scatter(x = DTWWX,   y = DTWWY,   name = 'Дерево решений на медианных данных'),
                    go.Scatter(x = DTUpX,   y = DTUpY,   name = 'Дерево решений на исходных данных, поднятое на K'),
                    go.Scatter(x = DTWWUpX, y = DTWWUpY, name = 'Дерево решений на медианных данных, поднятое на K')
                ])                
                title = f'Распределение отзывов к фильму c ID {reviewID} по месяцам'
                fig.update_layout(title = title, yaxis_title = 'Количество отзывов в месяц')
            
            elif (indicator == self.FilterKeys[12]):
                reviewCount = self.getCursorFromCacheDB('reviewCount')
                if reviewCount is None:
                    return no_update

                reviewID = reviewCount[0][(min(takeElem, len(reviewCount[0])) - 1)][0]

                reviewValueUp      = self.configParameters['reviewValueUp']

                RFpredictDateKey     = f'RFReviewDate/{reviewID}'
                RFpredictDateWWKey   = f'RFReviewDateWW/{reviewID}'
                RFpredictDateUpKey   = f'RFReviewDateUp/{reviewID}/{reviewValueUp}'
                RFpredictDateWWUpKey = f'RFReviewDateWWUp/{reviewID}/{reviewValueUp}'
                
                reviewDate        = self.getCursorFromCacheDB(f'reviewDate/{reviewID}')
                RFpredictDate     = self.getCursorFromCacheDB(RFpredictDateKey, False)
                RFpredictDateWW   = self.getCursorFromCacheDB(RFpredictDateWWKey, False)
                RFpredictDateUp   = self.getCursorFromCacheDB(RFpredictDateUpKey, False)
                RFpredictDateWWUp = self.getCursorFromCacheDB(RFpredictDateWWUpKey, False)
                
                if reviewDate is None or RFpredictDate is None or RFpredictDateWW is None or \
                        RFpredictDateUp is None or RFpredictDateWWUp is None:
                    return no_update

                initX,   initY   = self.splitArrToXAndY(reviewDate)
                RFX,     RFY     = self.splitArrToXAndY(RFpredictDate)
                RFWWX,   RFWWY   = self.splitArrToXAndY(RFpredictDateWW)
                RFUpX,   RFUpY   = self.splitArrToXAndY(RFpredictDateUp)
                RFWWUpX, RFWWUpY = self.splitArrToXAndY(RFpredictDateWWUp)

                fig = go.Figure([
                    go.Scatter(x = initX,   y = initY,   name = 'Исходные данные'),
                    go.Scatter(x = RFX,     y = RFY,     name = 'Случайный лес на исходных данных'),
                    go.Scatter(x = RFWWX,   y = RFWWY,   name = 'Случайный лес на медианных данных'),
                    go.Scatter(x = RFUpX,   y = RFUpY,   name = 'Случайный лес на исходных данных, поднятый на K'),
                    go.Scatter(x = RFWWUpX, y = RFWWUpY, name = 'Случайный лес на медианных данных, поднятый на K')
                ])                
                title = f'Распределение отзывов к фильму c ID {reviewID} по месяцам'
                fig.update_layout(title = title, yaxis_title = 'Количество отзывов в месяц')
            
            elif (indicator == self.FilterKeys[13]):
                reviewCount = self.getCursorFromCacheDB('reviewCount')
                if reviewCount is None:
                    return no_update

                reviewID      = reviewCount[0][(min(takeElem, len(reviewCount[0])) - 1)][0]

                reviewValueUp = self.configParameters['reviewValueUp']

                GBpredictDateKey     = f'GBReviewDate/{reviewID}'
                GBpredictDateWWKey   = f'GBReviewDateWW/{reviewID}'
                GBpredictDateUpKey   = f'GBReviewDateUp/{reviewID}/{reviewValueUp}'
                GBpredictDateWWUpKey = f'GBReviewDateWWUp/{reviewID}/{reviewValueUp}'
                
                reviewDate        = self.getCursorFromCacheDB(f'reviewDate/{reviewID}')
                GBpredictDate     = self.getCursorFromCacheDB(GBpredictDateKey, False)
                GBpredictDateWW   = self.getCursorFromCacheDB(GBpredictDateWWKey, False)
                GBpredictDateUp   = self.getCursorFromCacheDB(GBpredictDateUpKey, False)
                GBpredictDateWWUp = self.getCursorFromCacheDB(GBpredictDateWWUpKey, False)
                
                if reviewDate is None or GBpredictDate is None or GBpredictDateWW is None or \
                        GBpredictDateUp is None or GBpredictDateWWUp is None:
                    return no_update

                initX,   initY   = self.splitArrToXAndY(reviewDate)
                GBX,     GBY     = self.splitArrToXAndY(GBpredictDate)
                GBWWX,   GBWWY   = self.splitArrToXAndY(GBpredictDateWW)
                GBUpX,   GBUpY   = self.splitArrToXAndY(GBpredictDateUp)
                GBWWUpX, GBWWUpY = self.splitArrToXAndY(GBpredictDateWWUp)

                fig = go.Figure([
                    go.Scatter(x = initX,   y = initY,   name = 'Исходные данные'),
                    go.Scatter(x = GBX,     y = GBY,     name = 'Градиентный бустинг на исходных данных'),
                    go.Scatter(x = GBWWX,   y = GBWWY,   name = 'Градиентный бустинг на медианных данных'),
                    go.Scatter(x = GBUpX,   y = GBUpY,   name = 'Градиентный бустинг на исходных данных, поднятый на K'),
                    go.Scatter(x = GBWWUpX, y = GBWWUpY, name = 'Градиентный бустинг на медианных данных, поднятый на K')
                ])                
                title = f'Распределение отзывов к фильму c ID {reviewID} по месяцам'
                fig.update_layout(title = title, yaxis_title = 'Количество отзывов в месяц')

            elif (indicator == self.FilterKeys[14]):
                reviewCount = self.getCursorFromCacheDB('reviewCount')
                if reviewCount is None:
                    return no_update

                reviewID      = reviewCount[0][(min(takeElem, len(reviewCount[0])) - 1)][0]
                
                reviewValueUp = self.configParameters['reviewValueUp']
                
                reviewDateWWUpKey    = f'reviewDateWWUp/{reviewID}/{reviewValueUp}'
                LRpredictDateUpKey   = f'LRReviewDateUp/{reviewID}/{reviewValueUp}'
                PRpredictDateUpKey   = f'PRReviewDateUp/{reviewID}/{reviewValueUp}'
                DTpredictDateUpKey   = f'DTReviewDateUp/{reviewID}/{reviewValueUp}'
                DTpredictDateWWUpKey = f'DTReviewDateWWUp/{reviewID}/{reviewValueUp}'

                reviewDateDay     = self.getCursorFromCacheDB(f'reviewDateDay/{reviewID}')
                reviewDateWWUp    = self.getCursorFromCacheDB(reviewDateWWUpKey)
                LRpredictDateUp   = self.getCursorFromCacheDB(LRpredictDateUpKey, False)
                PRpredictDateUp   = self.getCursorFromCacheDB(PRpredictDateUpKey, False)
                DTpredictDateUp   = self.getCursorFromCacheDB(DTpredictDateUpKey, False)
                DTpredictDateWWUp = self.getCursorFromCacheDB(DTpredictDateWWUpKey, False)

                if reviewDateDay is None or reviewDateWWUp is None or LRpredictDateUp is None or \
                         PRpredictDateUp is None or DTpredictDateUp is None or DTpredictDateWWUp is None:
                    return no_update

                initX, initY = self.splitArrToXAndY(reviewDateDay[-self.configParameters['lastDays']:])
                mediY        = [reviewDateWWUp[-1][1]]    * self.configParameters['lastDays']
                LRpredY      = [LRpredictDateUp[-1][1]]   * self.configParameters['lastDays']
                PRpredY      = [PRpredictDateUp[-1][1]]   * self.configParameters['lastDays']
                DTpredY      = [DTpredictDateUp[-1][1]]   * self.configParameters['lastDays']
                DTpredWWY    = [DTpredictDateWWUp[-1][1]] * self.configParameters['lastDays']

                fig = go.Figure([
                    go.Scatter(x = initX, y = initY,     name = 'Исходные данные'),
                    go.Scatter(x = initX, y = mediY,     name = 'Медиана, поднятая на K'),
                    go.Scatter(x = initX, y = LRpredY,   name = 'Линейная регрессия с K-уровнем'),
                    go.Scatter(x = initX, y = PRpredY,   name = 'Полиномиальная регрессия с K-уровнем'),
                    go.Scatter(x = initX, y = DTpredY,   name = 'Дерево решений на исходных данных, поднятое на K'),
                    go.Scatter(x = initX, y = DTpredWWY, name = 'Дерево решений на медианных данных, поднятое на K')
                ])                
                title = f'Распределение отзывов к фильму c ID {reviewID} за последние N дней'
                fig.update_layout(title = title, yaxis_title = 'Количество отзывов в день')

            elif (indicator == self.FilterKeys[15]):
                reviewCount = self.getCursorFromCacheDB('reviewCount')
                if reviewCount is None:
                    return no_update

                reviewID      = reviewCount[0][(min(takeElem, len(reviewCount[0])) - 1)][0]
                
                reviewValueUp = self.configParameters['reviewValueUp']
                
                reviewDateWWUpKey    = f'reviewDateWWUp/{reviewID}/{reviewValueUp}'
                RFpredictDateUpKey   = f'RFReviewDateUp/{reviewID}/{reviewValueUp}'
                RFpredictDateWWUpKey = f'RFReviewDateWWUp/{reviewID}/{reviewValueUp}'
                GBpredictDateUpKey   = f'GBReviewDateUp/{reviewID}/{reviewValueUp}'
                GBpredictDateWWUpKey = f'GBReviewDateWWUp/{reviewID}/{reviewValueUp}'

                reviewDateDay     = self.getCursorFromCacheDB(f'reviewDateDay/{reviewID}')
                reviewDateWWUp    = self.getCursorFromCacheDB(reviewDateWWUpKey)
                RFpredictDateUp   = self.getCursorFromCacheDB(RFpredictDateUpKey, False)
                RFpredictDateWWUp = self.getCursorFromCacheDB(RFpredictDateWWUpKey, False)
                GBpredictDateUp   = self.getCursorFromCacheDB(GBpredictDateUpKey, False)
                GBpredictDateWWUp = self.getCursorFromCacheDB(GBpredictDateWWUpKey, False)

                if reviewDateDay is None or reviewDateWWUp is None or RFpredictDateUp is None or \
                         RFpredictDateWWUp is None or GBpredictDateUp is None or GBpredictDateWWUp is None:
                    return no_update

                initX, initY = self.splitArrToXAndY(reviewDateDay[-self.configParameters['lastDays']:])
                mediY        = [reviewDateWWUp[-1][1]]    * self.configParameters['lastDays']
                RFpredY      = [RFpredictDateUp[-1][1]]   * self.configParameters['lastDays']
                RFpredWWY    = [RFpredictDateWWUp[-1][1]] * self.configParameters['lastDays']
                GBpredY      = [GBpredictDateUp[-1][1]]   * self.configParameters['lastDays']
                GBpredWWY    = [GBpredictDateWWUp[-1][1]] * self.configParameters['lastDays']

                fig = go.Figure([
                    go.Scatter(x = initX, y = initY,     name = 'Исходные данные'),
                    go.Scatter(x = initX, y = mediY,     name = 'Медиана, поднятая на K'),
                    go.Scatter(x = initX, y = RFpredY,   name = 'Случайный лес на исходный данных, поднятый на K'),
                    go.Scatter(x = initX, y = RFpredWWY, name = 'Случайный лес на медианных данных, поднятый на K'),
                    go.Scatter(x = initX, y = GBpredY,   name = 'Градиентный бустинг на исходных данных, поднятый на K'),
                    go.Scatter(x = initX, y = GBpredWWY, name = 'Градиентный бустинг на медианных данных, поднятый на K')
                ])                
                title = f'Распределение отзывов к фильму c ID {reviewID} за последние N дней'
                fig.update_layout(title = title, yaxis_title = 'Количество отзывов в день')

            fig.update_layout(title_x = 0.5, width = 1500, height = 700, autosize = True)            
            return fig

    def main(self):        
        self.splitConfigFile()
        
        mongoClient = self.connectionToMongoDB()
        if mongoClient is None:
            return
        
        connectionDB            =  mongoClient[self.configParameters['databaseName']]
        self.collectionAnalytic = connectionDB[self.configParameters['dataPathAnalytic']]
        self.collectionPredict  = connectionDB[self.configParameters['dataPathPredict']]

        self.layout()
        self.app.run_server(host = 'localhost', port = 8050)
        
        return

if __name__ == '__main__':
     VisualizationReviews().main()