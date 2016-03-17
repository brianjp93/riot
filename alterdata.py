"""
alterdata.py
"""
from __future__ import division
import csv
import sys

class Alterchamp():

    ranks = ["bronze", "silver", "gold", "platinum", "diamond", "master", "challenger"]

    def __init__(self, folder):
        self.folder = folder

    def getIndeces(self, rank):
        champIndex = {}
        champs = []
        with open("{}/{}.csv".format(self.folder, rank), "r") as f:
            reader = csv.reader(f)
            i = 0
            for row in reader:
                if i == 0:
                    headers = row
                    break
        # print(headers[-8:-2])
        i = 0
        for ft in headers:
            if "t100:p1:champ" in ft:
                name = ft.split(":")[-1]
                champs.append(name)
                champIndex[name] = i
                i += 1
        return champs, champIndex

    def makeSpreadsheet(self, rank):
        champs, champIndex = self.getIndeces(rank)
        sheet = []
        with open("{}/{}.csv".format(self.folder, rank), "r") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                team1 = [0] * len(champs)
                team2 = [0] * len(champs)
                if i == 0:
                    headers = row
                else:
                    for j, ft in enumerate(row):
                        ftname = headers[j]
                        if "champ" in ftname:
                            if "t1" in ftname:
                                name = ftname.split(":")[-1]
                                if int(ft) == 1:
                                    team1[champIndex[name]] = 1
                            if "t2" in ftname:
                                name = ftname.split(":")[-1]
                                if int(ft) == 1:
                                    team2[champIndex[name]] = 1
                    sheet.append(team1 + row[-14:-8] + [row[-2]])
                    sheet.append(team1 + row[-8:-2] + [row[-1]])
        sheet = [champs + ["firstbaron", "firstdragon", "firsttower", "firstinhibitor", "firstriftherald", "firstblood", "win"]] + sheet
        with open("{}/{}/{}.csv".format(self.folder, "comboswgame", rank), "w") as f:
            writer = csv.writer(f, lineterminator="\n")
            for row in sheet:
                writer.writerow(row)
        with open("{}/{}/{}.csv".format(self.folder, "combos", rank), "w") as f:
            writer = csv.writer(f, lineterminator="\n")
            for row in sheet:
                writer.writerow(row[:-7] + [row[-1]])

    def writeAllSpreadsheets(self):
        for rank in self.ranks:
            self.makeSpreadsheet(rank)


def main(patch):
    alter = Alterchamp(patch)
    # champs, champIndex = alter.getIndeces("bronze")
    # alter.makeSpreadsheet("bronze")
    # print(champs)
    # print(champIndex)
    alter.writeAllSpreadsheets()


if __name__ == '__main__':
    patch = "patch" + sys.argv[1]
    main(patch)
