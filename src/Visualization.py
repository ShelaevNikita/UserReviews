#!/usr/bin/env python3

import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output, no_update

from src import DataAnalytics as DA

class VisualizationReviews():
    
    FilterKeys = [
        'Распределение фильмов/сериалов по жанрам',
        'Распределение фильмов/сериалов по странам',
        'Распределение фильмов/сериалов по году производства',       
        'Фильмы/сериалы с самым высоким рейтингом пользователей',
        'Фильмы/сериалы с самой высокой продолжительностью',
        'Актёрский состав с самым высоким рейтингом',
        'Фильмы/сериалы с самым большим количеством отзывов',
        'Распределение отзывов к фильму/сериалу по месяцам',
        'Среднее количество слов в отзыве в зависимости от его класса'
    ]

    def __init__(self, configParameters):
        self.app = Dash(__name__)
        
        self.DataAnalytics    = DA.DataAnalytics(configParameters)
        
        self.indicatorArrDict = {}

    def splitArrToXAndY(self, tupleFromArr, first = 0, second = 1):      
        X = [tupleFrom[first]  for tupleFrom in tupleFromArr]
        Y = [tupleFrom[second] for tupleFrom in tupleFromArr]
        return (X, Y)

    def splitPersonToBar(self, personArr):       
        X      = [person[1] for person in personArr]
        Y      = [person[2] for person in personArr]
        textXY = [f'{person[2]} {person[3]}' for person in personArr]
        return (X, Y, textXY)

    def countFilmReviewInDict(self, reviewJSON):        
        reviewClassArr = self.DataAnalytics.countFilmReview(reviewJSON)

        reviewCount    = sorted(reviewClassArr, key = lambda elem: elem[2], reverse = True)
        reviewPercent  = sorted(reviewClassArr, key = lambda elem: elem[4], reverse = True)
                    
        self.indicatorArrDict[6] = (reviewCount, reviewPercent)
        self.indicatorArrDict[7] = [(elem[0], elem[1]) for elem in self.indicatorArrDict[6][0]]
        return
    
    def takeFilmFromOffset(self, takeElem, reviewJSON):        
        if 6 not in self.indicatorArrDict:
            self.countFilmReviewInDict(reviewJSON)
                
        offsetArr = min(takeElem, len(self.indicatorArrDict[7])) - 1
        return self.indicatorArrDict[7][offsetArr]

    def layout(self, filmJSON, reviewJSON):

        self.app.layout = html.Div([
            html.H1('User reviews for different films and serials',
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
        def updateGraph(takeElem, indicator):

            if (indicator is None or takeElem is None):
                return no_update

            if (indicator == self.FilterKeys[0]):
                if 0 not in self.indicatorArrDict:                   
                    filmGenreArr = self.DataAnalytics.countFilmParam(filmJSON, 'genre')
                    filmGenreArr.sort(key = lambda elem: elem[1], reverse = True)
                    
                    self.indicatorArrDict[0] = filmGenreArr

                X, Y = self.splitArrToXAndY(self.indicatorArrDict[0][:takeElem])

                fig = go.Figure(go.Bar(x = X, y = Y, text = Y, textposition = 'auto'))
                
                fig.update_layout(title = indicator,
                                  yaxis_title = 'Количество фильмов/сериалов',
                                  xaxis_title = 'Название жанра')
            
            elif (indicator == self.FilterKeys[1]):
                if 1 not in self.indicatorArrDict:                  
                    filmCountryArr = self.DataAnalytics.countFilmParam(filmJSON, 'country')
                    filmCountryArr.sort(key = lambda elem: elem[1], reverse = True)
                    
                    self.indicatorArrDict[1] = filmCountryArr

                X, Y = self.splitArrToXAndY(self.indicatorArrDict[1][:takeElem])

                fig = go.Figure(go.Bar(x = X, y = Y, text = Y, textposition = 'auto'))
                
                fig.update_layout(title = indicator,
                                  yaxis_title = 'Количество фильмов/сериалов',
                                  xaxis_title = 'Страна производства')

            elif (indicator == self.FilterKeys[2]):
                if 2 not in self.indicatorArrDict:                   
                    filmYearArr = self.DataAnalytics.countFilmParam(filmJSON, 'year', False)
                    filmYearArr.sort(key = lambda elem: elem[1], reverse = True)
                    
                    self.indicatorArrDict[2] = filmYearArr

                X, Y = self.splitArrToXAndY(self.indicatorArrDict[2][:takeElem])

                fig = go.Figure(go.Bar(x = X, y = Y, text = Y, textposition = 'auto'))
                
                fig.update_layout(title = indicator, yaxis_title = 'Количество фильмов/сериалов')
                
            elif (indicator == self.FilterKeys[3]):
                if 3 not in self.indicatorArrDict:                
                    filmRatingArr = self.DataAnalytics.countFilmRating(filmJSON)
                    
                    filmRatingValue = sorted(filmRatingArr, key = lambda elem: elem[1], reverse = True)
                    filmRatingCount = sorted(filmRatingArr, key = lambda elem: elem[2], reverse = True)

                    self.indicatorArrDict[3] = (filmRatingValue, filmRatingCount)
                
                filmRatingArr = self.indicatorArrDict[3]

                xValue, yValue = self.splitArrToXAndY(filmRatingArr[0][:takeElem])
                xCount, yCount = self.splitArrToXAndY(filmRatingArr[1][:takeElem], second = 2)

                fig = go.Figure([
                    go.Bar(x = xCount, y = yCount, text = yCount,
                           textposition = 'auto', name = 'По количеству'),
                    go.Bar(x = xValue, y = yValue, text = yValue,
                           textposition = 'auto', name = 'По значению')    
                ])
                
                fig.update_layout(barmode = 'stack', title = indicator,
                                  yaxis_title = 'Значение / Количество')

            elif (indicator == self.FilterKeys[4]):
                if 4 not in self.indicatorArrDict:                   
                    movieTimeArr, serialTimeArr = self.DataAnalytics.countFilmTime(filmJSON)
                    movieTimeArr.sort(key = lambda elem: elem[1], reverse = True)

                    serialEpisodesCount = sorted(serialTimeArr, key = lambda elem: elem[1], reverse = True)
                    serialAllTime       = sorted(serialTimeArr, key = lambda elem: elem[2], reverse = True)
                    
                    self.indicatorArrDict[4] = (movieTimeArr, serialEpisodesCount, serialAllTime)

                filmTimeArr = self.indicatorArrDict[4]

                xMovie, yMovie       = self.splitArrToXAndY(filmTimeArr[0][:takeElem])
                xEpisodes, yEpisodes = self.splitArrToXAndY(filmTimeArr[1][:takeElem])
                xAllTime, yAllTime   = self.splitArrToXAndY(filmTimeArr[2][:takeElem], second = 2)

                fig = go.Figure([
                    go.Bar(x = xMovie, y = yMovie, text = yMovie,
                           textposition = 'auto', name = 'Фильмы - Продолжительность'),
                    go.Bar(x = xEpisodes, y = yEpisodes, text = yEpisodes,
                           textposition = 'auto', name = 'Сериалы - Количество серий'),
                    go.Bar(x = xAllTime, y = yAllTime, text = yAllTime,
                           textposition = 'auto', name = 'Сериалы - Общая продолжительность')
                ])
                
                fig.update_layout(barmode = 'stack', title = indicator,
                                  yaxis_title = 'Время / Количество')
            
            elif (indicator == self.FilterKeys[5]):
                if 5 not in self.indicatorArrDict:                  
                    filmProd = self.DataAnalytics.countFilmPerson(filmJSON, 'producer')
                    filmDir  = self.DataAnalytics.countFilmPerson(filmJSON, 'director')
                    filmAct  = self.DataAnalytics.countFilmPerson(filmJSON, 'actor')
                    
                    filmProd.sort(key = lambda elem: elem[2], reverse = True)
                    filmDir.sort( key = lambda elem: elem[2], reverse = True)
                    filmAct.sort( key = lambda elem: elem[2], reverse = True)
                    
                    self.indicatorArrDict[5] = (filmProd, filmDir, filmAct)
                
                filmPersonArr = self.indicatorArrDict[5]

                xProd, yProd, textProd = self.splitPersonToBar(filmPersonArr[0][:takeElem])
                xDir,  yDir,  textDir  = self.splitPersonToBar(filmPersonArr[1][:takeElem])
                xAct,  yAct,  textAct  = self.splitPersonToBar(filmPersonArr[2][:takeElem])

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
                if 6 not in self.indicatorArrDict:
                    self.countFilmReviewInDict(reviewJSON)               
                
                reviewClassArr = self.indicatorArrDict[6]
                
                xCount, yCount = self.splitArrToXAndY(reviewClassArr[0][:takeElem],
                                                      first = 1, second = 2)
                
                xPerc,  yPerc  = self.splitArrToXAndY(reviewClassArr[1][:takeElem],
                                                      first = 1, second = 4)

                fig = go.Figure([
                    go.Bar(x = xCount, y = yCount, text = yCount,
                           textposition = 'auto', name = 'По количеству'),
                    go.Bar(x = xPerc,  y = yPerc,  text = yPerc,
                           textposition = 'auto', name = 'По % положительных')    
                ])
                
                fig.update_layout(barmode = 'group', title = indicator,
                                  yaxis_title = 'Количество / %')

            elif (indicator == self.FilterKeys[7]):                   
                filmID, filmName = self.takeFilmFromOffset(takeElem, reviewJSON)

                reviewDateArr    = self.DataAnalytics.countReviewDate(reviewJSON, filmID)
                reviewDateArr.sort(key = lambda elem: elem[0], reverse = True)

                reviewWithWindow = self.DataAnalytics.reviewDateWithWindow(reviewDateArr)
                reviewPredict    = self.DataAnalytics.fitLinearRegressionForReview(reviewWithWindow)

                initX, initY = self.splitArrToXAndY(reviewDateArr)
                mediX, mediY = self.splitArrToXAndY(reviewWithWindow)
                predX, predY = self.splitArrToXAndY(reviewPredict)

                fig = go.Figure([
                    go.Scatter(x = initX, y = initY, name = 'Исходные данные'),
                    go.Scatter(x = mediX, y = mediY, name = 'Усреднённые данные'),
                    go.Scatter(x = predX, y = predY, name = 'Предсказание')    
                ])
                
                title = 'Распределение отзывов к фильму \"' + filmName + '\" по месяцам'

                fig.update_layout(title = title, yaxis_title = 'Количество отзывов в месяц')
            
            elif (indicator == self.FilterKeys[8]):                                
                filmID, filmName = self.takeFilmFromOffset(takeElem, reviewJSON)

                reviewClass = self.DataAnalytics.reviewLenText(reviewJSON, filmID)
                
                minReviews = [min(reviewClass[i]) for i in range(3)]
                maxReviews = [max(reviewClass[i]) for i in range(3)]
                lenReviews = [len(reviewClass[i]) for i in range(3)]
                
                avgReviews = [round(sum(reviewClass[i]) / lenReviews[i], 1) for i in range(3)]

                X       = ['Положительные', 'Нейтральные', 'Отрицательные']
                Y       = [avgReviews[i] for i in range(3)]
                textXY  = [f'{avgReviews[i]}: от {minReviews[i]} до {maxReviews[i]} из {lenReviews[i]}' for i in range(3)]

                fig = go.Figure(go.Bar(x = X, y = Y, text = textXY, textposition = 'auto'))

                fig.update_layout(title = indicator + ' (\"' + filmName + '\")',
                                  yaxis_title = 'Среднее количество слов в отзыве')

            fig.update_layout(title_x = 0.5, width = 1500, height = 700, autosize = True)
            
            return fig

    def main(self):        
        filmJSON, reviewJSON = self.DataAnalytics.getFilmAndReviewJSON()

        self.layout(filmJSON, reviewJSON)      
        self.app.run_server(host = 'localhost', port = 8050)
        
        return

if __name__ == '__main__':
     VisualizationReviews().main()