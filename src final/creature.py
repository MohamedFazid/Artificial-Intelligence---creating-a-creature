import genome 
from xml.dom.minidom import getDOMImplementation
from enum import Enum
import numpy as np
import math

# --- CONFIGURATION ---
# Set this to 'Basic' for your previous experiments
# Set this to 'Spider' for Experiment 6
EXP_MODE = 'Spider'


class MotorType(Enum):
    PULSE = 1
    SINE = 2

class Motor:
    def __init__(self, control_waveform, control_amp, control_freq):
        self.motor_type = MotorType.SINE
        self.amp = control_amp
        self.freq = control_freq
        self.phase = 0
    
    def get_output(self):
        self.phase = (self.phase + self.freq) % (np.pi * 2)
        # CONTINUOUS WHEEL MODE: Always positive
        return abs(self.amp)
    


class Creature:
    def __init__(self, gene_count):
        self.spec = genome.Genome.get_gene_spec()
        self.dna = genome.Genome.get_random_genome(len(self.spec), gene_count)
        self.flat_links = None
        self.exp_links = None
        self.motors = None
        self.start_position = None
        self.last_position = None

    def get_flat_links(self):
        if self.flat_links == None:
            gdicts = genome.Genome.get_genome_dicts(self.dna, self.spec)
            self.flat_links = genome.Genome.genome_to_links(gdicts)
        return self.flat_links
    
    def get_expanded_links(self):
        self.get_flat_links()
        if self.exp_links is not None:
            return self.exp_links
        
        exp_links = [self.flat_links[0]]
        genome.Genome.expandLinks(self.flat_links[0], 
                                self.flat_links[0].name, 
                                self.flat_links, 
                                exp_links)
        self.exp_links = exp_links
        return self.exp_links

    def to_xml(self):
        if EXP_MODE == 'Spider':
            # Use the new Blueprint Generator
            return genome.Genome.create_spider_xml(self.dna)
        
        else:
            # --- OLD BASIC LOGIC ---
            self.get_expanded_links()
            domimpl = getDOMImplementation()
            adom = domimpl.createDocument(None, "start", None)
            robot_tag = adom.createElement("robot")
            for link in self.exp_links:
                robot_tag.appendChild(link.to_link_element(adom))
            first = True
            for link in self.exp_links:
                if first:
                    first = False
                    continue
                robot_tag.appendChild(link.to_joint_element(adom))
            robot_tag.setAttribute("name", "pepe")
            return '<?xml version="1.0"?>' + robot_tag.toprettyxml()

    # In creature.py

    def update_position(self, pos, orn=None):
        # Update position
        if self.start_position is None:
            self.start_position = pos
        self.last_position = pos
        
        # Save Orientation (The "Head" rotation)
        if orn is not None:
            self.last_orn = orn

        # Update Heights
        if not hasattr(self, 'peak_z'): self.peak_z = pos[2]
        if not hasattr(self, 'verified_climb_z'): self.verified_climb_z = 0.0
        
        if pos[2] > self.peak_z: self.peak_z = pos[2]
    
    # This part of the code is done by me
    def get_heading_error(self):
        """
        THE SENSOR: Returns the angle between the robot's nose and the mountain.
        - Returns 0.0 if looking directly AT the mountain.
        - Returns 3.14 (PI) if looking directly AWAY.
        """
        if self.last_position is None or not hasattr(self, 'last_orn'):
            return 0.0 # Blind at start
        
        # 1. Where is the mountain? (At 0,0)
        # Vector from robot to mountain = (0-x, 0-y)
        dx = 0 - self.last_position[0]
        dy = 0 - self.last_position[1]
        target_angle = math.atan2(dy, dx)
        
        # 2. Where am I looking? (Yaw from Quaternion)
        # PyBullet quaternions are [x, y, z, w]
        x, y, z, w = self.last_orn
        # Standard formula to convert Quaternion to Yaw (Rotation around Z)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        current_yaw = math.atan2(siny_cosp, cosy_cosp)
        
        # 3. Calculate Difference
        diff = target_angle - current_yaw
        
        # Normalize to -PI to +PI
        while diff > math.pi: diff -= 2*math.pi
        while diff < -math.pi: diff += 2*math.pi
        
        return abs(diff)

# This part of the code is done by me
    def get_motors(self):
        if self.motors == None:
            motors = []
            if EXP_MODE == 'Spider':
                genes = self.dna[0]
                if len(genes) < 10:
                    genes = np.concatenate((genes, [0.5]*(10-len(genes))))

                # --- SENSORY CONTROL LOGIC ---
                heading_error = self.get_heading_error()
                
                # Threshold: Am I looking at the mountain?
                # If error is small (< 0.5 radians), I see it!
                can_see_target = heading_error < 0.5
                
                # --- MOTOR GENES ---
                # We define TWO behaviors:
                
                # Behavior A: CHARGE (When seeing mountain)
                run_speed = 6.0 + (genes[3] * 5.0)  # Fast
                
                # Behavior B: SEARCH (When lost)
                # We turn one side backwards to rotate in place
                turn_speed = 2.0 
                
                num_legs = int(4 + (genes[7] * 8.99))
                
                import math
                for i in range(num_legs):
                    # Default: Run Mode
                    amp = run_speed * 1.0
                    
                    # SENSOR OVERRIDE:
                    # If I can't see the mountain, switch to Turn Mode
                    if not can_see_target:
                        amp = turn_speed
                        # Reverse left legs to spin in place
                        angle = i * (2 * math.pi / num_legs) + (math.pi / num_legs)
                        if (math.pi / 2) < angle < (3 * math.pi / 2):
                            amp = -amp
                            
                    # Create Motor
                    m = Motor(1, amp, 4.0) # Freq 4.0
                    
                    # Gait Phase
                    if i % 2 == 0: m.phase = 0
                    else: m.phase = np.pi
                    
                    motors.append(m)
            
            self.motors = motors 
        return self.motors

# In creature.py
# This part of the code is done by me
    def get_distance_travelled(self):
        """
        TUNED FITNESS FUNCTION
        - Boosts 'Walking Reward' so Gen 0 learns to move.
        - Adds 'Survival Bonus' to prevent 0.0 scores.
        """
        if self.start_position is None or self.last_position is None:
            return 0.0
        
        # 1. Get Coordinates
        start_x, start_y = self.start_position[0], self.start_position[1]
        x, y = self.last_position[0], self.last_position[1]
        z = getattr(self, 'peak_z', self.last_position[2])
        
        # 2. Calculate Distances
        start_dist = math.sqrt(start_x**2 + start_y**2)
        current_dist = math.sqrt(x**2 + y**2)
        
        # 3. SCORE CALCULATION
        
        # Part A: Walking Reward (AMPLIFIED)
        # We multiply by 10 so 1 meter of walking = 10 points.
        # This allows the GA to detect even small improvements in movement.
        dist_improvement = (start_dist - current_dist) * 10.0
        
        # Part B: Height Bonus
        # Only counts if they are actually off the floor (> 0.1)
        height_score = 0
        if z > 0.1:
            height_score = z * 20.0  # Climbing is still double value!
        
        # 4. Final Sum with Survival Bonus
        # We add 1.0 just for surviving. This prevents "0.0" scores, 
        # allowing the GA to rank "bad walkers" higher than "dead robots".
        total_score = dist_improvement + height_score + 1.0
        
        # Prevent negative scores if they run backwards
        return max(0.1, total_score)
    
    def update_dna(self, dna):
        self.dna = dna
        self.flat_links = None
        self.exp_links = None
        self.motors = None
        self.start_position = None
        self.last_position = None