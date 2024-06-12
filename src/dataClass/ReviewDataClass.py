#!/usr/bin/env python3

from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict

#  ласс данных дл¤ хранени¤ информации о пользовательском отзыве
@dataclass
class Review:
    author:      str = '?'
    reviewClass: int = 0    # 0 - Good; 1 - Neutral; 2 - Negative
    title:       str = '?'
    dateAndTime: str = '?'
    reviewText:  str = '?'

#  ласс данных дл¤ хранени¤ информации обо всех пользовательских отзывах
#    к конкретному фильму / сериалу   
@dataclass
class ReviewForFilm:
    _id:              int = 0
    reviewMax:        int = 0
    countGood:        int = 0
    countNeutral:     int = 0
    countNegative:    int = 0

    reviewPercent:  float = 0.0
    
    pages:   List[int]    = field(default_factory = list)
    reviews: List[Review] = field(default_factory = list)
    
    def toDict(self) -> Dict[str, Any]:
        return asdict(self)