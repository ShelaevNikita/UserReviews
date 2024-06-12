#!/usr/bin/env python3

from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict

#  ласс данных дл¤ хранени¤ информации о съЄмочной группе
@dataclass
class Person:
    _id:         int = 0
    personType: bool = True     # True - человек; False - студи¤
    name:        str = '?'

#  ласс данных дл¤ хранени¤ информации о фильме / сериале
@dataclass
class Film:
    _id:            int  = 0
    family:         int  = 2
    timeForEpisode: int  = 0
    episodesCount:  int  = 1
    year:           int  = 0
    ratingCount:    int  = 0
    
    filmType:      bool  = True  # True - фильм; False - сериал

    ratingValue:  float  = 0.0
    
    URL:            str  = '?'
    nameRU:         str  = '?'
    nameEN:         str  = '?'
    headline:       str  = '?'
    contentRating:  str  = '?'
    description:    str  = '?'
    
    genres:       List[str] = field(default_factory = list)
    countries:    List[str] = field(default_factory = list)
    awards:       List[str] = field(default_factory = list)
    
    producers: List[Person] = field(default_factory = list)
    directors: List[Person] = field(default_factory = list)
    actors:    List[Person] = field(default_factory = list)
    
    def toDict(self) -> Dict[str, Any]:
        return asdict(self)