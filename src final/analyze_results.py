import os
import glob
import pandas as pd
import re
import numpy as np
import time
import sys
import matplotlib.pyplot as plt
import seaborn as sns

# --- IMPORTS FOR RE-SIMULATION ---
try:
    import simulation
    import creature
    import genome
    import pybullet as p
    CAN_SIMULATE = True
except ImportError:
    print("\nCRITICAL WARNING: 'simulation.py' or 'creature.py' not found.")
    print("Tables requiring Fitness/Height (Re-simulation) will fail or be empty.")
    CAN_SIMULATE = False

# ==========================================
# CONFIGURATION
# ==========================================
root_dir = '.'  

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_experiment_dirs(root):
    """Finds all folders that contain 'test1', 'test2', and 'test3'."""
    exp_dirs = []
    for dirpath, dirnames, filenames in os.walk(root):
        if all(x in dirnames for x in ['test1', 'test2', 'test3']):
            exp_dirs.append(dirpath)
    return sorted(exp_dirs)

def save_table_image(df, filename):
    """Render a Pandas DataFrame as a clean PNG table with auto-fitting text."""
    if df.empty:
        return

    # 1. Calculate required width based on text length
    # We iterate through columns to find the longest string (header or cell)
    total_chars = 0
    for col in df.columns:
        # Header length
        header_len = len(str(col))
        # Max cell length (convert to string first, handle empty logic)
        if len(df) > 0:
            cell_len = df[col].astype(str).map(len).max()
        else:
            cell_len = 0
        total_chars += max(header_len, cell_len)

    # Heuristic: 0.15 inches per character usually fits 12pt font well
    # We add a buffer of 2 inches for margins
    w = max(10, total_chars * 0.15 + 2)
    h = max(3, (len(df) + 2) * 0.6) # 0.6 inches per row
    
    fig, ax = plt.subplots(figsize=(w, h))
    ax.axis('off')  # Hide axes
    
    # 2. Create the table
    # Round numbers to 3 decimals
    tbl = ax.table(cellText=df.round(3).values, 
                   colLabels=df.columns, 
                   loc='center',
                   cellLoc='center')
    
    # 3. Styling & Formatting
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(12)
    tbl.scale(1, 2.0)  # Increase row height (vertical padding)
    
    # CRITICAL: Auto-adjust column widths to fit content
    tbl.auto_set_column_width(col=list(range(len(df.columns))))
    
    # Add Title
    title_text = filename.replace(".png", "").replace("_", " ")
    plt.title(title_text, pad=20, fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      Saved Image: '{filename}' (Size: {w:.1f}x{h:.1f})")

def get_final_generation_stats(exp_path, sim_engine):
    """
    Loads the LAST generation elite from test1, test2, test3.
    Re-simulates to get Fitness & Height.
    Extracts Genes for Leg Count.
    Returns the AVERAGE of the 3 tests.
    """
    stats = {
        'fitness': [],
        'height': [],
        'leg_count': [],
        'leg_length': []
    }
    
    for test_folder in ['test1', 'test2', 'test3']:
        full_test_path = os.path.join(exp_path, test_folder)
        
        # Find the highest generation file
        csv_files = glob.glob(os.path.join(full_test_path, 'elite_*.csv'))
        if not csv_files: continue
        
        # Sort to find the last one (e.g., elite_49.csv)
        latest_file = max(csv_files, key=lambda f: int(re.search(r'elite_(\d+)\.csv', f).group(1)))
        
        try:
            # 1. Load DNA
            dna = genome.Genome.from_csv(latest_file)
            
            # 2. Extract Genes (Morphology)
            # Gene 7 = Leg Count, Gene 0 = Leg Length
            csv_data = pd.read_csv(latest_file, header=None)
            gene7 = csv_data.iloc[0, 7]
            gene0 = csv_data.iloc[0, 0]
            
            leg_count = int(4 + (gene7 * 8.99))
            leg_length = 0.5 + (gene0 * 1.5)
            
            stats['leg_count'].append(leg_count)
            stats['leg_length'].append(leg_length)

            # 3. Re-Simulate (Performance)
            if CAN_SIMULATE and sim_engine:
                cr = creature.Creature(gene_count=1)
                cr.update_dna(dna)
                
                # Run quick simulation (1000 steps)
                sim_engine.run_creature(cr, iterations=1000)
                
                stats['fitness'].append(cr.get_distance_travelled())
                stats['height'].append(getattr(cr, 'peak_z', 0))
            else:
                stats['fitness'].append(0)
                stats['height'].append(0)
                
        except Exception as e:
            print(f"Error processing {latest_file}: {e}")

    # Return Averages
    return {
        'avg_fitness': np.mean(stats['fitness']) if stats['fitness'] else 0,
        'avg_height': np.mean(stats['height']) if stats['height'] else 0,
        'avg_legs': np.mean(stats['leg_count']) if stats['leg_count'] else 0,
        'avg_length': np.mean(stats['leg_length']) if stats['leg_length'] else 0
    }

# ==========================================
# MAIN MENU
# ==========================================
print("="*50)
print("      EVOLUTIONARY ROBOTICS ANALYSIS TOOL")
print("="*50)
print("[1] Plot Single Metric (Graph over time)")
print("[2] Generate Report Tables (Summary PNGs + CSVs)")
choice = input("\nEnter choice (1 or 2): ").strip()

# ==========================================
# OPTION 2: GENERATE TABLES
# ==========================================
if choice == '2':
    print("\n--- GENERATING TABLES ---")
    if CAN_SIMULATE:
        print("Initializing Physics Engine (Headless)...")
        sim = simulation.Simulation(sim_id=0)
    else:
        sim = None

    all_exps = get_experiment_dirs(root_dir)
    data_rows = []

    print(f"Processing {len(all_exps)} experiments (Calculating Final Stats)...")
    
    for exp in all_exps:
        name = os.path.basename(exp)
        print(f"  > Analyzing {name}...", end="")
        stats = get_final_generation_stats(exp, sim)
        print(" Done.")
        
        row = stats
        row['Experiment'] = name
        data_rows.append(row)

    df = pd.DataFrame(data_rows)
    
    # --- TABLE 1: FITNESS VS HEIGHT (MISMATCH) ---
    print("\n[1/3] Generating 'Mismatch Table' (Exp 1-3)...")
    target_exps = ['Baseline', 'Experiment_2', 'Experiment_3'] 
    t1_df = df[df['Experiment'].str.contains('|'.join(target_exps), case=False)].copy()
    
    if not t1_df.empty:
        t1_cols = ['Experiment', 'avg_fitness', 'avg_height']
        t1_df = t1_df[t1_cols]
        t1_df.columns = ['Experiment', 'Avg Fitness Score', 'Avg Max Height (m)']
        
        base_name = "Table_1_Fitness_vs_Height_Mismatch"
        t1_df.to_csv(f"{base_name}.csv", index=False)
        save_table_image(t1_df, f"{base_name}.png")
    else:
        print("      Skipping Table 1 (No matching experiments found).")

    # --- TABLE 2: MORPHOLOGY COMPARISON ---
    print("\n[2/3] Generating 'Morphology Comparison'...")
    # Compare Exp 1 (Worm) vs Exp 6 (Sphere) vs Exp 7 (Spider)
    # Adjust filters as needed for your report logic
    t2_df = df[['Experiment', 'avg_fitness', 'avg_height', 'avg_legs', 'avg_length']].copy()
    t2_df.columns = ['Experiment', 'Fitness', 'Height (m)', 'Avg Leg Count', 'Avg Leg Length (m)']
    
    base_name_2 = "Table_2_Morphology_Comparison"
    t2_df.to_csv(f"{base_name_2}.csv", index=False)
    save_table_image(t2_df, f"{base_name_2}.png")

    # --- TABLE 3: BLIND VS SENSORY (EXP 7 vs 8) ---
    print("\n[3/3] Generating 'Blind vs Sensory'...")
    target_exps_3 = ['Experiment_7', 'Experiment_8']
    t3_df = df[df['Experiment'].str.contains('|'.join(target_exps_3), case=False)].copy()
    
    if not t3_df.empty:
        t3_df = t3_df[['Experiment', 'avg_fitness', 'avg_height']]
        t3_df.columns = ['Condition', 'Final Fitness', 'Final Height (m)']
        
        base_name_3 = "Table_3_Blind_vs_Sensory"
        t3_df.to_csv(f"{base_name_3}.csv", index=False)
        save_table_image(t3_df, f"{base_name_3}.png")
    else:
        print("      Skipping Table 3 (No matching experiments found).")

    print("\n[DONE] All tables generated successfully.")
    exit()

# ==========================================
# OPTION 1: ORIGINAL GRAPHING LOGIC
# ==========================================
COLUMN_NAMES = {
    -1: ">> FITNESS SCORE (Re-Simulated)",
    -2: ">> MAX HEIGHT (Re-Simulated)",
    0: "Leg Length (Gene 0)",     
    7: "Leg Count (Gene 7)",  
    15: "Control Amp (Gene 15)",
    16: "Control Freq (Gene 16)"
}

print(f"\nScanning '{root_dir}' for experiments...")
all_experiments = get_experiment_dirs(root_dir)

for i, exp in enumerate(all_experiments):
    print(f"[{i+1}] {os.path.basename(exp)}")

selection = input("\nEnter numbers to compare (e.g., '1 7 8') or ENTER for ALL: ").strip()
selected_experiments = []
if selection == "":
    selected_experiments = all_experiments
else:
    try:
        indices = [int(x) - 1 for x in selection.replace(',', ' ').split()]
        for idx in indices:
            if 0 <= idx < len(all_experiments):
                selected_experiments.append(all_experiments[idx])
    except:
        selected_experiments = all_experiments

print("\nSelect Metric to Graph:")
for k, v in COLUMN_NAMES.items():
    print(f"[{k:<2}] {v}")
try:
    col_idx = int(input("Choice: "))
except:
    col_idx = 0

metric_name = COLUMN_NAMES.get(col_idx, f"Metric {col_idx}")
print(f"\nProcessing {metric_name}...")

if col_idx < 0 and CAN_SIMULATE:
    sim = simulation.Simulation(sim_id=0)

plot_data = []
for exp_path in selected_experiments:
    exp_name = os.path.basename(exp_path)
    gen_data = {} 

    print(f"  {exp_name}...", end="")
    for test_folder in ['test1', 'test2', 'test3']:
        full_test_path = os.path.join(exp_path, test_folder)
        csv_files = glob.glob(os.path.join(full_test_path, 'elite_*.csv'))
        
        for f in csv_files:
            try:
                match = re.search(r'elite_(\d+)\.csv', f)
                if not match: continue
                gen = int(match.group(1))

                if col_idx < 0:
                    dna = genome.Genome.from_csv(f)
                    cr = creature.Creature(gene_count=1)
                    cr.update_dna(dna)
                    sim.run_creature(cr, iterations=1000) 
                    val = cr.get_distance_travelled() if col_idx == -1 else getattr(cr, 'peak_z', 0)
                else:
                    df_csv = pd.read_csv(f, header=None)
                    raw_val = df_csv.iloc[0, col_idx]
                    if col_idx == 0: val = 0.5 + (raw_val * 1.5)
                    elif col_idx == 7: val = int(4 + (raw_val * 8.99))
                    else: val = raw_val

                if gen not in gen_data: gen_data[gen] = []
                gen_data[gen].append(val)
            except: pass
    print(" Done.")

    for gen, values in gen_data.items():
        if values:
            plot_data.append({'Experiment': exp_name, 'Generation': gen, 'Average Value': np.mean(values)})

if plot_data:
    df_plot = pd.DataFrame(plot_data)
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df_plot, x='Generation', y='Average Value', hue='Experiment', marker='o')
    plt.title(f'Comparison: Average {metric_name}')
    plt.ylabel(metric_name)
    plt.grid(True, alpha=0.3)
    clean_name = metric_name.replace(" ", "_").replace(">>", "").strip()
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"Graph_{clean_name}_{timestamp}.png"
    plt.savefig(filename)
    print(f"\n[SUCCESS] Graph saved as '{filename}'")
else:
    print("No data found.")