#!/usr/bin/env python3

import json

class DataAnalytics(object):
    
    def __init__(self, configParameters):
        
        self.dataPathFilms   = configParameters['dataPathFilms']
        self.dataPathReviews = configParameters['dataPathReviews']
        
        self.filmIDAndName   = {}

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

    def sortBySecondElem(self, elem):
        return elem[1]
    
    def sortByThirdElem(self, elem):
        return elem[2]

    def fillFilmIDAndName(self, filmJSON):
        
        for film in filmJSON['filmArray']:
            self.filmIDAndName[film['ID']] = film['nameRU']

        return

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
        
        paramArr = [(param, value) for (param, value) in paramDict.items()]

        return sorted(paramArr, key = self.sortBySecondElem, reverse = True)

    def sortFilmByRating(self, filmJSON):
        
        filmRatingArr = []
        
        for film in filmJSON['filmArray']:
            filmRatingArr.append((film['nameRU'], film['ratingValue'], film['ratingCount']))
            
        highFilmRatingValue = sorted(filmRatingArr, key = self.sortBySecondElem, reverse = True)
        highFilmRatingCount = sorted(filmRatingArr, key = self.sortByThirdElem,  reverse = True)
        
        return (
            [(film[0], film[1]) for film in highFilmRatingValue],
            [(film[0], film[2]) for film in highFilmRatingCount]
        )
    
    def sortFilmByTime(self, filmJSON):
        
        movieTimeArr  = []
        serialTimeArr = []

        for film in filmJSON['filmArray']:
            
            if (film['type'] == 'TVSeries'):
                serialTimeArr.append((film['nameRU'], film['episodesCount'], film['allTime']))
            
            else:
                movieTimeArr.append((film['nameRU'], film['timeForEpisode']))
                
        highSerialEpisodesCount = sorted(serialTimeArr, key = self.sortBySecondElem, reverse = True)
        highSerialAllTime       = sorted(serialTimeArr, key = self.sortByThirdElem,  reverse = True)
        highMovieTime           = sorted(movieTimeArr,  key = self.sortBySecondElem, reverse = True)

        return (
            highMovieTime,
            [(serial[0], serial[1]) for serial in highSerialEpisodesCount],
            [(serial[0], serial[2]) for serial in highSerialAllTime]
        )

    def filmPerson(self, filmJSON, typeOfPerson):

        personIDAndName   = {}
        personIDAndRating = {}
        
        personIDAndRatingArr = []

        for film in filmJSON['filmArray']:
            
            filmRatingValue = film['ratingValue']

            for person in film[typeOfPerson]:

                personID = person['ID']

                if personID not in personIDAndName:
                    personIDAndName  [personID] = person['name']
                    personIDAndRating[personID] = []
                
                personIDAndRating[personID].append(filmRatingValue)
        
        for personID in personIDAndRating.keys():
            
            personRating = personIDAndRating[personID]
            
            personFilmCount = len(personRating)
            personRatingAvg = round(sum(personRating) / personFilmCount, 3)

            personIDAndRatingArr.append((personID, personIDAndName[personID], 
                                         personRatingAvg, personFilmCount))

        return sorted(personIDAndRatingArr, key = self.sortByThirdElem,  reverse = True)

    def sortReviewByCount(self, reviewJSON):

        reviewArr = []

        for review in reviewJSON['reviewArray']:
            
            reviewMax   = review['reviewMax']
            reviewClass = review['reviewClass']
            
            filmID = review['filmID']
            
            reviewPercWithoutNeut = (
                round((reviewClass[0] + reviewClass[2] // 2) / reviewMax * 100, 3),
                round(reviewClass[0] / (reviewMax - reviewClass[2]) * 100, 3),
            )
            
            reviewArr.append((filmID, reviewMax, review['reviewPercent'], reviewClass,
                              self.filmIDAndName[filmID], reviewPercWithoutNeut))

        highReviewCount   = sorted(reviewArr, key = self.sortBySecondElem, reverse = True)
        highReviewPercent = sorted(reviewArr, key = self.sortByThirdElem,  reverse = True)
        
        return (
            [(review[4], review[1]) for review in highReviewCount],
            [(review[4], review[2]) for review in highReviewPercent]
        )

    def filmAnalytics(self, filmJSON):
        
        filmGenreArr  = self.countFilmParam(filmJSON, 'genre')
        filmYearArr   = self.countFilmParam(filmJSON, 'year', False)
        
        filmRatingArr = self.sortFilmByRating(filmJSON)

        filmTimeArr   = self.sortFilmByTime(filmJSON)
        
        filmPersonActors = self.filmPerson(filmJSON, 'actor')

        print(filmGenreArr)
        print(filmYearArr)
        print(filmRatingArr)
        print(filmTimeArr)
        print(filmPersonActors)

        return

    def reviewAnalytics(self, reviewJSON):
        
        reviewClassArr = self.sortReviewByCount(reviewJSON)
        
        print(reviewClassArr)

        return

    def main(self):
        
        filmJSON, reviewJSON = self.getFilmAndReviewJSON()

        self.filmAnalytics(filmJSON)

        self.reviewAnalytics(reviewJSON)

        return
    
if __name__ == '__main__':
    
    defaultConfigParameters = {
        'dataPathFilms'   : '../../data/films.json',
        'dataPathReviews' : '../../data/reviews.json'
    }
    
    DataAnalytics(defaultConfigParameters).main()