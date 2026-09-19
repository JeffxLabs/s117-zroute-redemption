#!/usr/bin/env python3
"""
Process Capitol War Event Data.
Generates structured JSON, CSV, and summary metrics for the interactive GitHub Pages site.
"""
import json
import csv
import os
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_alliance_tag(alliance_str):
    if not alliance_str:
        return "", "No Alliance"
    m = re.match(r'^\[(.*?)\]\s*(.*)$', alliance_str.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", alliance_str.strip()

def detect_server(alliance_str):
    if not alliance_str:
        return "117"
    if "S119" in alliance_str:
        return "119"
    if "S113" in alliance_str:
        return "113"
    if "S117" in alliance_str:
        return "117"
    # Unlabelled alliances belong to home server S117
    return "117"

def process_event(event_id, title, date_str, opponent_server, raw_json_path):
    event_dir = os.path.join(BASE_DIR, "events", event_id)
    os.makedirs(event_dir, exist_ok=True)

    with open(raw_json_path, "r", encoding="utf-8") as f:
        raw_players = json.load(f)

    processed_players = []
    alliance_map = defaultdict(lambda: {
        "tag": "",
        "name": "",
        "server": "117",
        "full_name": "",
        "members": [],
        "total_points": 0
    })

    server_totals = defaultdict(lambda: {"players": 0, "points": 0})

    for p in raw_players:
        rank = p["rank"]
        cmd = p["commander"].strip()
        ally_raw = p["alliance"].strip() if p.get("alliance") else ""
        pts = p["points"]

        tag, name = parse_alliance_tag(ally_raw)
        srv = detect_server(ally_raw)

        # Standardize alliance display name without redundant trailing server tag if present
        clean_ally_name = re.sub(r'\s*S\d+\s*$', '', name).strip() if name else ""

        full_display = f"[{tag}] {clean_ally_name}".strip() if tag else (clean_ally_name or "No Alliance")

        player_record = {
            "rank": rank,
            "commander": cmd,
            "alliance": full_display,
            "alliance_tag": tag,
            "alliance_name": clean_ally_name,
            "server": srv,
            "points": pts
        }
        processed_players.append(player_record)

        # Alliance aggregation
        ally_key = full_display
        alliance_map[ally_key]["tag"] = tag
        alliance_map[ally_key]["name"] = clean_ally_name or "No Alliance"
        alliance_map[ally_key]["full_name"] = full_display
        alliance_map[ally_key]["server"] = srv
        alliance_map[ally_key]["total_points"] += pts
        alliance_map[ally_key]["members"].append({
            "rank": rank,
            "commander": cmd,
            "points": pts
        })

        # Server aggregation
        server_totals[srv]["players"] += 1
        server_totals[srv]["points"] += pts

    # Sort alliances by total points
    sorted_alliances = []
    for ally_key, data in alliance_map.items():
        sorted_members = sorted(data["members"], key=lambda m: m["points"], reverse=True)
        top_member = sorted_members[0] if sorted_members else {"commander": "None", "points": 0, "rank": 0}
        count = len(sorted_members)
        avg_pts = data["total_points"] // count if count > 0 else 0
        sorted_alliances.append({
            "alliance": data["full_name"],
            "tag": data["tag"],
            "name": data["name"],
            "server": data["server"],
            "members_count": count,
            "total_points": data["total_points"],
            "avg_points": avg_pts,
            "top_commander": top_member["commander"],
            "top_points": top_member["points"],
            "top_rank": top_member["rank"],
            "members": sorted_members
        })

    sorted_alliances.sort(key=lambda a: a["total_points"], reverse=True)
    for idx, a in enumerate(sorted_alliances, 1):
        a["rank"] = idx

    total_pts = sum(p["points"] for p in processed_players)

    event_meta = {
        "id": event_id,
        "title": title,
        "date": date_str,
        "home_server": "117",
        "opponent_server": opponent_server,
        "total_players": len(processed_players),
        "total_points": total_pts,
        "unique_alliances": len(sorted_alliances),
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

    # Save to event directory
    with open(os.path.join(event_dir, "event.json"), "w", encoding="utf-8") as f:
        json.dump(event_meta, f, indent=2, ensure_ascii=False)

    with open(os.path.join(event_dir, "rankings.json"), "w", encoding="utf-8") as f:
        json.dump(processed_players, f, indent=2, ensure_ascii=False)

    with open(os.path.join(event_dir, "alliances.json"), "w", encoding="utf-8") as f:
        json.dump(sorted_alliances, f, indent=2, ensure_ascii=False)

    with open(os.path.join(event_dir, "rankings.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Commander", "Alliance", "Server", "Points"])
        for p in processed_players:
            writer.writerow([p["rank"], p["commander"], p["alliance"], f"S{p['server']}", p["points"]])

    with open(os.path.join(event_dir, "alliances.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Alliance", "Server", "Members", "Total Points", "Avg Points/Player", "Top Commander", "Top Commander Points"])
        for a in sorted_alliances:
            writer.writerow([a["rank"], a["alliance"], f"S{a['server']}", a["members_count"], a["total_points"], a["avg_points"], a["top_commander"], a["top_points"]])

    # Generate embedded JS file for offline/file:// local execution without CORS issues
    with open(os.path.join(event_dir, "event_data.js"), "w", encoding="utf-8") as f:
        f.write(f"window.EVENT_{event_id.replace('-', '_')} = {{\n")
        f.write(f"  meta: {json.dumps(event_meta, ensure_ascii=False)},\n")
        f.write(f"  alliances: {json.dumps(sorted_alliances, ensure_ascii=False)},\n")
        f.write(f"  rankings: {json.dumps(processed_players, ensure_ascii=False)}\n")
        f.write("};\n")

    # Update root data copies for backwards compatibility
    with open(os.path.join(BASE_DIR, "data", "capitol_event_rankings.json"), "w", encoding="utf-8") as f:
        json.dump(processed_players, f, indent=2, ensure_ascii=False)
    with open(os.path.join(BASE_DIR, "data", "capitol_event_rankings.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Commander", "Alliance", "Server", "Points"])
        for p in processed_players:
            writer.writerow([p["rank"], p["commander"], p["alliance"], f"S{p['server']}", p["points"]])
    with open(os.path.join(BASE_DIR, "data", "alliance_summary.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Alliance", "Server", "Members", "Total Points", "Avg Points/Player", "Top Commander", "Top Commander Points"])
        for a in sorted_alliances:
            writer.writerow([a["rank"], a["alliance"], f"S{a['server']}", a["members_count"], a["total_points"], a["avg_points"], a["top_commander"], a["top_points"]])

    # Update events manifest
    manifest_path = os.path.join(BASE_DIR, "events", "manifest.json")
    manifest = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as mf:
                manifest = json.load(mf)
        except Exception:
            manifest = []
    
    # Update or append event
    existing_idx = next((i for i, e in enumerate(manifest) if e["id"] == event_id), None)
    summary_entry = {
        "id": event_id,
        "title": title,
        "date": date_str,
        "home_server": "117",
        "opponent_server": opponent_server,
        "total_players": len(processed_players),
        "total_points": total_pts,
        "top_alliance": sorted_alliances[0]["alliance"] if sorted_alliances else "",
        "top_commander": processed_players[0]["commander"] if processed_players else ""
    }
    if existing_idx is not None:
        manifest[existing_idx] = summary_entry
    else:
        manifest.insert(0, summary_entry)

    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2, ensure_ascii=False)

    # Write manifest JS for offline file:// support
    with open(os.path.join(BASE_DIR, "events", "manifest.js"), "w", encoding="utf-8") as mfjs:
        mfjs.write(f"window.EVENTS_MANIFEST = {json.dumps(manifest, indent=2, ensure_ascii=False)};\n")

    print(f"Successfully processed event '{event_id}' ({len(processed_players)} players, {len(sorted_alliances)} alliances).")

if __name__ == "__main__":
    process_event(
        event_id="2026-09-19-s117-vs-s119",
        title="Capitol War: Server 117 vs Server 119",
        date_str="2026-09-19",
        opponent_server="119",
        raw_json_path=os.path.join(BASE_DIR, "data", "capitol_event_rankings.json")
    )
