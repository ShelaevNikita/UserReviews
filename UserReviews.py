#!/usr/bin/env python3

import src.dataMiningKinopoisk.filmMining   as filmMining
import src.dataMiningKinopoisk.reviewMining as reviewMining
import src.dataAnalytics                    as dataAnalytics

def userReviews():

    dataPathFilms   = './data/movies.json'
    dataPathReviews = './data/reviews.json'
    threads         = 4
    #maxID          = 700000
    maxID           = 435
    reviewInPage    = 10

    #filmMining.FilmMining(dataPathFilms, threads, maxID).main()
    
    reviewMining.ReviewMining(dataPathFilms, dataPathReviews, threads, reviewInPage).main()

    #dataAnalytics.DataAnalytics(dataPathFilms, dataPathReviews).main()

    return

if __name__ == '__main__':
    userReviews()