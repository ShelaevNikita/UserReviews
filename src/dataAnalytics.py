#!/usr/bin/env python3

import json

class DataAnalytics(object):
    
    def __init__(self, dataPathFilms, dataPathReviews):
        self.dataPathFilms   = dataPathFilms
        self.dataPathReviews = dataPathReviews
     
    def getJSONFromFile(self, dataPath):
        try:
            with open(dataPath, 'r', encoding = 'utf-8') as file:
                return json.loads(file.read(), strict = False)
                
        except FileNotFoundError:
            print(f'\n Error: Not found file \"{dataPath}\"!')
            return None
    
    def main(self):
        filmJSON   = self.getJSONFromFile(self.dataPathFilms)
        reviewJSON = self.getJSONFromFile(self.dataPathReviews)
        
        return
    
if __name__ == '__main__':
    
    dataPathFilms   = '../../data/films.json'
    dataPathReviews = '../../data/reviews.json'
    
    DataAnalytics(dataPathFilms, dataPathReviews).main()