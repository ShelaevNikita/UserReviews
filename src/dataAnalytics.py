#!/usr/bin/env python3

from audioop import reverse
import json
from re import S

class DataAnalytics(object):
    
    def __init__(self, configParameters):
        
        self.dataPathFilms   = configParameters['dataPathFilms']
        self.dataPathReviews = configParameters['dataPathReviews']

    def getJSONFromFile(self, dataPath):
        
        try:
            with open(dataPath, 'r', encoding = 'utf-8') as file:
                return json.loads(file.read(), strict = False)
                
        except FileNotFoundError:
            print(f'\n Error: Not found file \"{dataPath}\"!')
            return None
    
    def getFilmAndReviewJSON(self):
        filmJSON   = self.getJSONFromFile(self.dataPathFilms)
        reviewJSON = self.getJSONFromFile(self.dataPathReviews)
        return (filmJSON, reviewJSON)

    def countFilmParam(self, filmJSON, param, flag = True):
        
        paramDict = {}

        for film in filmJSON['filmArray']:

            if flag:
                elemArr = film[param]
                
            else:
                elemArr = [film[param]]

            for elem in elemArr:
                
                if elem in paramDict:
                    paramDict[elem] += 1
                    
                else:
                    paramDict[elem] = 1

        return paramDict

    def sortBySecondElem(self, elem):
        return elem[1]

    def sortByThirdElem(self, elem):
        return elem[2]

    def sortFilmByRating(self, filmJSON, takeFilms):
        
        filmRatingArr = []

        for film in filmJSON['filmArray']:
            filmRatingArr.append((film['nameRU'], film['ratingValue'], film['ratingCount']))

        highFilmRatingValue = sorted(filmRatingArr, key = self.sortBySecondElem, reverse = True)[:takeFilms]
        highFilmRatingCount = sorted(filmRatingArr, key = self.sortByThirdElem,  reverse = True)[:takeFilms]
        
        return (
            {film[0]:film[1] for film in highFilmRatingValue},
            {film[0]:film[2] for film in highFilmRatingCount}
        )
    
    def sortFilmByTime(self, filmJSON, takeFilms):
        
        movieTimeArr  = []
        serialTimeArr = []

        for film in filmJSON['filmArray']:
            
            if (film['type'] == 'TVSeries'):
                serialTimeArr.append((film['nameRU'], film['episodesCount'], film['allTime']))
            
            else:
                movieTimeArr.append((film['nameRU'], film['timeForEpisode']))
                
        highSerialEpisodesCount = sorted(serialTimeArr, key = self.sortBySecondElem, reverse = True)[:takeFilms]
        highSerialAllTime       = sorted(serialTimeArr, key = self.sortByThirdElem,  reverse = True)[:takeFilms]
        highMovieTime           = sorted(movieTimeArr,  key = self.sortBySecondElem, reverse = True)[:takeFilms]

        return (
            {movie[0] : movie[1] for movie  in highMovieTime},
            {serial[0]:serial[1] for serial in highSerialEpisodesCount},
            {serial[0]:serial[2] for serial in highSerialAllTime}
        )

    def filmPerson(self, filmJSON, typeOfPerson):

        personIDAndName   = {}
        personIDAndRating = {}

        for film in filmJSON['filmArray']:
            
            filmRatingValue = film['ratingValue']

            for person in film[typeOfPerson]:

                personID = person['ID']

                if personID not in personIDAndName:
                    personIDAndName[personID]   = person['name']
                    personIDAndRating[personID] = []
                
                personIDAndRating[personID].append(filmRatingValue)
        
        for personID in personIDAndRating.keys():          
            personRating = personIDAndRating[personID]
            personFilmCount = len(personRating)
            personIDAndRating[personID] = (personIDAndName[personID], 
                                           personFilmCount, sum(personRating) / personFilmCount)

        return personIDAndRating

    def sortReviewByCount(self, reviewJSON):

        reviewArr = []

        for review in reviewJSON['reviewArray']:
            
            reviewMax   = review['reviewMax']
            reviewClass = review['reviewClass']
            
            reviewPercWithoutNeut = (
                round((reviewClass[0] + reviewClass[2] // 2) / reviewMax * 100, 3),
                round(reviewClass[0] / (reviewMax - reviewClass[2]) * 100, 3),
            )
            
            reviewArr.append((review['filmID'], reviewMax, reviewClass,
                              review['reviewPercent'], reviewPercWithoutNeut))

        highReviewCount = sorted(reviewArr, key = self.sortBySecondElem, reverse = True)
        
        return {review[0]:(review[1], review[2], review[3], review[4]) for review in highReviewCount}

    def main(self):
        
        filmJSON, reviewJSON = self.getFilmAndReviewJSON()

        filmGenreDict  = self.countFilmParam(filmJSON, 'genre')
        filmYearDict   = self.countFilmParam(filmJSON, 'year', False)
        
        filmRating = self.sortFilmByRating(filmJSON, 10)

        filmTime   = self.sortFilmByTime(filmJSON, 10)
        
        filmPersonActors = self.filmPerson(filmJSON, 'actor')

        # print(filmGenreDict)
        # print(filmYearDict)
        # print(filmRating)
        # print(filmTime)
        # print(filmPersonActors)

        reviewClass = self.sortReviewByCount(reviewJSON)
        
        # print(reviewClass)

        return
    
if __name__ == '__main__':
    
    defaultConfigParameters = {
        'dataPathFilms'   : '../../data/films.json',
        'dataPathReviews' : '../../data/reviews.json'
    }
    
    DataAnalytics(defaultConfigParameters).main()