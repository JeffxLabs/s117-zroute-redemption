import subprocess
import threading
import time
import json
import re
import os
import csv
import sys

SCRATCH = "/Users/jeff/.gemini/antigravity-cli/brain/83d4817d-dbc1-4088-88a4-4ffa9f4ec040/scratch"
OCR_BIN = os.path.join(SCRATCH, "vision_ocr")
ADB = "/opt/homebrew/bin/adb"
DEVICE = "127.0.0.1:5565"
OUTPUT_CSV = "/Users/jeff/capitol_event_rankings.csv"
OUTPUT_JSON = "/Users/jeff/capitol_event_rankings.json"

def swipe_up_to_scroll_down():
    subprocess.run([ADB, "-s", DEVICE, "shell", "input", "swipe", "540", "1350", "540", "750", "500"])

def scroll_to_top():
    print("Scrolling to the top of the rankings...")
    for i in range(12):
        subprocess.run([ADB, "-s", DEVICE, "shell", "input", "swipe", "540", "500", "540", "1750", "180"])
        time.sleep(0.2)
    time.sleep(1.5)
    print("Reached top.")

def screencap(dest_path):
    with open(dest_path, "wb") as f:
        subprocess.run([ADB, "-s", DEVICE, "exec-out", "screencap", "-p"], stdout=f)

def parse_items_to_rows(items):
    rank_boxes = []
    points_boxes = []
    middle_boxes = []
    
    for it in items:
        x, y, w, h = it['x'], it['y'], it['width'], it['height']
        text = it['text'].strip()
        
        # Discard header and footer
        if y > 0.865 or y < 0.05:
            continue
            
        # Discard marquee broadcast banner (wide box spanning across screen)
        if w > 0.45 and x < 0.30:
            continue
            
        clean_num = re.sub(r'[^\d]', '', text)
        if x < 0.20 and clean_num and clean_num.isdigit():
            val = int(clean_num)
            if 1 <= val <= 3000:
                rank_boxes.append({'rank': val, 'y': y, 'h': h, 'x': x, 'raw': text})
        elif x > 0.73:
            pts_digits = re.sub(r'[^\d]', '', text)
            if pts_digits:
                points_boxes.append({'points': int(pts_digits), 'y': y, 'h': h, 'raw': text})
        elif 0.32 <= x <= 0.74:
            middle_boxes.append({'text': text, 'y': y, 'h': h, 'x': x})

    # Check for rank 2 if rank 1 and 3 are present but 2 wasn't recognized in rank column
    detected_ranks = {r['rank']: r for r in rank_boxes}
    if 1 in detected_ranks and 3 in detected_ranks and 2 not in detected_ranks:
        y1 = detected_ranks[1]['y']
        y3 = detected_ranks[3]['y']
        y2 = (y1 + y3) / 2.0
        rank_boxes.append({'rank': 2, 'y': y2, 'h': (detected_ranks[1]['h'] + detected_ranks[3]['h']) / 2.0, 'x': 0.08, 'raw': '2'})

    rows = []
    for r in rank_boxes:
        ry = r['y']
        # Find closest points box within +/- 0.045
        best_pt = None
        min_p_dist = 0.045
        for p in points_boxes:
            dist = abs(p['y'] - ry)
            if dist < min_p_dist:
                min_p_dist = dist
                best_pt = p['points']
                
        # Find middle boxes within +/- 0.042
        row_mid = [m for m in middle_boxes if abs(m['y'] - ry) <= 0.042]
        row_mid = sorted(row_mid, key=lambda m: m['y'], reverse=True)
        
        commander = ''
        alliance = ''
        if len(row_mid) == 1:
            commander = row_mid[0]['text']
        elif len(row_mid) >= 2:
            commander = row_mid[0]['text']
            alliance = ' '.join(m['text'] for m in row_mid[1:])
            
        center_dist = abs(ry - 0.45)
        score = 100 - center_dist * 50
        if best_pt is not None:
            score += 30
        if commander:
            score += 20
        if alliance:
            score += 10
            
        rows.append({
            'rank': r['rank'],
            'commander': commander,
            'alliance': alliance,
            'points': best_pt,
            'y': ry,
            'score': score
        })
    return rows

def save_current_results(results):
    sorted_ranks = sorted(results.keys())
    data = [results[r] for r in sorted_ranks]
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Player Name", "Player Alliance", "Points"])
        for r in sorted_ranks:
            item = results[r]
            writer.writerow([item['rank'], item['commander'], item['alliance'], item['points']])

def main():
    print("Starting Capitol Event ranking extraction...")
    scroll_to_top()
    
    results = {}
    last_max_rank = 0
    stagnant_count = 0
    max_frames = 350
    t_start = time.time()
    
    for frame in range(max_frames):
        img_path = os.path.join(SCRATCH, f"frame_{frame % 2}.png")
        screencap(img_path)
        
        # Launch swipe in background
        swipe_thread = threading.Thread(target=swipe_up_to_scroll_down)
        swipe_thread.start()
        
        # Concurrently perform OCR
        ocr_start = time.time()
        out = subprocess.check_output([OCR_BIN, img_path])
        items = json.loads(out)
        rows = parse_items_to_rows(items)
        
        # Merge rows into results
        for row in rows:
            rk = row['rank']
            if rk not in results:
                results[rk] = row
            else:
                curr = results[rk]
                # Update if new row has higher quality score or missing fields
                if row['score'] > curr['score']:
                    # If existing has points and new doesn't, keep existing points
                    if row['points'] is None and curr['points'] is not None:
                        row['points'] = curr['points']
                    if not row['commander'] and curr['commander']:
                        row['commander'] = curr['commander']
                    if not row['alliance'] and curr['alliance']:
                        row['alliance'] = curr['alliance']
                    results[rk] = row
                else:
                    if curr['points'] is None and row['points'] is not None:
                        curr['points'] = row['points']
                    if not curr['commander'] and row['commander']:
                        curr['commander'] = row['commander']
                    if not curr['alliance'] and row['alliance']:
                        curr['alliance'] = row['alliance']

        swipe_thread.join()
        time.sleep(0.15)
        
        cur_max = max(results.keys()) if results else 0
        if frame % 10 == 0 or cur_max != last_max_rank:
            sys.stdout.write(f"\r[Frame {frame:3d}] Max Rank: {cur_max:4d} | Collected: {len(results):4d} entries | Rate: {(time.time()-t_start)/(frame+1):.2f}s/frame")
            sys.stdout.flush()
            
        if cur_max == last_max_rank and cur_max > 50:
            stagnant_count += 1
            if stagnant_count >= 6:
                print(f"\nNo new ranks detected for 6 frames. Reached end of rankings at rank {cur_max}.")
                break
        else:
            stagnant_count = 0
            last_max_rank = cur_max
            
        if frame % 25 == 0 and frame > 0:
            save_current_results(results)

    print(f"\nFinished capture. Total frames: {frame+1}. Total entries: {len(results)}.")
    save_current_results(results)
    
    # Analyze gaps
    max_rk = max(results.keys()) if results else 0
    missing_ranks = [r for r in range(1, max_rk + 1) if r not in results]
    print(f"Total unique ranks collected: {len(results)} / {max_rk}")
    if missing_ranks:
        print(f"Missing {len(missing_ranks)} ranks: {missing_ranks[:20]}...")
    else:
        print("All ranks from 1 to", max_rk, "are captured with 0 missing entries!")

if __name__ == "__main__":
    main()
