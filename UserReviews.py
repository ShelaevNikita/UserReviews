#!/usr/bin/env python3

import src.dataMiningKinopoisk.FilmMining   as filmMining
import src.dataMiningKinopoisk.ReviewMining as reviewMining
import src.Visualization                    as visualization
import src.DataAnalytics                    as dataAnalytics

class mainClassUserReview(object):
    
    def __init__(self):
        
        self.configFile       = './configFile.txt'
        
        self.configParameters = {}

    def inputConfigFile(self):
        
        inputFlag = input(f'\t Use default config file (\"{self.configFile}\")? (Y / N): ')
        
        if inputFlag.strip().lower().startswith('n'):
            self.configFile = input('\t Enter path and name your config file: ').strip()
              
        return

    def splitConfigFile(self):
        
        dataParameters = ''
        
        try:
            with open(self.configFile, 'r') as fileData:
                dataParameters = fileData.readlines()
                
        except FileNotFoundError:
            print('\t ERROR: Not found config file!...')
            return
        
        for line in dataParameters[3:]:
            
            splitParameter = line.replace('\n', ' ').replace('\t', ' ').split('=')
            
            parameterName  = splitParameter[0].strip()
            parameterValue = splitParameter[1].strip()
            
            try:
                parameterValue = int(parameterValue)
                
            except ValueError:
                pass
            
            self.configParameters[parameterName] = parameterValue
            
        return

    def orderWork(self):

        # filmMining.FilmMining(self.configParameters).main()
    
        # reviewMining.ReviewMining(self.configParameters).main()
        
        # dataAnalytics.DataAnalytics(self.configParameters).main()

        visualization.VisualizationReviews(self.configParameters).main()

        return

    def main(self):

        print('\n\t\t Hello in app \"UserReview\"!\n')
        
        # self.inputConfigFile()
        self.splitConfigFile()
        self.orderWork()

        return

if __name__ == '__main__':
    mainClassUserReview().main()