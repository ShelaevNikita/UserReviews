#!/usr/bin/env python3

import src.dataMiningKinopoisk.filmMining   as filmMining
import src.dataMiningKinopoisk.reviewMining as reviewMining

def userReviews():

    dataPathFilms   = './data/films.json'
    dataPathReviews = './data/reviews.json'
    threads  = 1
    #maxID   = 700000
    maxID    = 435 

    filmMining.FilmMining(dataPathFilms, threads, maxID).main()
    
    #reviewMining.ReviewMining(dataPathFilms, dataPathReviews, threads).main()

    return

if __name__ == '__main__':
    userReviews()