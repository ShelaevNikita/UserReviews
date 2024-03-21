#!/usr/bin/env python3

import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output, no_update

from src import DataAnalytics

class VisualizationReviews():
    
    FilterKeys = [
        'Распределение фильмов/сериалов по жанрам',
        'Распределение фильмов/сериалов по странам',
        'Распределение фильмов/сериалов по году производства',       
        'Фильмы/сериалы с самым высоким рейтингом (Top-10)',
        'Фильмы/сериалы с самой высокой продолжительностью (Top-10)',
        'Актёрский состав с самым высоким рейтингом (Top-10)',
        'Фильмы/сериалы с самым большим количеством отзывов (Top-10)'
    ]

    def __init__(self, configParameters):
        
        self.app = Dash(__name__)
        
        self.DataAnalytics = DataAnalytics.DataAnalytics(configParameters)
    
    def splitArrToXAndY(self, arrFromPara):
        
        x = []
        y = []
        
        for para in arrFromPara:
            x.append(para[0])
            y.append(para[1])

        return (x, y)

    def personToBar(self, personArr):
        
        x    = []
        y    = []
        text = []

        for person in personArr:
            x.append(person[1])
            y.append(person[2])
            text.append(f'{person[2]} {person[3]}')

        return (x, y, text)

    def layout(self, filmJSON, reviewJSON):

        self.app.layout = html.Div([
            html.H1('User reviews for different films and serials', style = {'textAlign':'center'}),
            html.Hr(),
            html.Div([
                dcc.Dropdown(
                    self.FilterKeys,
                    self.FilterKeys[0],
                    id = 'indicator'
                )], style = {
                    'width'     : '100%',                    
                    'position'  : 'relative',
                    'display'   : 'inline-block',
                    'textAlign' : 'center'
                }),
            dcc.Graph(id = 'graph'),
        ])

        @self.app.callback(
            Output('graph', 'figure'),
            Input('indicator', 'value'))
        def updateGraph(indicator):

            if (indicator == self.FilterKeys[0]):

                filmGenreArr = self.DataAnalytics.countFilmParam(filmJSON, 'genre')

                x, y = self.splitArrToXAndY(filmGenreArr)

                fig = go.Figure(data = go.Bar(x = x, y = y, text = y, textposition = 'auto'))
                
                fig.update_layout(title = indicator,
                                  yaxis_title = 'Количество фильмов/сериалов',
                                  xaxis_title = 'Название жанра')
            
            elif (indicator == self.FilterKeys[1]):

                filmCountryArr = self.DataAnalytics.countFilmParam(filmJSON, 'country')

                x, y = self.splitArrToXAndY(filmCountryArr)

                fig = go.Figure(data = go.Bar(x = x, y = y, text = y, textposition = 'auto'))
                
                fig.update_layout(title = indicator,
                                  yaxis_title = 'Количество фильмов/сериалов',
                                  xaxis_title = 'Страна производства')

            elif (indicator == self.FilterKeys[2]):

                filmYearArr = self.DataAnalytics.countFilmParam(filmJSON, 'year', False)

                x, y = self.splitArrToXAndY(filmYearArr)

                fig = go.Figure(data = go.Bar(x = x, y = y, text = y, textposition = 'auto'))
                
                fig.update_layout(title = indicator,
                                  yaxis_title = 'Количество фильмов/сериалов')
                
            elif (indicator == self.FilterKeys[3]):

                filmRatingArr = self.DataAnalytics.sortFilmByRating(filmJSON)

                xValue, yValue = self.splitArrToXAndY(filmRatingArr[0][:10])
                xCount, yCount = self.splitArrToXAndY(filmRatingArr[1][:10])

                fig = go.Figure(data = [
                    go.Bar(x = xCount, y = yCount, text = yCount,
                           textposition = 'auto', name = 'По количеству'),
                    go.Bar(x = xValue, y = yValue, text = yValue,
                           textposition = 'auto', name = 'По значению')    
                ])
                
                fig.update_layout(barmode = 'stack', title = indicator,
                                  yaxis_title = 'Значение / Количество')
                
            elif (indicator == self.FilterKeys[4]):

                filmTimeArr = self.DataAnalytics.sortFilmByTime(filmJSON)

                xMovie, yMovie       = self.splitArrToXAndY(filmTimeArr[0][:10])
                xEpisodes, yEpisodes = self.splitArrToXAndY(filmTimeArr[1][:10])
                xAllTime, yAllTime   = self.splitArrToXAndY(filmTimeArr[2][:10])

                fig = go.Figure(data = [
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

                filmProd = self.DataAnalytics.filmPerson(filmJSON, 'producer')
                filmDir  = self.DataAnalytics.filmPerson(filmJSON, 'director')
                filmAct  = self.DataAnalytics.filmPerson(filmJSON, 'actor')               

                xProd, yProd, textProd = self.personToBar(filmProd[:10])
                xDir,  yDir,  textDir  = self.personToBar(filmDir [:10])
                xAct,  yAct,  textAct  = self.personToBar(filmAct [:10])

                fig = go.Figure(data = [
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

                reviewClassArr = self.DataAnalytics.sortReviewByCount(reviewJSON)

                xCount, yCount = self.splitArrToXAndY(reviewClassArr[0][:10])
                xPerc,  yPerc  = self.splitArrToXAndY(reviewClassArr[1][:10])

                fig = go.Figure(data = [
                    go.Bar(x = xCount, y = yCount, text = yCount,
                           textposition = 'auto', name = 'По количеству'),
                    go.Bar(x = xPerc,  y = yPerc,  text = yPerc,
                           textposition = 'auto', name = 'По % положительных')    
                ])
                
                fig.update_layout(barmode = 'group', title = indicator,
                                  yaxis_title = 'Количество / %')

            else:
                return no_update

            fig.update_layout(title_x = 0.5, width = 1500, height = 700, autosize = True)
            
            return fig

    def main(self):
        
        filmJSON, reviewJSON = self.DataAnalytics.getFilmAndReviewJSON()
        
        self.DataAnalytics.fillFilmIDAndName(filmJSON)

        self.layout(filmJSON, reviewJSON)
        
        self.app.run_server(host = 'localhost', port = 8050)
        
        return

if __name__ == '__main__':
     VisualizationReviews().main()