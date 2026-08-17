import csv
import json
from pathlib import Path
import sys

def main():
    prompts_dir = Path(r"c:\projects\OpenAI tool hack\prompts")
    if not prompts_dir.exists():
        print(f"Directory not found: {prompts_dir}")
        return

    csv_files = list(prompts_dir.glob("*_top100_deduped.csv"))
    
    if not csv_files:
        print("No matching CSV files found.")
        return

    cross_file_best = {} # model -> (best_score, prompt_id, file)

    for csv_path in csv_files:
        print(f"\nProcessing {csv_path.name}...")
        
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                continue
            
            rows = list(reader)

        if not rows:
            print("  Empty file.")
            continue

        # First pass to compute most metrics and find max_reward_per_second
        max_rps = 0.0
        parsed_rows = []
        for row in rows:
            try:
                # Extract values with safe fallbacks
                hit_rate = float(row.get('Mean_Hit_Pct', 0)) / 100.0
                k = float(row.get('Num_Turns', 0))
                raw_score = 16 * k + 2
                expected_raw = hit_rate * raw_score
                mean_time = float(row.get('Mean_Time_s', 0))
                
                # avoid division by zero
                mean_time = max(mean_time, 0.001)

                rps = expected_raw / mean_time
                if rps > max_rps:
                    max_rps = rps
                
                var_hit = hit_rate * (1 - hit_rate)
                selectivity = hit_rate / (var_hit + 1.0)
                cph = 3600.0 / mean_time
                esph = cph * expected_raw
                
                if hit_rate == 1.0: rel_tier = 'ELITE'
                elif hit_rate >= 0.8: rel_tier = 'HIGH'
                elif hit_rate >= 0.5: rel_tier = 'MED'
                elif hit_rate >= 0.2: rel_tier = 'LOW'
                else: rel_tier = 'WEAK'
                
                if mean_time < 3.0: speed_tier = 'FAST'
                elif mean_time < 8.0: speed_tier = 'MEDIUM'
                else: speed_tier = 'SLOW'

                parsed_row = dict(row)
                parsed_row['hit_rate'] = hit_rate
                parsed_row['K'] = k
                parsed_row['raw_score_per_fire'] = raw_score
                parsed_row['expected_raw_score'] = expected_raw
                parsed_row['reward_per_second'] = rps
                parsed_row['variance_hit'] = var_hit
                parsed_row['selectivity'] = selectivity
                parsed_row['candidates_per_hour'] = cph
                parsed_row['expected_score_per_hour'] = esph
                parsed_row['reliability_tier'] = rel_tier
                parsed_row['speed_tier'] = speed_tier
                parsed_rows.append(parsed_row)
            except Exception as e:
                print(f"  Error processing row: {e}")

        if not parsed_rows:
            continue
            
        if max_rps == 0:
            max_rps = 1.0 # prevent div by zero

        # Second pass to compute composite_rank_score
        for r in parsed_rows:
            crs = 0.5 * r['selectivity'] + 0.3 * (r['reward_per_second'] / max_rps) + 0.2 * r['hit_rate']
            r['composite_rank_score'] = crs

        # Sort by composite_rank_score descending
        parsed_rows.sort(key=lambda x: x['composite_rank_score'], reverse=True)

        # Output columns
        new_cols = [
            'hit_rate', 'K', 'raw_score_per_fire', 'expected_raw_score',
            'reward_per_second', 'variance_hit', 'selectivity', 'candidates_per_hour',
            'expected_score_per_hour', 'reliability_tier', 'speed_tier', 'composite_rank_score'
        ]
        out_fieldnames = fieldnames + new_cols

        out_name = csv_path.name.replace('.csv', '_analyzed.csv')
        out_path = csv_path.parent / out_name

        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=out_fieldnames)
            writer.writeheader()
            writer.writerows(parsed_rows)

        print(f"  Saved to {out_name}")
        print("  Top 10 Prompts by composite_rank_score:")
        print(f"  {'Prompt ID':<20} | {'Model':<10} | {'Hit%':<6} | {'Time(s)':<8} | {'Score':<8}")
        print("  " + "-"*65)
        for i, r in enumerate(parsed_rows[:10]):
            pid_val = r.get('Prompt ID', '')
            model_val = r.get('Model', '')
            try:
                hit_val = float(r.get('Mean_Hit_Pct', 0))
            except:
                hit_val = 0.0
            try:
                time_val = float(r.get('Mean_Time_s', 0))
            except:
                time_val = 0.0
            score_val = r['composite_rank_score']
            print(f"  {pid_val:<20} | {model_val:<10} | {hit_val:<6.1f} | {time_val:<8.2f} | {score_val:<8.4f}")
            
            # Update cross_file_best
            model = model_val if model_val else 'unknown'
            if model not in cross_file_best or score_val > cross_file_best[model][0]:
                cross_file_best[model] = (score_val, pid_val, csv_path.name)

    print("\n" + "="*50)
    print("CROSS-FILE SUMMARY (Highest Composite Score per Model)")
    print("="*50)
    if not cross_file_best:
        print("No models found.")
    else:
        for model, (score, pid, fname) in sorted(cross_file_best.items()):
            print(f"Model: {model:<15} | Prompt ID: {pid:<20} | Score: {score:.4f} | File: {fname}")

if __name__ == '__main__':
    main()
