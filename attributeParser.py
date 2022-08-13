
from os.path import exists
import xml.etree.ElementTree as ET

def parse(config):
    path = config["path"]
    attributesxml = path + "\\user\\profiles\\default\\attributes.xml"
    if not exists(attributesxml):
        print(f"Not found: {attributesxml}")
        return
    with open(attributesxml, "r", encoding="utf-8") as f:
        tree = ET.parse(f)
        root = tree.getroot()
        attrdict = {x.attrib["name"]: x.attrib["value"] for x in root.findall("Attr")}
        teams = list(range(int(attrdict["MissionBagNumTeams"])))
        team_playercounts = [int(attrdict[f"MissionBagTeam_{x}_numplayers"]) for x in teams]

        players = []
        for team in teams:
            teamplayers = team_playercounts[team]
            for player in range(teamplayers):
                attributes = ["blood_line_name", "mmr", "profileid", "downedbyme", "downedme", "killedbyme", "killedme", "ispartner"]

                playerattrs = {x: attrdict[f"MissionBagPlayer_{team}_{player}_{x}"] for x in attributes}

                playerattrs["isOwnTeam"] = attrdict[f"MissionBagTeam_{team}_ownteam"] == "true"
                players.append((team, player, playerattrs))
        return players
