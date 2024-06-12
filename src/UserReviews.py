#!/usr/bin/env python3

import dataMiningKinopoisk.DataMining as DM
import dataAnalytics.DataAnalytics    as DA
import dataPredict.DataPredict        as DP
import visualization.Visualization    as VS

class mainClassUserReview(object):

    def main(self):
        print('\n\t Hello in app \"UserReview\"!\n')     
        DM.ClassDataMining().main()
        DA.DataAnalytics().main()
        DP.DataPredict().main()
        VS.VisualizationReviews().main()
        print('\n\t Bye!')
        return

if __name__ == '__main__':
    mainClassUserReview().main()