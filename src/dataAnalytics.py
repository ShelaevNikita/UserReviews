#!/usr/bin/env python3

import json
import numpy as np

from collections import Counter
from datetime    import datetime as dt

from sklearn.linear_model import LinearRegression

class DataAnalytics(object):
    
    def __init__(self, configParameters):       
        self.dataPathFilms    = configParameters['dataPathFilms']
        self.dataPathReviews  = configParameters['dataPathReviews']
        self.reviewWindowSize = configParameters['reviewWindowSize']
        
        self.filmIDAndName   = {}

    def getJSONFromFile(self, dataPath):        
        try:
            with open(dataPath, 'r', encoding = 'utf-8') as file:
                return json.loads(file.read(), strict = False)
        
        except FileNotFoundError:
            print(f'\n Error: Not found file \"{dataPath}\"!')
            return None
       
    def fillFilmIDAndName(self, filmJSON):      
        for film in filmJSON['filmArray']:
            self.filmIDAndName[film['ID']] = film['nameRU']

        return

    def getFilmAndReviewJSON(self):       
        filmJSON   = self.getJSONFromFile(self.dataPathFilms)
        reviewJSON = self.getJSONFromFile(self.dataPathReviews)
        
        self.fillFilmIDAndName(filmJSON)
        return (filmJSON, reviewJSON)

    def countFilmParam(self, filmJSON, param, flag = True):       
        paramDict = Counter()
        for film in filmJSON['filmArray']:           
            if flag:
                for elem in film[param]:               
                    paramDict[elem] += 1
            else:
                paramDict[film[param]] += 1  

        return list(paramDict.items())

    def countFilmRating(self, filmJSON):       
        filmRatingArr = []
        for film in filmJSON['filmArray']:
            filmRatingArr.append((film['nameRU'], film['ratingValue'], film['ratingCount']))
        
        return filmRatingArr
    
    def countFilmTime(self, filmJSON):       
        movieTimeArr  = []
        serialTimeArr = []
        for film in filmJSON['filmArray']:            
            if (film['type'] == 'TVSeries'):
                serialTimeArr.append((film['nameRU'], film['episodesCount'], film['allTime']))
            
            else:
                movieTimeArr.append((film['nameRU'], film['timeForEpisode']))

        return (movieTimeArr, serialTimeArr)

    def countFilmPerson(self, filmJSON, typeOfPerson):
        personIDAndName   = {}
        personIDAndRating = {}       
        personRatingArr   = []
        for film in filmJSON['filmArray']:           
            filmRatingValue = film['ratingValue']
            for person in film[typeOfPerson]:
                personID = person['ID']
                if personID not in personIDAndName:
                    personIDAndName  [personID] = person['name']
                    personIDAndRating[personID] = []
                
                personIDAndRating[personID].append(filmRatingValue)
        
        for personID in personIDAndRating.keys():           
            personRating    = personIDAndRating[personID]           
            personFilmCount = len(personRating)
            personRatingAvg = round(sum(personRating) / personFilmCount, 3)

            personRatingArr.append((personID, personIDAndName[personID],
                                    personRatingAvg, personFilmCount))

        return personRatingArr

    def countFilmReview(self, reviewJSON):
        reviewCountArr = []
        for film in reviewJSON['reviewArray']:           
            reviewMax   = film['reviewMax']
            reviewClass = film['reviewClass']           
            filmID      = film['filmID']
            
            reviewPercWithoutNeut = (
                round((reviewClass[0] + reviewClass[2] // 2) / reviewMax * 100, 3),
                round( reviewClass[0] / (reviewMax - reviewClass[2])     * 100, 3),
            )
            
            reviewCountArr.append((filmID, self.filmIDAndName[filmID], reviewMax, reviewClass,
                                   film['reviewPercent'], reviewPercWithoutNeut))
        
        return reviewCountArr

    def countReviewDate(self, reviewJSON, filmID):       
        reviewDateCount = Counter()
        for film in reviewJSON['reviewArray']:            
           if film['filmID'] != filmID:
               continue
           
           for review in film['reviews']:              
               reviewDateAndTime = dt.strptime(review['dateAndTime'], '%H:%M|%d.%m.%Y')           
               reviewDateCount[reviewDateAndTime.strftime('%m.%Y')] += 1

           break

        return [(dt.strptime(key, '%m.%Y'), value) 
                    for (key, value) in reviewDateCount.items()]

    def reviewLenText(self, reviewJSON, filmID):       
        reviewGood = []
        reviewNeg  = []
        reviewNeut = []

        notUsedSymbols = (
            '.',  ',', '–', '-', '—', 
            ';', '\'', ':', '«', '»',
            '(',  ')', '!', '?'
        )

        for film in reviewJSON['reviewArray']:           
            if film['filmID'] != filmID:
                continue
           
            for review in film['reviews']:
                reviewText  = review['reviewText']
                reviewClass = review['class']

                for symbol in notUsedSymbols:
                    reviewText = reviewText.replace(symbol, '')
                
                reviewText     = reviewText.replace('…', ' ').replace('/', ' ')
                reviewTextArr  = reviewText.lower().split()
                reviewLenText  = len(reviewTextArr)

                if reviewClass == 'Good':
                    reviewGood.append(reviewLenText)               
                elif reviewClass == 'Neutral':
                    reviewNeut.append(reviewLenText)                   
                else:
                    reviewNeg.append(reviewLenText)

            break

        return (reviewGood, reviewNeg, reviewNeut)

    def reviewDateWithWindow(self, reviewDateArr):
        windowSize     = self.reviewWindowSize
        windowSizeLeft = windowSize // 2
        rightMax       = len(reviewDateArr) - windowSizeLeft

        firstElem      = sum([reviewDateArr[j][1] for j in range(windowSize)]) // windowSize
        reviewValue    = []
        for i in range(windowSizeLeft + 1):
            reviewValue.append(firstElem)

        for i in range(windowSizeLeft + 1, rightMax):
            reviewWindow = [reviewDateArr[j][1] 
                                for j in range(i - windowSizeLeft, i + windowSizeLeft + 1)]
            
            reviewValue.append(sum(reviewWindow) // windowSize)
        
        lastElem = reviewValue[-1]
        for i in range(windowSizeLeft):
            reviewValue.append(lastElem)

        return [(reviewDateArr[i][0], reviewValue[i]) for i in range(len(reviewDateArr))]

    def fitLinearRegressionForReview(self, reviewDateArr):
        reviewIntTime  = []
        reviewValue    = []
        for review in reviewDateArr:
            month, year = map(int, review[0].strftime('%m %Y').split())
            reviewIntTime.append(year * 100 + month)
            reviewValue.append(review[1])
        
        reviewIntTime      = np.array(reviewIntTime).reshape((-1, 1))
        reviewValue        = np.array(reviewValue)
        
        reviewRegression   = LinearRegression().fit(reviewIntTime, reviewValue)
        predictReviewValue = reviewRegression.predict(reviewIntTime)

        return [(reviewDateArr[i][0], predictReviewValue[i]) 
                    for i in range(len(reviewDateArr))]

    def filmAnalytics(self, filmJSON):       
        filmGenreArr     = self.countFilmParam(filmJSON, 'genre')
        filmYearArr      = self.countFilmParam(filmJSON, 'year', False)
        
        filmRatingArr    = self.countFilmRating(filmJSON)

        filmTimeArr      = self.countFilmTime(filmJSON)
        
        filmPersonActors = self.countFilmPerson(filmJSON, 'actor')

        print(filmGenreArr)
        print(filmYearArr)
        print(filmRatingArr)
        print(filmTimeArr)
        print(filmPersonActors)

        return

    def reviewAnalytics(self, reviewJSON):        
        reviewClassArr      = self.countFilmReview(reviewJSON)
        
        reviewDateCount     = self.countReviewDate(reviewJSON, 435)
        
        reviewLenTextArr    = self.reviewLenText(reviewJSON, 435)
        reviewWithWindow    = self.reviewDateWithWindow(reviewLenTextArr)
        reviewLinearPredict = self.fitLinearRegressionForReview(reviewLinearPredict)      
        
        print(reviewClassArr)
        print(reviewDateCount)
        print(reviewLenTextArr)
        print(reviewWithWindow)
        print(reviewLinearPredict)

        return

    def main(self):       
        filmJSON, reviewJSON = self.getFilmAndReviewJSON()

        self.filmAnalytics(filmJSON)

        self.reviewAnalytics(reviewJSON)

        return
    
if __name__ == '__main__':
    
    defaultConfigParameters = {
        'dataPathFilms'    : '../../data/films.json',
        'dataPathReviews'  : '../../data/reviews.json',
        'reviewWindowSize' : 5
    }
    
    DataAnalytics(defaultConfigParameters).main()