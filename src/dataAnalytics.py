#!/usr/bin/env python3

import json

from datetime import datetime as dt

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
            
            personRating = personIDAndRating[personID]
            
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
        
        reviewDateCount = {}

        for film in reviewJSON['reviewArray']:
            
           if film['filmID'] != filmID:
               continue
           
           for review in film['reviews']:
               
               reviewDateAndTime = dt.strptime(review['dateAndTime'], '%H:%M|%d.%m.%Y')
               
               keyReview = reviewDateAndTime.strftime('%m.%Y')
               
               if keyReview in reviewDateCount:
                   reviewDateCount[keyReview] += 1
                   
               else:
                   reviewDateCount[keyReview] = 1

           break

        return [(dt.strptime(key, '%m.%Y'), value) 
                for (key, value) in reviewDateCount.items()]

    def reviewLenText(self, reviewJSON, filmID):
        
        reviewGood = []
        reviewNeg  = []
        reviewNeut = []

        notUsedSymbols = [
            '.',  ',', '–', '-', '—', 
            ';', '\'', ':', '«', '»',
            '(',  ')', '!', '?'
        ]

        for film in reviewJSON['reviewArray']:
            
            if film['filmID'] != filmID:
                continue
           
            for review in film['reviews']:

                reviewText  = review['reviewText']
                reviewClass = review['class']

                for symbol in notUsedSymbols:
                    reviewText = reviewText.replace(symbol, '')
                
                reviewText = reviewText.replace('…', ' ').replace('/', ' ')

                reviewTextArr = reviewText.lower().split()

                if reviewClass == 'Good':
                    reviewGood.append(len(reviewTextArr))
                
                elif reviewClass == 'Neutral':
                    reviewNeut.append(len(reviewTextArr))
                    
                else:
                    reviewNeg.append(len(reviewTextArr))

            break

        return (reviewGood, reviewNeg, reviewNeut)

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
        
        reviewClassArr   = self.countFilmReview(reviewJSON)
        
        reviewDateCount  = self.countReviewDate(reviewJSON, 435)
        
        reviewLenTextArr = self.reviewLenText(reviewJSON, 435)
        
        print(reviewClassArr)
        print(reviewDateCount)
        print(reviewLenTextArr)

        return

    def main(self):
        
        filmJSON, reviewJSON = self.getFilmAndReviewJSON()

        self.fillFilmIDAndName(filmJSON)

        self.filmAnalytics(filmJSON)

        self.reviewAnalytics(reviewJSON)

        return
    
if __name__ == '__main__':
    
    defaultConfigParameters = {
        'dataPathFilms'   : '../../data/films.json',
        'dataPathReviews' : '../../data/reviews.json'
    }
    
    DataAnalytics(defaultConfigParameters).main()