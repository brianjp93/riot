"""
riot.py
Brian Perrett
3/31/15
messing around with riot's developer api
"""
from __future__ import division
import requests
import json
import time
import csv
import os.path
import pprint


class Riot:
    def __init__(self):
        self.key = None
        self.creds = None
        self.base = "https://na.api.pvp.net/api/lol/na/"
        self.champName = {}
        self.champId = {}
        self.fillChampDicts()

    def fillChampDicts(self):
        """
        fills dictionaries by querying riot api
        """
        if self.key is None:
            self.getKey()
        champ_dict = self.getChampionJson()
        for champ in champ_dict["data"]:
            champ_name = str(champ_dict["data"][champ]["name"])
            identity = str(champ_dict["data"][champ]["id"])
            self.champName[champ_name] = identity
            self.champId[identity] = champ_name

    def getCreds(self):
        """
        gets credentials from riot.auth file
        returns dictionary
        """
        creds = {}
        with open("riot.auth", "r") as f:
            for line in f:
                if line[0] != "#":
                    line = line.split(":")
                    key = line[0].strip()
                    val = line[1].strip()
                    creds[key] = val
        self.creds = creds
        return creds

    def getKey(self):
        """
        fills in self.key from the self.creds dictionary
        """
        if self.creds is None:
            self.getCreds()
        self.key = self.creds["key"]

    def getFeaturedGames(self, version="v1.0"):
        if self.key is None:
            self.getKey()
        html = "https://na.api.pvp.net/observer-mode/rest/featured?api_key=" + self.key
        r = requests.get(html)
        time.sleep(1)
        return r

    def getSummonerNames(self):
        """
        Gets summoner names from featured games
        """
        summoners = []
        if self.key is None:
            self.getKey()
        r = self.getFeaturedGames()
        for game in r.json()["gameList"]:
            for part in game["participants"]:
                summoners.append((part["summonerName"]))
        return summoners

    def getFeaturedGameStats(self):
        """
        Writes csv with data of many champions from ranked summoners in featured games
        if featuredGameStats.csv file exists, stats are added to this file.
        """
        summoners = self.getSummonerNames()
        old_summoners = set()
        # summoners = summoners[2:4]
        full_data = {}
        filename = "featuredGameStats.csv"
        # print(os.path.isfile(filename))
        if os.path.isfile("summoners.txt"):
            with open("summoners.txt", "r") as f:
                for line in f:
                    summ = line.strip()
                    old_summoners.add(summ)
        if os.path.isfile(filename):
            with open(filename, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    champ = row["Champion"]
                    wins = int(row["Wins"])
                    losses = int(row["Losses"])
                    k = int(row["Kills"])
                    d = int(row["Deaths"])
                    a = int(row["Assists"])
                    full_data[champ] = {"wins": wins,
                                        "losses": losses,
                                        "k": k,
                                        "d": d,
                                        "a": a,
                                        "wl_ratio": 0,  # computed later
                                        "kda": 0,       # computed later
                                        "games": 0}     # computed later
        for count, summoner in enumerate(summoners):
            if summoner in old_summoners:
                print("Data already found for %s" % summoner)
            else:
                print("Getting champion data for %s. (%d/%d)" % (summoner, count+1, len(summoners)))
                totals, data = self.getFullMatchHistory(summoner)
                old_summoners.add(summoner)
                for champ in data:
                    if champ in full_data:
                        full_data[champ]["k"] += data[champ]["k"]
                        full_data[champ]["d"] += data[champ]["d"]
                        full_data[champ]["a"] += data[champ]["a"]
                        full_data[champ]["wins"] += data[champ]["wins"]
                        full_data[champ]["losses"] += data[champ]["losses"]
                        if data[champ]["losses"] == 0:
                            full_data[champ]["wl_ratio"] = data[champ]["wins"]
                        else:
                            full_data[champ]["wl_ratio"] = round(data[champ]["wins"]/data[champ]["losses"], 2)
                    else:
                        full_data[champ] = {"k": 0,
                                            "d": 0,
                                            "a": 0,
                                            "wins": 0,
                                            "losses": 0,
                                            "kda": 0,
                                            "wl_ratio": 0,
                                            "games": 0}
                        full_data[champ]["k"] += data[champ]["k"]
                        full_data[champ]["d"] += data[champ]["d"]
                        full_data[champ]["a"] += data[champ]["a"]
                        full_data[champ]["wins"] += data[champ]["wins"]
                        full_data[champ]["losses"] += data[champ]["losses"]
                for champ in full_data:
                    k = full_data[champ]["k"]
                    d = full_data[champ]["d"]
                    a = full_data[champ]["a"]
                    wins = full_data[champ]["wins"]
                    losses = full_data[champ]["losses"]
                    if d == 0:
                        full_data[champ]["kda"] = (k + a)
                    else:
                        full_data[champ]["kda"] = round((k + a)/d, 2)
                    if losses == 0:
                        full_data[champ]["wl_ratio"] = wins
                    else:
                        full_data[champ]["wl_ratio"] = round(wins/losses, 2)
                    full_data[champ]["games"] = wins + losses
        with open(filename, "wb") as f:
            fieldnames = ["Champion", "KDA", "W/L Ratio", "Wins", "Losses", "Kills", "Deaths", "Assists", "Games"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for champ in full_data:
                writer.writerow({"Champion": champ,
                                "KDA": str(full_data[champ]["kda"]),
                                "W/L Ratio": str(full_data[champ]["wl_ratio"]),
                                "Wins": str(full_data[champ]["wins"]),
                                "Losses": str(full_data[champ]["losses"]),
                                "Kills": str(full_data[champ]["k"]),
                                "Deaths": str(full_data[champ]["d"]),
                                "Assists": str(full_data[champ]["a"]),
                                "Games": str(full_data[champ]["games"])})
        with open("summoners.txt", "wb") as f:
            for summ in old_summoners:
                f.write(summ.encode("utf-8")+"\n")
        print("Finished making %s" % filename)

    def getMatchHistory(self,
                        summonerid,
                        j_son=True,
                        version="v2.2",
                        beginIndex=None,
                        endIndex=None,
                        championids=None,
                        rankedqueues="RANKED_SOLO_5x5",
                        seasons=None,
                        begintime=None,
                        endtime=None):
        if self.key is None:
            self.getKey()
        html = self.base + version + "/matchlist/by-summoner/" + summonerid
        payload = {
            "api_key": self.key,
            "rankedQueues": rankedqueues
            }
        if beginIndex is not None: payload["beginIndex"] = beginIndex
        if endIndex is not None: payload["endIndex"] = endIndex
        if championids is not None: payload["championIds"] = championids
        if seasons is not None: payload["seasons"] = seasons
        if begintime is not None: payload["beginTime"] = begintime
        if endtime is not None: payload["endTime"] = endtime
        r = requests.get(html, params=payload)
        time.sleep(1)
        received = False
        if j_son:
            while not received:
                try:
                    x = r.json()
                    if not x == {}:
                        x["matches"]
                    received = True
                    return r
                except:
                    print("Retrying with error code %s" % r.status_code)
                    r = requests.get(html)
                    time.sleep(1)
            return r
        else:
            return r

    def getSummonerHistory(self,
                            summonerid,
                            version="v2.2",
                            begintime=None,
                            endtime=None,
                            beginIndex=None,
                            endIndex=None,
                            championids=None,
                            rankedqueues="RANKED_SOLO_5x5",
                            seasons=None):
        """
        Retrieve data on a summoner.
        """
        r = self.getMatchHistory(summonerid,
            version=version,
            beginIndex=beginIndex,
            endIndex=endIndex,
            championids=championids,
            rankedqueues=rankedqueues,
            seasons=seasons,
            begintime=begintime,
            endtime=endtime)
        matches = set()
        match_info = {}
        match_json = r.json()
        wins = 0
        losses = 0
        games = 0
        total_time = 0
        total_kills = 0
        total_assists = 0
        total_deaths = 0
        for match in match_json["matches"]:
            matches.add(match["matchId"])
        for match in matches:
            print("Retrieving game {}.".format(games+1))
            code = "400"
            while code != "200":
                r = self.getMatch(match)
                code = str(r.status_code)
                # print("code")
            m = r.json()
            # print(m)
            games += 1
            try:
                duration = int(m["matchDuration"])
            except:
                with open("No match duration found.txt", "wb") as f:
                    f.write(pprint.pformat(m))
                raise Exception("No match duration found")
            total_time += duration
            for team in m["teams"]:
                if str(team["winner"]) == "False":
                    loser = str(team["teamId"])
                elif str(team["winner"]) == "True":
                    winner = str(team["teamId"])
            for part in m["participantIdentities"]:
                # print(part)
                if str(part["player"]["summonerId"]) == str(summonerid):
                    p_id = part["participantId"]
            for part in m["participants"]:
                if part["participantId"] == p_id:
                    info = part
                    # print(info)
                    champ_id = (str(info["championId"]))
                    stats = info["stats"]
                    k = int(stats["kills"])
                    total_kills += k
                    d = int(stats["deaths"])
                    total_deaths += d
                    a = int(stats["assists"])
                    total_assists += a
                    gold = int(stats["goldEarned"])
                    wards_placed = int(stats["wardsPlaced"])
                    minions = int(stats["minionsKilled"])
                    teamid = str(info["teamId"])
                    win = False
                    lose = False
                    if teamid == winner:
                        wins += 1
                        win = True
                    elif teamid == loser:
                        losses += 1
                        lose = True
                    champ = self.getChampName(champ_id)
                    if champ in match_info:
                        match_info[champ]["k"] += k
                        match_info[champ]["d"] += d
                        match_info[champ]["a"] += a
                        match_info[champ]["gold"] += gold
                        match_info[champ]["wardsPlaced"] += wards_placed
                        match_info[champ]["cs"] += minions
                        match_info[champ]["time"] += duration
                        if teamid == winner:
                            match_info[champ]["wins"] += 1
                        else:
                            match_info[champ]["losses"] += 1
                        match_info[champ]["games"] += 1
                    else:
                        champ_info = {"k": k,
                            "d": d,
                            "a": a,
                            "gold": gold,
                            "wardsPlaced": wards_placed,
                            "cs": minions,
                            "wins": 0,
                            "losses": 0,
                            "games": 1,
                            "time": duration}
                        if win:
                            champ_info["wins"] += 1
                        elif lose:
                            champ_info["losses"] += 1
                        match_info[champ] = champ_info
        endinfo = {"totalKills": total_kills,
            "totalDeaths": total_deaths,
            "totalAssists": total_assists,
            "kda": (total_kills+total_assists)/total_deaths,
            "totalTime": total_time,
            "champData": match_info}
        print("Finished retrieving match data for summonerid {}".format(summonerid))
        return endinfo

    def getRankedData(self,
                        summoner_name,
                        version="v2.2",
                        begintime=None,
                        endtime=None,
                        beginIndex=None,
                        endIndex=None,
                        championids=None,
                        rankedqueues="RANKED_SOLO_5x5",
                        seasons=None):
        """
        Retrieve data on a summoner.
        """
        summonerid = self.getSummonerId(summoner_name)
        info = self.getSummonerHistory(summonerid,
            version=version,
            beginIndex=beginIndex,
            endIndex=endIndex,
            championids=championids,
            rankedqueues=rankedqueues,
            seasons=seasons,
            begintime=begintime,
            endtime=endtime)
        with open("data/{}_{}.csv".format(summoner_name, seasons), "wb") as f:
            header = ["Champion",
                "KDA",
                "W/L",
                "Wins",
                "Losses",
                "Kill AVG",
                "Death AVG",
                "Assist AVG",
                "Games Played",
                "Time Played (Days)",
                "CS/m",
                "g/m",
                "ward AVG",
                "Total KDA",
                "Total Time (Days)"]
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            days_total = info["totalTime"]/3600/24
            writer.writerow({"Total KDA": str(info["kda"]), "Total Time (Days)": days_total})
            for c in info["champData"]:
                c_info = info["champData"][c]
                if c_info["losses"] == 0:
                    winloss = "inf"
                else:
                    winloss = str(c_info["wins"]/c_info["losses"])
                if str(c_info["d"]) == "0":
                    kda = "Perfect"
                else:
                    kda = str((c_info["k"] + c_info["a"])/c_info["d"])
                writer.writerow({"KDA": kda,
                    "Champion": c,
                    "Kill AVG": str(c_info["k"]/c_info["games"]),
                    "Death AVG": str(c_info["d"]/c_info["games"]),
                    "Assist AVG": str(c_info["a"]/c_info["games"]),
                    "Games Played": str(c_info["games"]),
                    "Time Played (Days)": str(c_info["time"]/3600/24),
                    "CS/m": str(c_info["cs"]/(c_info["time"]/60)),
                    "g/m": str(c_info["gold"]/(c_info["time"]/60)),
                    "ward AVG": str(c_info["wardsPlaced"]/c_info["games"]),
                    "W/L": winloss,
                    "Wins": str(c_info["wins"]),
                    "Losses": str(c_info["losses"])})
        print("Finished writing csv for {}".format(summoner_name))

    def getChampionJson(self, version="v1.2"):
        if self.key is None:
            self.getKey()
        html = "https://na.api.pvp.net/api/lol/static-data/na/" + version + "/champion/" + "?api_key=" + self.key
        r = requests.get(html)
        # print(r.status_code)
        return r.json()

    @staticmethod
    def prettyJson(json_dict):
        pretty = json.dumps(json_dict, indent=4, separators=(",", ":"))
        return pretty

    def getChampId(self, name):
        if self.champName == {}:
            self.fillChampDicts()
        return self.champName[name]

    def getChampName(self, identity):
        if self.champId == {}:
            self.fillChampDicts()
        return self.champId[identity]

    def getMatch(self, matchid, version="v2.2"):
        html = "{}{}/match/{}".format(self.base, version, matchid)
        params = {"api_key": self.key}
        r = requests.get(html, params=params)
        time.sleep(1)
        return r

    def getSummonerId(self, name, version="v1.4"):
        """
        returns summoner id given summoner name
        """
        if self.key is None:
            self.getKey()
        html = self.base + version + "/summoner/by-name/" + name + "?api_key=" + self.key
        # print(html)
        received = False
        name = name.lower()
        name = "".join(name.split())
        while not received:
            try:
                r = requests.get(html)
                time.sleep(1)
                r.json()[name]["id"]
                received = True
            except:
                print("Retrying with error code %s" % r.status_code)
        # print(r.json())
        identity = r.json()[name]["id"]
        return str(identity)


def testGetChampName():
    riot = Riot()
    r_json = riot.getChampionJson()
    with open("champidjson.txt", "wb") as f:
        f.write(riot.prettyJson(r_json))


def testMatchHistory(summonerid):
    riot = Riot()
    mh = riot.getMatchHistory(summonerid)
    with open("matchhistory.txt", "wb") as f:
        f.write(riot.prettyJson(mh))


def main():
    riot = Riot()
    r = riot.getFeaturedGames()
    pretty = riot.prettyJson(r.json())
    with open("prettyjson.txt", "wb") as f:
        f.write(pretty)


def test():
    riot = Riot()
    riot.getKey()
    r = requests.get("https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/brianjp93?api_key=" + riot.key)
    print(r.text)


def test2():
    riot = Riot()
    mh_json = riot.getMatchHistory("45294480", seasons="PRESEASON2016")
    print(pprint.pformat(mh_json))
    # riot.parseMatchHistory(mh_json)


def testGetSummonerId():
    riot = Riot()
    identity = riot.getSummonerId("brianjp93")
    print(identity)


def testGetFullMatchHistory():
    riot = Riot()
    totals, data = riot.getFullMatchHistory("brianjp93")
    print(data)
    print(totals)


def testGetRankedData(name):
    riot = Riot()
    riot.getRankedData(name)


def testGetSummoners():
    riot = Riot()
    names = riot.getSummonerNames()
    print(names)


def testGetFeaturedStats():
    riot = Riot()
    riot.getFeaturedGameStats()

def testGetMatch(matchid):
    riot = Riot()
    r = riot.getMatch(matchid)
    with open("match.txt", "wb") as f:
        f.write(pprint.pformat(r.json()))

def testGetSummonerHistory(summoner_name):
    riot = Riot()
    identity = riot.getSummonerId(summoner_name)
    info = riot.getSummonerHistory(identity, seasons="PRESEASON2016", beginIndex=0, endIndex=10)
    print(info)

if __name__ == '__main__':
    # main()
    # test()
    # testMatchHistory("45294480")
    # testGetChampName()
    # test2()
    # testGetSummonerId()
    # testGetFullMatchHistory()
    testGetRankedData("kiiroi flash")
    # testGetSummoners()
    # testGetFeaturedStats()
    # testGetMatch("2043270746")
    # testGetSummonerHistory("brianjp93")
