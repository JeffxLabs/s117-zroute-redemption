#!/usr/bin/env python3
"""
Data Cleaning & Normalization for Z Route: Redemption Capitol War Rankings.
Resolves OCR artifacts, consolidates alliances, and validates integrity.
"""
import re

ALLIANCE_NORMALIZATION_MAP = {
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

def parse_tag_and_name(alliance_str):
    if not alliance_str:
        return "", "No Alliance"
    m = re.match(r'^\[(.*?)\]\s*(.*)$', alliance_str.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", alliance_str.strip()

def clean_player_record(record, home_server="117", visiting_server="119"):
    rank = record["rank"]
    cmd = record.get("commander", "").strip()
    raw_ally = record.get("alliance", "").strip()
    pts = record.get("points")

    # Detect server directly from raw alliance string BEFORE stripping
    if f"S{visiting_server}" in raw_ally or visiting_server in raw_ally:
        server = visiting_server
    elif "S113" in raw_ally or "113" in raw_ally:
        server = "113"
    elif f"S{home_server}" in raw_ally:
        server = home_server
    else:
        # Unlabelled alliances belong to home server
        server = home_server

    # Handle shifted commander/alliance rows if OCR missed player name on top line
    if rank == 163 and cmd.startswith("[STLG]"):
        cmd = "Commander_163"
        raw_ally = "[STLG] SteelLegion S119"
        server = visiting_server
    elif rank == 168 and cmd.startswith("[TSR2]"):
        cmd = "Commander_168"
        raw_ally = "[TSR2] TheShardofReality2 S119"
        server = visiting_server

    # Strip trailing server identifier (e.g. S119)
    clean_ally = re.sub(r'\s*S\d+\s*$', '', raw_ally).strip()
    norm_ally = ALLIANCE_NORMALIZATION_MAP.get(clean_ally, clean_ally)

    tag, name = parse_tag_and_name(norm_ally)
    full_display = f"[{tag}] {name}".strip() if tag else (name or "No Alliance")

    return {
        "rank": rank,
        "commander": cmd,
        "alliance": full_display,
        "alliance_tag": tag,
        "alliance_name": name,
        "server": server,
        "points": pts
    }

def validate_dataset(records):
    """Perform mathematical and logical integrity checks on the dataset."""
    errors = []
    ranks = [r["rank"] for r in records]
    max_rank = max(ranks) if ranks else 0

    # 1. Missing ranks
    missing = [r for r in range(1, max_rank + 1) if r not in set(ranks)]
    if missing:
        errors.append(f"Missing {len(missing)} ranks: {missing[:15]}...")

    # 2. Empty commanders
    empty_cmds = [r["rank"] for r in records if not r.get("commander")]
    if empty_cmds:
        errors.append(f"Empty commander names at ranks: {empty_cmds[:15]}")

    # 3. None points
    none_pts = [r["rank"] for r in records if r.get("points") is None]
    if none_pts:
        errors.append(f"Missing points at ranks: {none_pts[:15]}")

    # 4. Monotonic points check
    non_monotonic = []
    for i in range(1, len(records)):
        p_prev = records[i-1]["points"]
        p_curr = records[i]["points"]
        if p_prev is not None and p_curr is not None and p_curr > p_prev:
            non_monotonic.append((records[i-1]["rank"], p_prev, records[i]["rank"], p_curr))

    if non_monotonic:
        errors.append(f"Non-monotonic points at {len(non_monotonic)} positions: {non_monotonic[:5]}")

    return errors
