
import sys
sys.path.append('../src')

import src.dataMiningKinopoisk.DataMining as DM
import src.dataAnalytics.DataAnalytics    as DA
import src.dataPredict.DataPredict        as DP
import src.visualization.Visualization    as VS
import src.dataClass.FilmDataClass        as FC
import src.dataClass.ReviewDataClass      as RC

class TestUnit(object):
    
    def testSplitXY(self):
        XY   = [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
        X, Y = VS.VisualizationReviews().splitArrToXAndY(XY, 3, 2)
        assert X == [3, 6, 9]
        assert Y == [2, 5, 8]
        
    def testFilmClass(self):
        film     = FC.Film()
        film._id = 5
        assert film.toDict()['_id'] == 5
        
    def testReviewClass(self):
        review               = RC.ReviewForFilm()
        review.reviewMax     = 100
        review.countGood     = 50
        review.countNegative = 20
        review.countNeutral  = 30
        assert review.reviewMax == \
            (review.countGood + review.countNegative + review.countNeutral)
      
