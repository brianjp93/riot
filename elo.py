"""
elo.py
"""
from __future__ import division
from riot import Riot
import csv
import os
import time
from datetime import datetime
import sys


def getPatchTime(day, month, year):
    """
    returns patch time in epoch time (ms)
    """
    epoch = datetime.utcfromtimestamp(0)
    return str(int((datetime(year=year, month=month, day=day) - epoch).total_seconds())*1000)


class Elo(Riot):

    divisions = ["bronze", "silver", "gold", "platinum", "diamond", "master", "challenger", "all"]
    patches = {
        "6.2": getPatchTime(1, 2, 2016),
        "6.3": getPatchTime(11, 2, 2016),
        "6.4": getPatchTime(25, 2, 2016)
        }
    patchend = {
    "6.2": patches["6.3"],
    "6.3": patches["6.4"]
    }

    def __init__(self, seedplayer, datafolder, elo="all", season=None, maxdivsize=20, patch=None, endtime=None):
        """
        seedplayer      - Player to first analyze previous games of
        elo             - Which elo players to record data of
                            - ["bronze", "silver", "gold", "platinum", "diamond",
                               "master", "challenger", "all"]
        season          - What season to gather data from.
        maxdivsize      - max size of list of players in each division to be checking next.
        """
        super(self.__class__, self).__init__()
        if elo not in self.divisions:
            raise Exception("elo must be one of {}.".format(self.divisions))
        self.elo = elo
        self.tocheck = {div: [] for div in self.divisions[:-1]}
        self.seedplayer = seedplayer
        self.datafolder = datafolder
        self.checkedplayersfile = "{}/checkedplayers.txt".format(self.datafolder)
        self.checkedgamesfile = "{}/checkedgames.txt".format(self.datafolder)
        self.bronzedatafile = "{}/bronze.csv".format(self.datafolder)
        self.silverdatafile = "{}/silver.csv".format(self.datafolder)
        self.golddatafile = "{}/gold.csv".format(self.datafolder)
        self.platinumdatafile = "{}/platinum.csv".format(self.datafolder)
        self.diamonddatafile = "{}/diamond.csv".format(self.datafolder)
        self.masterdatafile = "{}/master.csv".format(self.datafolder)
        self.challengerdatafile = "{}/challenger.csv".format(self.datafolder)
        self.datafiles = {
            "bronze": self.bronzedatafile,
            "silver": self.silverdatafile,
            "gold": self.golddatafile,
            "platinum": self.platinumdatafile,
            "diamond": self.diamonddatafile,
            "master": self.masterdatafile,
            "challenger": self.challengerdatafile
            }
        if not os.path.exists(self.datafolder):
            os.makedirs(self.datafolder)
        self.checkedplayers = self.getCheckedPlayers()
        self.checkedgames = self.getCheckedGames()
        self.maxdivsize = maxdivsize
        self.patch = self.patches[patch] if patch is not None else None
        self.season = season
        self.endtime = self.patches[endtime] if endtime is not None else None
        # print(self.patch)

    def getCheckedPlayers(self):
        """
        returns a set of all the players checked so far.
            Reads data from checkedplayers.txt file in the datafolder.
        """
        checked = set()
        try:
            with open("{}".format(self.checkedplayersfile), "r") as f:
                for line in f:
                    if line.strip() == "":
                        continue
                    checked.add(int(line.strip()))
        except IOError:
            f = open("{}".format(self.checkedplayersfile), "w")
            f.close()
        return checked

    def getCheckedGames(self):
        """
        same as getCheckedPlayers, but with games
        """
        checked = set()
        try:
            with open("{}".format(self.checkedgamesfile), "r") as f:
                for line in f:
                    if line.strip() == "":
                        continue
                    checked.add(int(line.strip()))
        except IOError:
            f = open("{}".format(self.checkedgamesfile), "w")
            f.close()
        return checked

    def getAverageTier(self, participants):
        tiers = self.getSummonerTiers(participants)
        tl = [tiers[s].lower() for s in tiers]
        divisions = self.divisions[:-1]
        high = 0
        hightier = None
        for div in divisions:
            num = tl.count(div)
            if num >= high:
                high = num
                hightier = div
        return hightier, tiers

    def getData(self, rankedqueues="TEAM_BUILDER_DRAFT_RANKED_5x5,RANKED_SOLO_5x5"):
        """
        """
        gamenumber = 0
        summoner = self.getSummonerId(self.seedplayer)
        h, tier = self.getAverageTier([summoner])
        tier = tier[str(summoner)]
        self.tocheck[str(tier).lower()].append(summoner)
        # matchlist = self.getMatchHistory(sumid, rankedqueues=rankedqueues, begintime=begintime, endtime=endtime).json()
        # matchset = {x["matchId"] for x in matchlist["matches"]}
        # todomatches = matchset - self.checkedgames
        # print(todomatches)
        # self.checkedplayers.add(int(sumid))
        # with open(self.checkedplayersfile, "a") as f:
        #     f.write("{}".format(summoner))
        cycle = 0
        while True:
            checked = True
            while checked:
                divcheck = self.divisions[(cycle % len(self.divisions[:-1]))]
                if len(self.tocheck[divcheck]) == 0:
                    cycle += 1
                    continue
                else:
                    summoner = self.tocheck[divcheck].pop()
                    if summoner in self.checkedplayers:
                        continue
                print("Getting matches list for summoner id: {}.".format(summoner))
                matchlist = self.getMatchHistory(summoner, seasons=self.season, rankedqueues=rankedqueues, begintime=self.patch, endtime=self.endtime).json()
                todomatches = [x["matchId"] for x in matchlist["matches"]]
                print("Adding {} to checkedplayers set and file.".format(summoner))
                self.checkedplayers.add(int(summoner))
                with open(self.checkedplayersfile, "a") as f:
                    f.write("{}\n".format(summoner))
                checked = False
                cycle += 1
            for game in todomatches:
                if game not in self.checkedgames:
                    try:
                        gamenumber += 1
                        print("Game number {}.".format(gamenumber))
                        print("Retrieving data for match {}.".format(game))
                        rawdata = self.getMatch(game).json()
                        participants = [str(x["player"]["summonerId"]) for x in rawdata["participantIdentities"]]
                        tiers = self.getSummonerTiers(participants)
                        g = Game(rawdata, tiers, self.champId, self.spells)
                        gametier, tiers = self.getAverageTier(g.participants)
                        print("Adding {} to checkedgamesfile and set.".format(game))
                        self.checkedgames.add(game)
                        with open(self.checkedgamesfile, "a") as f:
                            f.write("{}\n".format(game))
                        if not os.path.isfile(self.datafiles[gametier]):
                            with open(self.datafiles[gametier], "w") as f:
                                writer = csv.DictWriter(f, fieldnames=g.headers, lineterminator="\n")
                                writer.writeheader()
                        print("Adding game data to datafile.")
                        written = False
                        while not written:
                            try:
                                with open(self.datafiles[gametier], "a") as f:
                                    writer = csv.DictWriter(f, fieldnames=g.headers, lineterminator="\n")
                                    writer.writerow(g.data)
                                    written = True
                            except Exception as e:
                                print(e)
                                raw_input("Error writing file. Press enter to continue.")
                        for p in tiers:
                            if len(self.tocheck[str(tiers[p]).lower()]) < self.maxdivsize:
                                self.tocheck[str(tiers[p]).lower()].append(p)
                    except Exception as e:
                        print("Error in current game.  Continuing to next.")
                        print(e)
                        continue
                else:
                    print("Skipping {}.  Already in checked games.".format(game))
                    gamenumber += 1


class Game():

    def __init__(self, gamedata, tiers, champId, spells, includeingamedata=True):
        """
        includeingamedata      - whether or not to keep track of in game data
        """
        # super(self.__class__, self).__init__()
        self.gamedata = gamedata
        self.headers = None
        self.data = None
        self.participants = None
        self.includeingamedata = includeingamedata
        self.tiers = tiers
        self.champId = champId
        self.spells = spells
        self.extractData()

    def extractData(self):
        g = self.gamedata
        datalist = []
        data = {}
        datalist.append("matchDuration")
        data["matchDuration"] = g["matchDuration"]
        participants = [str(x["player"]["summonerId"]) for x in g["participantIdentities"]]
        tiers = self.tiers
        ps = g["participants"]
        maxchamp = int(max(self.champId, key=lambda x: int(x)))
        maxspell = max(self.spells)
        # print(maxchamp)
        for p in ps:
            champion = p["championId"]
            pid = p["participantId"]
            # masteries = p["masteries"]
            # runes = p["runes"]
            spell1 = p["spell1Id"]
            spell2 = p["spell2Id"]
            teamid = p["teamId"]
            # lane = p["timeline"]["lane"]  # not implemented
            # role = p["timeline"]["role"]  # not implemented
            # Add data to dictionary and list
            tp = "t{}:p{}".format(teamid, pid)
            # champion
            # print([("{}:champ{}".format(tp, x+1), "0") for x in range(len(self.champName))])
            # data.update(dict([("{}:champ{}".format(tp, x+1), "0") for x in range(maxchamp)]))
            champs = {}
            for i in range(maxchamp + 1):
                if str(i) in self.champId:
                    champs["{}:champ{}".format(tp, i)] = "0"
                    datalist.append("{}:champ{}".format(tp, i))
            data.update(champs)
            data["{}:champ{}".format(tp, str(champion))] = "1"

            # spell 1
            spelldict1 = {}
            spelldict2 = {}
            for i in range(maxspell + 1):
                if i in self.spells:
                    spelldict1["{}:spell1{}".format(tp, i)] = "0"
                    datalist.append("{}:spell1{}".format(tp, i))
            spelldict1["{}:spell1{}".format(tp, str(spell1))] = "1"
            data.update(spelldict1)

            # spell2
            for i in range(maxspell + 1):
                if i in self.spells:
                    spelldict2["{}:spell2{}".format(tp, i)] = 0
                    datalist.append("{}:spell2{}".format(tp, i))
            spelldict2["{}:spell1{}".format(tp, str(spell2))] = "1"
            data.update(spelldict2)

        for team in g["teams"]:
            tid = "t{}".format(team["teamId"])
            win = team["winner"]
            firstBaron = team["firstBaron"]
            firstDragon = team["firstDragon"]
            firstTower = team["firstTower"]
            firstInhibitor = team["firstInhibitor"]
            firstRiftHerald = team["firstRiftHerald"]
            firstBlood = team["firstBlood"]
            # add data to dictionary and list
            data["{}win".format(tid)] = "1" if win else "0"
            if self.includeingamedata:
                data["{}firstbaron".format(tid)] = "1" if firstBaron else "0"
                datalist.append("{}firstbaron".format(tid))
                data["{}firstdragon".format(tid)] = "1" if firstDragon else "0"
                datalist.append("{}firstdragon".format(tid))
                data["{}firsttower".format(tid)] = "1" if firstTower else "0"
                datalist.append("{}firsttower".format(tid))
                data["{}firstinhibitor".format(tid)] = "1" if firstInhibitor else "0"
                datalist.append("{}firstinhibitor".format(tid))
                data["{}firstriftherald".format(tid)] = "1" if firstRiftHerald else "0"
                datalist.append("{}firstriftherald".format(tid))
                data["{}firstblood".format(tid)] = "1" if firstBlood else "0"
                datalist.append("{}firstblood".format(tid))
        datalist.append("t100win")
        datalist.append("t200win")

        self.headers = datalist
        self.data = data
        self.participants = participants




def main():
    # elo = Elo("brianjp93", "test", patch="6.2", endtime=str(int(time.time())*1000))
    # elo = Elo("brianjp93", "test", patch="6.2", endtime=None)
    seedplayer = sys.argv[1]
    elo = Elo(seedplayer, "patch6.4", season="SEASON2016", patch="6.4")
    elo.getData()

if __name__ == '__main__':
    main()
