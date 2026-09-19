#!/usr/bin/env python3
import csv
import json
import os
import re
from collections import defaultdict, Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENT_DIR = os.path.join(BASE_DIR, "events", "2026-09-19-s117-vs-s119")
SCRATCH_CSV = os.path.join(BASE_DIR, "scratch_rankings.csv")

ALLIANCE_NORM = {
    "[P1MP] JU1CER": "[P1MP] JU1CE",
    "[P1MP]JU1CER": "[P1MP] JU1CE",
    "[P1MP]JU1CE": "[P1MP] JU1CE",
    "[7DS] Se7enDeàdlySinsR": "[7DS] Se7enDeàdlySins",
    "[cHIL] ChillEmpire": "[CHIL] ChillEmpire",
    "[CLAVI ВОЙНЫ": "[CLAV] ВОЙНЫ",
    "[CLAV] ВОЙНЫ-": "[CLAV] ВОЙНЫ",
    "[FBLL] DVDVDVD": "[FBL3] DVDVDVDC",
    "[HElI] DarkAl": "[HEII] DarkAl",
    "[Hhhh] Xpovoç": "[Hhhh] Xpovos",
    "[QCKJ QUICKREACTIONFORCE": "[QCK] QUICKREACTIONFORCE",
    "[RTRJ RETRO": "[RTR] RETRO",
    "TSKG] Horizon": "[SKG] Horizon",
    "UJQK] JQKKK": "[JQK] JQKKK",
    "UQK]JOKKK": "[JQK] JQKKK",
    "[19o] CandyClub": "[190] CandyClub",
    "[1BİR] XOXOX": "[1BiR] XOXOX",
    "[TІOX] ПоХуисты": "[TIOX] ПоХуисты",
    "Df] 아무이름이나붙이기": "[Df] 아무이름이나붙이기"
}

def parse_tag(alliance_str):
    if not alliance_str:
        return "", "No Alliance"
    m = re.match(r'^\[(.*?)\]\s*(.*)$', alliance_str.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", alliance_str.strip()

def main():
    with open(SCRATCH_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    players = []
    alliance_map = defaultdict(lambda: {
        "tag": "",
        "name": "",
        "full_name": "",
        "servers": Counter(),
        "members": [],
        "total_points": 0
    })

    server_totals = defaultdict(lambda: {"players": 0, "points": 0})

    for row in raw_rows:
        rank = int(row["Rank"])
        cmd = row["Commander"].strip()
        raw_ally = row["Alliance"].strip()
        raw_srv = row["Server"].strip().replace("S", "")
        pts = int(row["Points"])

        # Normalize alliance name
        norm_ally = ALLIANCE_NORM.get(raw_ally, raw_ally)
        base_ally = re.sub(r'\s*S\d+\s*$', '', norm_ally).strip()
        norm_ally = ALLIANCE_NORM.get(base_ally, base_ally)

        # Fix rank 163 and 168
        if rank == 163:
            cmd = "Commander_163"
            norm_ally = "[STLG] SteelLegion"
            raw_srv = "119"
        elif rank == 168:
            cmd = "Commander_168"
            norm_ally = "[TSR2] TheShardofReality2"
            raw_srv = "119"

        tag, name = parse_tag(norm_ally)
        full_display = f"[{tag}] {name}".strip() if tag else (name or "No Alliance")

        p_obj = {
            "rank": rank,
            "commander": cmd,
            "alliance": full_display,
            "alliance_tag": tag,
            "alliance_name": name,
            "server": raw_srv,
            "points": pts
        }
        players.append(p_obj)

        alliance_map[full_display]["tag"] = tag
        alliance_map[full_display]["name"] = name
        alliance_map[full_display]["full_name"] = full_display
        alliance_map[full_display]["servers"][raw_srv] += 1
        alliance_map[full_display]["total_points"] += pts
        alliance_map[full_display]["members"].append({
            "rank": rank,
            "commander": cmd,
            "points": pts,
            "server": raw_srv
        })

        server_totals[raw_srv]["players"] += 1
        server_totals[raw_srv]["points"] += pts

    total_pts = sum(p["points"] for p in players)

    # Process alliances
    alliances = []
    for ally_name, data in alliance_map.items():
        # Determine dominant server for this alliance
        dom_server = data["servers"].most_common(1)[0][0] if data["servers"] else "117"
        sorted_members = sorted(data["members"], key=lambda m: m["points"], reverse=True)
        top_p = sorted_members[0] if sorted_members else {"commander": "None", "points": 0, "rank": 0}
        count = len(sorted_members)
        avg_pts = data["total_points"] // count if count > 0 else 0

        alliances.append({
            "alliance": ally_name,
            "tag": data["tag"],
            "name": data["name"],
            "server": dom_server,
            "members_count": count,
            "total_points": data["total_points"],
            "avg_points": avg_pts,
            "top_commander": top_p["commander"],
            "top_points": top_p["points"],
            "top_rank": top_p["rank"],
            "members": sorted_members
        })

    alliances.sort(key=lambda a: a["total_points"], reverse=True)
    for idx, a in enumerate(alliances, 1):
        a["rank"] = idx

    event_meta = {
        "id": "2026-09-19-s117-vs-s119",
        "title": "Capitol War: Server 117 vs Server 119",
        "date": "2026-09-19",
        "home_server": "117",
        "opponent_server": "119",
        "total_players": len(players),
        "total_points": total_pts,
        "unique_alliances": len(alliances),
        "servers": {
            "117": {
                "name": "Server 117 (Home)",
                "players": server_totals["117"]["players"],
                "points": server_totals["117"]["points"],
                "point_share_pct": round((server_totals["117"]["points"] / total_pts) * 100, 2)
            },
            "119": {
                "name": "Server 119 (Visiting)",
                "players": server_totals["119"]["players"],
                "points": server_totals["119"]["points"],
                "point_share_pct": round((server_totals["119"]["points"] / total_pts) * 100, 2)
            },
            "113": {
                "name": "Server 113 (Cross-server)",
                "players": server_totals["113"]["players"],
                "points": server_totals["113"]["points"],
                "point_share_pct": round((server_totals["113"]["points"] / total_pts) * 100, 2)
            }
        }
    }

    # Save to events/2026-09-19-s117-vs-s119/
    with open(os.path.join(EVENT_DIR, "event.json"), "w", encoding="utf-8") as f:
        json.dump(event_meta, f, indent=2, ensure_ascii=False)
    with open(os.path.join(EVENT_DIR, "rankings.json"), "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
    with open(os.path.join(EVENT_DIR, "alliances.json"), "w", encoding="utf-8") as f:
        json.dump(alliances, f, indent=2, ensure_ascii=False)

    with open(os.path.join(EVENT_DIR, "rankings.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Commander", "Alliance", "Server", "Points"])
        for p in players:
            writer.writerow([p["rank"], p["commander"], p["alliance"], f"S{p['server']}", p["points"]])

    with open(os.path.join(EVENT_DIR, "alliances.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Alliance", "Server", "Members", "Total Points", "Avg Points/Player", "Top Commander", "Top Commander Points"])
        for a in alliances:
            writer.writerow([a["rank"], a["alliance"], f"S{a['server']}", a["members_count"], a["total_points"], a["avg_points"], a["top_commander"], a["top_points"]])

    with open(os.path.join(EVENT_DIR, "event_data.js"), "w", encoding="utf-8") as f:
        f.write("window.EVENT_2026_09_19_s117_vs_s119 = {\n")
        f.write(f"  meta: {json.dumps(event_meta, ensure_ascii=False)},\n")
        f.write(f"  alliances: {json.dumps(alliances, ensure_ascii=False)},\n")
        f.write(f"  rankings: {json.dumps(players, ensure_ascii=False)}\n")
        f.write("};\n")

    # Save to data/
    with open(os.path.join(BASE_DIR, "data", "capitol_event_rankings.json"), "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
    with open(os.path.join(BASE_DIR, "data", "capitol_event_rankings.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Commander", "Alliance", "Server", "Points"])
        for p in players:
            writer.writerow([p["rank"], p["commander"], p["alliance"], f"S{p['server']}", p["points"]])
    with open(os.path.join(BASE_DIR, "data", "alliance_summary.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Alliance", "Server", "Members", "Total Points", "Avg Points/Player", "Top Commander", "Top Commander Points"])
        for a in alliances:
            writer.writerow([a["rank"], a["alliance"], f"S{a['server']}", a["members_count"], a["total_points"], a["avg_points"], a["top_commander"], a["top_points"]])

    # Also update home copies
    with open("/Users/jeff/capitol_event_rankings.json", "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
    with open("/Users/jeff/capitol_event_rankings.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Commander", "Alliance", "Server", "Points"])
        for p in players:
            writer.writerow([p["rank"], p["commander"], p["alliance"], f"S{p['server']}", p["points"]])

    # Remove temporary scratch
    if os.path.exists(SCRATCH_CSV):
        os.remove(SCRATCH_CSV)

    print("Rebuild complete!")
    print(f"Total players: {len(players)}")
    print(f"Total alliances: {len(alliances)}")
    print(f"Server distribution:")
    for s, d in event_meta["servers"].items():
        print(f"  Server {s}: {d['players']} players | {d['points']:,} pts ({d['point_share_pct']}%)")
    print(f"\nTop Alliance: {alliances[0]['alliance']} ({alliances[0]['members_count']} members, {alliances[0]['total_points']:,} pts)")

if __name__ == "__main__":
    main()
