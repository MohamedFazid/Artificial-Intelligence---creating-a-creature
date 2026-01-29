import os 
import genome
import sys
import creature
import pybullet as p
import time 
import random
import numpy as np
import cw_envt_ga as envt # Import your environment library
import pybullet_data

def main(csv_file):
    assert os.path.exists(csv_file), "Tried to load " + csv_file + " but it does not exist"

    # 1. Connect to GUI
    cid = p.connect(p.GUI)
    p.setPhysicsEngineParameter(enableFileCaching=0)
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
    p.setGravity(0, 0, -10)
    
    # Add search paths for basic shapes and your custom shapes
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setAdditionalSearchPath('shapes/')

    # 2. Build the Arena & Mountain
    # Pass the client ID (cid)
    envt.make_arena(arena_size=20, cid=cid) 
    
    mountain_position = (0, 0, -1)
    mountain_orientation = p.getQuaternionFromEuler((0, 0, 0))
    # Load the Rocky Mountain with Cubes
    p.loadURDF("shapes/gaussian_pyramid.urdf", mountain_position, mountain_orientation, useFixedBase=1)

    # 3. Load the Genome
    cr = creature.Creature(gene_count=1)
    dna = genome.Genome.from_csv(csv_file)
    cr.update_dna(dna)

    # 4. Convert to XML and Load Robot
    # We use a temp file for viewing
    urdf_filename = 'view_temp.urdf'
    with open(urdf_filename, 'w') as f:
        f.write(cr.to_xml())
    
    # Spawn settings: Adjusted to drop near the mountain base or peak
    # (4, 4, 1) is a good starting spot to climb UP.
    rob1 = p.loadURDF(urdf_filename)
    p.resetBasePositionAndOrientation(rob1, [4, 4, 1.0], [0, 0, 0, 1])

    start_pos, orn = p.getBasePositionAndOrientation(rob1)

   # 5. Run Simulation Loop
    elapsed_time = 0
    wait_time = 1.0/240 # seconds
    total_time = 60 # Run for 60 seconds (adjust if needed)
    step = 0
    
    print(f"Viewing {csv_file}... Press Ctrl+C to stop.")
    
    # CRITICAL FIX: Only run while the GUI window is open
    while p.isConnected():
        p.stepSimulation()
        step += 1
        
        # --- UPDATE CREATURE STATE ---
        # We get position/orientation EVERY STEP so the sensors work (Exp 8)
        pos, orn = p.getBasePositionAndOrientation(rob1)
        
        # Try passing orientation (Exp 8 code), fallback to just position (Exp 7 code)
        try:
            cr.update_position(pos, orn)
        except TypeError:
            cr.update_position(pos)

        # --- UPDATE MOTORS (10Hz) ---
        if step % 24 == 0:
            motors = cr.get_motors()
            for jid in range(p.getNumJoints(rob1)):
                mode = p.VELOCITY_CONTROL
                vel = motors[jid].get_output()
                p.setJointMotorControl2(rob1, 
                            jid,  
                            controlMode=mode, 
                            targetVelocity=vel,
                            force=180) # INCREASED TO 180 (Matches Simulation)
            
            # Print current height to terminal
            print(f"Height: {round(pos[2], 2)}", end='\r')

        time.sleep(wait_time)
        elapsed_time += wait_time
        if elapsed_time > total_time:
            break

if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Usage: python realtime_from_csv.py <path_to_csv_file>")