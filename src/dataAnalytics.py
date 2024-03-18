#!/usr/bin/env python3

import json

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
    
    def main(self):
        
        filmJSON   = self.getJSONFromFile(self.dataPathFilms)
        reviewJSON = self.getJSONFromFile(self.dataPathReviews)
        
        return
    
if __name__ == '__main__':
    
    defaultConfigParameters = {
        'dataPathFilms'   : '../../data/films.json',
        'dataPathReviews' : '../../data/reviews.json'
    }
    
    DataAnalytics(defaultConfigParameters).main()