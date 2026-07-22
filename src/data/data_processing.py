import json
import lzma
import math
from pathlib import Path

import polars as pl

FILENAME = "./collected_data.csv"


def read_parsed_demo(filename):
    with lzma.LZMAFile(filename, "rb") as f:
        d = json.load(f)
        return d


def bearings(x1, x2, y1, y2):
    attacker_angle = (math.degrees(math.atan2(y2 - y1, x2 - x1)) + 360) % 360
    victim_angle = (math.degrees(math.atan2(y1 - y2, x1 - x2)) + 360) % 360
    return attacker_angle, victim_angle


def vel_angle(x, y):
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def vert_ang_dist(distance, z1, z2):
    if distance == 0.0:
        print(
            f"Distance is 0 in vertical angle distance!!!."\
            f"Z1 and Z2 are {z1} and {z2} respectively."
        )
        return math.degrees(math.asin((z2 - z1) / 0.00001))
    angle = math.degrees(math.asin((z2 - z1) / distance))
    return angle


def distance(x1, x2, y1, y2, z1, z2):
    return math.sqrt(((x2 - x1) ** 2) + ((y2 - y1) ** 2) + ((z2 - z1) ** 2))


def make_dict(data):
    kills = {
        "kill_tick": [],
        "kill_seconds": [],
        "duel_tick": [],
        "duel_seconds": [],
        "distance": [],
        "attacker_vel": [],
        "attacker_vel_dir": [],
        "attacker_vz": [],
        "attacker_side": [],
        "attacker_hp": [],
        "attacker_helmet": [],
        "attacker_armor": [],
        "attacker_spotted": [],
        "attacker_angle": [],
        "attacker_vert_angle": [],
        "attacker_blinded": [],
        "attacker_weapon": [],
        "victim_vel": [],
        "victim_vel_dir": [],
        "victim_vz": [],
        "victim_hp": [],
        "victim_helmet": [],
        "victim_armor": [],
        "victim_spotted": [],
        "victim_angle": [],
        "victim_vert_angle": [],
        "victim_blinded": [],
        "victim_weapon": [],
    }
    for round in data["gameRounds"]:
        for kill in round["kills"]:
            if kill["isTeamkill"] or kill["isSuicide"]:
                continue

            tick = kill["tick"]
            seconds = kill["seconds"]

            attacker_name = kill["attackerName"]
            attacker_side = str(kill["attackerSide"]).lower()

            victim_name = kill["victimName"]
            victim_side = kill["victimSide"].lower()

            kills["kill_tick"].append(tick)
            kills["kill_seconds"].append(seconds)

            kills["attacker_side"].append(attacker_side)

            kills["attacker_weapon"].append(str(kill["weapon"]))

            players = {kill["attackerName"], kill["victimName"]}
            time = kill["seconds"]
            damage_time = time
            for damage in round["damages"]:
                if (
                    time - 3 < damage["seconds"] <= time
                    and damage["attackerName"] in players
                    and damage["victimName"] in players
                ):
                    damage_time = damage["seconds"]
                    break
            i = -1
            while (
                i + 1 < len(round["frames"])
                and round["frames"][i + 1]["seconds"] < damage_time
            ):
                i += 1
            frame = round["frames"][i]
            kills["duel_tick"].append(frame["tick"])
            kills["duel_seconds"].append(frame["seconds"])

            for player in frame[attacker_side]["players"]:
                if player["name"] == attacker_name:
                    attacker = player
            if not attacker:
                raise KeyError

            for player in frame[victim_side]["players"]:
                if player["name"] == victim_name:
                    victim = player
            if not victim:
                raise KeyError

            kills["attacker_hp"].append(attacker["hp"])
            kills["victim_hp"].append(victim["hp"])

            if attacker["armor"] > 0:
                kills["attacker_armor"].append(True)
            else:
                kills["attacker_armor"].append(False)

            if victim["armor"] > 0:
                kills["victim_armor"].append(True)
            else:
                kills["victim_armor"].append(False)

            kills["attacker_helmet"].append(attacker["hasHelmet"])
            kills["victim_helmet"].append(victim["hasHelmet"])

            kills["attacker_blinded"].append(attacker["isBlinded"])
            kills["victim_blinded"].append(victim["isBlinded"])

            attacker_bearing, victim_bearing = bearings(
                attacker["x"], victim["x"], attacker["y"], victim["y"]
            )

            kills["attacker_angle"].append(abs(attacker_bearing - attacker["viewX"]))
            kills["victim_angle"].append(abs(victim_bearing - victim["viewX"]))

            dist = distance(
                attacker["x"],
                victim["x"],
                attacker["y"],
                victim["y"],
                attacker["z"],
                victim["z"],
            )
            kills["distance"].append(dist)

            vert_angle = vert_ang_dist(dist, attacker["z"], victim["z"])
            kills["attacker_vert_angle"].append(vert_angle)
            kills["victim_vert_angle"].append(-1 * vert_angle)

            kills["attacker_spotted"].append(
                True if len(attacker["spotters"]) > 0 else False
            )
            kills["victim_spotted"].append(
                True if len(victim["spotters"]) > 0 else False
            )

            kills["victim_weapon"].append(str(victim["activeWeapon"]))

            kills["attacker_vz"].append(attacker["velocityZ"])
            kills["victim_vz"].append(victim["velocityZ"])

            kills["attacker_vel"].append(
                math.sqrt(attacker["velocityX"] ** 2 + attacker["velocityY"] ** 2)
            )
            kills["victim_vel"].append(
                math.sqrt(victim["velocityX"] ** 2 + victim["velocityY"] ** 2)
            )

            kills["attacker_vel_dir"].append(
                vel_angle(attacker["velocityX"], attacker["velocityY"])
            )
            kills["victim_vel_dir"].append(
                vel_angle(victim["velocityX"], victim["velocityY"])
            )
    return kills


def create_csv(data):
    dir = Path(__file__).parent
    rel_path = FILENAME

    path = dir.joinpath(rel_path)

    df = pl.DataFrame(
        data=data,
        schema=[
            ("kill_tick", pl.Int32),
            ("kill_seconds", pl.Float64),
            ("duel_tick", pl.Int32),
            ("duel_seconds", pl.Float64),
            ("distance", pl.Float64),
            ("attacker_vel", pl.Float64),
            ("attacker_vel_dir", pl.Float64),
            ("attacker_vz", pl.Float64),
            ("attacker_side", pl.String),
            ("attacker_hp", pl.Int16),
            ("attacker_helmet", pl.Boolean),
            ("attacker_armor", pl.Boolean),
            ("attacker_spotted", pl.Boolean),
            ("attacker_angle", pl.Float64),
            ("attacker_vert_angle", pl.Float64),
            ("attacker_blinded", pl.Boolean),
            ("attacker_weapon", pl.String),
            ("victim_vel", pl.Float64),
            ("victim_vel_dir", pl.Float64),
            ("victim_vz", pl.Float64),
            ("victim_hp", pl.Int16),
            ("victim_helmet", pl.Boolean),
            ("victim_armor", pl.Boolean),
            ("victim_spotted", pl.Boolean),
            ("victim_angle", pl.Float64),
            ("victim_vert_angle", pl.Float64),
            ("victim_blinded", pl.Boolean),
            ("victim_weapon", pl.String),
        ],
        orient="row",
    )

    df.write_csv(path, separator=",", include_header=True)


def update_csv(data):
    dir = Path(__file__).parent
    rel_path = FILENAME

    path = dir.joinpath(rel_path)

    df = pl.DataFrame(
        data=data,
        schema=[
            ("kill_tick", pl.Int32),
            ("kill_seconds", pl.Float64),
            ("duel_tick", pl.Int32),
            ("duel_seconds", pl.Float64),
            ("distance", pl.Float64),
            ("attacker_vel", pl.Float64),
            ("attacker_vel_dir", pl.Float64),
            ("attacker_vz", pl.Float64),
            ("attacker_side", pl.String),
            ("attacker_hp", pl.Int16),
            ("attacker_helmet", pl.Boolean),
            ("attacker_armor", pl.Boolean),
            ("attacker_spotted", pl.Boolean),
            ("attacker_angle", pl.Float64),
            ("attacker_vert_angle", pl.Float64),
            ("attacker_blinded", pl.Boolean),
            ("attacker_weapon", pl.String),
            ("victim_vel", pl.Float64),
            ("victim_vel_dir", pl.Float64),
            ("victim_vz", pl.Float64),
            ("victim_hp", pl.Int16),
            ("victim_helmet", pl.Boolean),
            ("victim_armor", pl.Boolean),
            ("victim_spotted", pl.Boolean),
            ("victim_angle", pl.Float64),
            ("victim_vert_angle", pl.Float64),
            ("victim_blinded", pl.Boolean),
            ("victim_weapon", pl.String),
        ],
        orient="row",
    )

    with open(path, mode="a") as f:
        df.write_csv(f, separator=",", include_header=False)


def main():
    dir = Path(__file__).parent
    rel = "./files.txt"
    path = dir.joinpath(rel)

    with open(path) as f:
        lines = f.readlines()
        for i in range(len(lines)):
            lines[i] = lines[i].replace("\n", "")

    print(lines[0])
    first_xz = "./esta/data/lan/0013db25-4444-452b-980b-7702dc6fb810.json.xz"
    create_path = dir.joinpath(first_xz)
    data = read_parsed_demo(create_path)
    kills = make_dict(data)
    create_csv(kills)
    count = 1
    for line in lines:
        relative = f"./esta/data/lan/{line}"
        new_path = dir.joinpath(relative)

        data = read_parsed_demo(new_path)
        kills = make_dict(data)
        update_csv(kills)
        print(f"updated! count = {count}")
        count += 1
    print("Completed")


def test_main():
    dir = Path(__file__).parent
    rel = "./esta/data/lan/0a5fb56f-de83-4e4c-8f9d-bf6f24d7f54a.json.xz"
    path = dir.joinpath(rel)
    df = read_parsed_demo(path)
    players = {
        df["gameRounds"][0]["kills"][0]["attackerName"],
        df["gameRounds"][0]["kills"][0]["victimName"],
    }
    time = df["gameRounds"][0]["kills"][0]["seconds"]
    for damage in df["gameRounds"][0]["damages"]:
        if (
            time - 3 < damage["seconds"] <= time
            and damage["attackerName"] in players
            and damage["victimName"] in players
        ):
            print(
                f"Duel between attacker {damage['attackerName']}"\
                f"and victim {damage['victimName']} starts at"\
                f"{damage['seconds']} seconds"
            )
            damage_time = damage["seconds"]
            break
    i = -1
    while (
        i + 1 < len(df["gameRounds"][0]["frames"])
        and df["gameRounds"][0]["frames"][i + 1]["seconds"] < damage_time
    ):
        i += 1
    print(df["gameRounds"][0]["frames"][i])


if __name__ == "__main__":
    main()
