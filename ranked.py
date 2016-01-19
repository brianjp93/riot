"""
ranked.py

Brian Perrett
3/31/15
Written for funsies

Example usage:
$ python27 ranked.py brianjp93
"""

from riot import Riot
import sys

riot = Riot()

seasons = {"1": "PRESEASON2013",
    "2": "SEASON2013",
    "3": "PRESEASON2014",
    "4": "SEASON2014",
    "5": "PRESEASON2015",
    "6": "SEASON2015",
    "7": "PRESEASON2016",
    "8": "SEASON2016",
    "9": ""}

name = sys.argv[1]
sea = raw_input("1 -> Preseason 3\n2 -> Season 3\n3 -> Preseason 4\n4 -> Season 4\n5 -> Preseason 5\n6 -> Season 5\n7 -> Preseason 6\n8 -> Season 6\n9 -> All\nWhat season do you want data for? - ")

riot.getRankedData(name, seasons=seasons[sea])
# riot.getRankedData(name)
