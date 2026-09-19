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

    alliance_stats = defaultdict(lambda: {"count": 0, "points": 0, "players": []})
    server_stats = defaultdict(lambda: {"count": 0, "points": 0})

    for p in players:
        ally = p["alliance"].strip() if p["alliance"] else "No Alliance"
        alliance_stats[ally]["count"] += 1
        alliance_stats[ally]["points"] += p["points"]
        alliance_stats[ally]["players"].append(p)

        # Detect server
        if "S119" in ally:
            server_stats["Server 119"]["count"] += 1
            server_stats["Server 119"]["points"] += p["points"]
        elif "S113" in ally:
            server_stats["Server 113"]["count"] += 1
            server_stats["Server 113"]["points"] += p["points"]
        else:
            server_stats["Server 117 (Home / Unlabeled)"]["count"] += 1
            server_stats["Server 117 (Home / Unlabeled)"]["points"] += p["points"]

    sorted_alliances = sorted(alliance_stats.items(), key=lambda x: x[1]["points"], reverse=True)

    # Save alliance summary CSV
    with open(ALLIANCE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Alliance", "Participants", "Total Points", "Avg Points/Player", "Top Player", "Top Player Points"])
        for idx, (ally, stat) in enumerate(sorted_alliances, 1):
            top_p = max(stat["players"], key=lambda x: x["points"])
            avg_pts = stat["points"] // stat["count"]
            writer.writerow([idx, ally, stat["count"], stat["points"], avg_pts, top_p["commander"], top_p["points"]])

    print("=" * 80)
    print(f" CAPITOL EVENT WAR RANKINGS SUMMARY - S117 Z ROUTE: REDEMPTION")
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
    print(f"{'#':<3} | {'Alliance':<32} | {'Members':>7} | {'Total Points':>14} | {'Avg/Player':>12}")
    print("-" * 76)
    for idx, (ally, stat) in enumerate(sorted_alliances[:15], 1):
        avg = stat["points"] // stat["count"]
        print(f"{idx:<3} | {ally:<32} | {stat['count']:>7} | {stat['points']:>14,} | {avg:>12,}")

    print("\n[TOP 15 INDIVIDUAL COMMANDERS]")
    print(f"{'Rank':<5} | {'Commander':<22} | {'Alliance':<30} | {'Points':>12}")
    print("-" * 76)
    for p in players[:15]:
        print(f"{p['rank']:<5} | {p['commander']:<22} | {p['alliance']:<30} | {p['points']:>12,}")

if __name__ == "__main__":
    analyze()
