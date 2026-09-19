#!/usr/bin/env python3
import json
import csv
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON = os.path.join(BASE_DIR, "data", "capitol_event_rankings.json")
DATA_CSV = os.path.join(BASE_DIR, "data", "capitol_event_rankings.csv")
ALLIANCE_CSV = os.path.join(BASE_DIR, "data", "alliance_summary.csv")

def analyze():
    with open(DATA_JSON, "r", encoding="utf-8") as f:
        players = json.load(f)

    total_players = len(players)
    total_points = sum(p["points"] for p in players)

    alliance_stats = defaultdict(lambda: {"count": 0, "points": 0, "players": [], "server": "117"})
    server_stats = defaultdict(lambda: {"count": 0, "points": 0})

    for p in players:
        ally = p["alliance"].strip() if p["alliance"] else "No Alliance"
        srv = p.get("server", "117")
        alliance_stats[ally]["count"] += 1
        alliance_stats[ally]["points"] += p["points"]
        alliance_stats[ally]["players"].append(p)
        alliance_stats[ally]["server"] = srv

        if srv == "119":
            server_stats["Server 119 (Visiting)"]["count"] += 1
            server_stats["Server 119 (Visiting)"]["points"] += p["points"]
        elif srv == "113":
            server_stats["Server 113 (Cross-server)"]["count"] += 1
            server_stats["Server 113 (Cross-server)"]["points"] += p["points"]
        else:
            server_stats["Server 117 (Home Server)"]["count"] += 1
            server_stats["Server 117 (Home Server)"]["points"] += p["points"]

    sorted_alliances = sorted(alliance_stats.items(), key=lambda x: x[1]["points"], reverse=True)

    print("=" * 80)
    print(" CAPITOL EVENT WAR RANKINGS SUMMARY - S117 Z ROUTE: REDEMPTION")
    print("=" * 80)
    print(f" Total Players:  {total_players:,}")
    print(f" Total Points:   {total_points:,}")
    print(f" Unique Alliances: {len(alliance_stats)}")
    print("-" * 80)

    print("\n[SERVER POINT DISTRIBUTION]")
    for srv, sdata in sorted(server_stats.items(), key=lambda x: x[1]["points"], reverse=True):
        pct = (sdata["points"] / total_points) * 100
        print(f"  {srv:<30}: {sdata['points']:>13,} pts ({pct:>5.1f}%) | {sdata['count']:>4} players")

    print("\n[TOP 15 ALLIANCES BY TOTAL POINTS]")
    print(f"{'#':<3} | {'Alliance':<32} | {'Server':<6} | {'Members':>7} | {'Total Points':>14} | {'Avg/Player':>12}")
    print("-" * 85)
    for idx, (ally, stat) in enumerate(sorted_alliances[:15], 1):
        avg = stat["points"] // stat["count"]
        print(f"{idx:<3} | {ally:<32} | S{stat['server']:<5} | {stat['count']:>7} | {stat['points']:>14,} | {avg:>12,}")

    print("\n[TOP 15 INDIVIDUAL COMMANDERS]")
    print(f"{'Rank':<5} | {'Commander':<22} | {'Alliance':<30} | {'Server':<6} | {'Points':>12}")
    print("-" * 85)
    for p in players[:15]:
        print(f"{p['rank']:<5} | {p['commander']:<22} | {p['alliance']:<30} | S{p['server']:<5} | {p['points']:>12,}")

if __name__ == "__main__":
    analyze()
