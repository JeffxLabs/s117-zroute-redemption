import json
import re

DATA_PATHS = [
    "/Users/jeff/s117-zroute-redemption/data/capitol_event_rankings.json",
    "/Users/jeff/capitol_event_rankings.json"
]

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

for path in DATA_PATHS:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_count = 0
    for d in data:
        a = d.get("alliance", "").strip()

        # Handle S119 trailing tags in normalization lookup
        base_a = re.sub(r'\s*S\d+\s*$', '', a).strip()
        has_s119 = "S119" in a
        has_s113 = "S113" in a

        if a in ALLIANCE_NORM:
            d["alliance"] = ALLIANCE_NORM[a]
            cleaned_count += 1
        elif base_a in ALLIANCE_NORM:
            norm_base = ALLIANCE_NORM[base_a]
            d["alliance"] = f"{norm_base} S119" if has_s119 else (f"{norm_base} S113" if has_s113 else norm_base)
            cleaned_count += 1

        # Fix rank 163 and 168
        if d["rank"] == 163 and d["commander"].startswith("[STLG]"):
            d["commander"] = "Commander_163"
            d["alliance"] = "[STLG] SteelLegion S119"
            cleaned_count += 1
        elif d["rank"] == 168 and d["commander"].startswith("[TSR2]"):
            d["commander"] = "Commander_168"
            d["alliance"] = "[TSR2] TheShardofReality2 S119"
            cleaned_count += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Cleaned {cleaned_count} entries in {path}")

