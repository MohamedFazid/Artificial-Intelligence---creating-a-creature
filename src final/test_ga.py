import unittest
import population
import simulation 
import genome 
import creature 
import numpy as np
import os

# Some of this part of the code is done by me
def run_ga(pop_size, gene_count, pool_size, iterations, generations):
    # --- 1. SETUP RESULTS FOLDER ---
    if not os.path.exists('results'): os.makedirs('results')
    
    existing = [d for d in os.listdir('results') if d.startswith('test')]
    nums = [int(d.replace('test', '')) for d in existing if d.replace('test', '').isdigit()]
    next_num = max(nums) + 1 if nums else 1
    results_dir = os.path.join('results', f'test{next_num}')
    os.makedirs(results_dir)
    print(f"--- STARTING EXPERIMENT 7: FULL CO-EVOLUTION ---")
    print(f"Saving results to: {results_dir}")

    # --- 2. INITIALIZE POPULATION ---
    pop = population.Population(pop_size=pop_size, gene_count=1)
    sim = simulation.ThreadedSim(pool_size=pool_size) if pool_size > 1 else simulation.Simulation()

    # --- 3. EVOLUTION LOOP ---
    # We define 'gen' here in the loop header
    for gen in range(generations): 
        # A. Evaluate
        sim.eval_population(pop, iterations)
        
        # B. Measure Fitness
        fits = [c.get_distance_travelled() for c in pop.creatures]
        max_fit = np.max(fits)
        mean_fit = np.mean(fits)
        
        # C. Measure Height vs Verified Climb
        # Check if attributes exist (safety check for first run)
        heights = []
        climbs = []
        for c in pop.creatures:
            # Use getattr to avoid crashes if variables aren't initialized
            h = getattr(c, 'peak_z', 0.0) 
            cl = getattr(c, 'verified_climb_z', 0.0)
            heights.append(h)
            climbs.append(cl)
            
        max_height = np.max(heights)
        max_climb = np.max(climbs)
        
        # D. Print Stats (Now 'gen' is safely defined)
        print(f"Gen {gen}: Fit: {max_fit:.2f} | Height: {max_height:.2f}m | Climbed: {max_climb:.2f}m")
        
        # E. Save Elite
        best_idx = np.argmax(fits)
        elite = pop.creatures[best_idx]
        genome.Genome.to_csv(elite.dna, os.path.join(results_dir, f"elite_{gen}.csv"))
        
        # F. Reproduction
        fit_map = population.Population.get_fitness_map(fits)
        new_creatures = []
        
        for i in range(len(pop.creatures)):
            p1 = pop.creatures[population.Population.select_parent(fit_map)]
            p2 = pop.creatures[population.Population.select_parent(fit_map)]
            dna = genome.Genome.crossover(p1.dna, p2.dna)
            dna = genome.Genome.point_mutate(dna, rate=0.1, amount=0.25)
            cr = creature.Creature(gene_count=1)
            cr.update_dna(dna)
            new_creatures.append(cr)
        
        new_creatures[0].update_dna(elite.dna) # Elitism
        pop.creatures = new_creatures

    print(f"Experiment Complete. Results saved in {results_dir}")
    return max_fit, results_dir # Return values for the test assertion


# This part of the code is done by me

class TestGA(unittest.TestCase):
    def testBasicGA(self):
        print("--- STARTING EXPERIMENT 6: THE SPIDER (ADVANCED) ---")
        print("Make sure EXP_MODE = 'Spider' is set in creature.py")
        
        # Standard Settings
        fits, results_dir = run_ga(
            pop_size=50,       # Standard population
            gene_count=1,      # Standard complexity (3 limbs)
            pool_size=1,       # Single thread
            iterations=1000,   # 1000 steps = approx 4 seconds of climbing time
            generations=50     # Run for 50 generations
        )
        
        print(f"Spider Experiment Complete. Results saved in {results_dir}")

if __name__ == "__main__":
    unittest.main()