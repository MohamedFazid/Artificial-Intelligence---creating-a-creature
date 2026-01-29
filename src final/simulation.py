import pybullet as p
import cw_envt_ga as envt
import pybullet_data
from multiprocessing import Pool
import os

class Simulation: 
    def __init__(self, sim_id=0):
        self.physicsClientId = p.connect(p.DIRECT)
        self.sim_id = sim_id
        p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=self.sim_id)
        p.setAdditionalSearchPath('shapes/', physicsClientId=self.sim_id)

    def run_creature(self, cr, iterations=2400):
        pid = self.physicsClientId
        p.resetSimulation(physicsClientId=pid)
        p.setPhysicsEngineParameter(enableFileCaching=0, physicsClientId=pid)
        p.setGravity(0, 0, -10, physicsClientId=pid)

        envt.make_arena(arena_size=20, cid=pid)
        
        # Load Mountain
        mountain_pos = (0, 0, -1)
        mountain_orn = p.getQuaternionFromEuler((0, 0, 0))
        
        # Make sure this filename is correct ("shapes/mountain_with_cubes.urdf")
    def run_creature(self, cr, iterations=2400):
        pid = self.physicsClientId
        p.resetSimulation(physicsClientId=pid)
        p.setPhysicsEngineParameter(enableFileCaching=0, physicsClientId=pid)
        p.setGravity(0, 0, -10, physicsClientId=pid)

        envt.make_arena(arena_size=20, cid=pid)
        
        # Load Mountain
        mountain_pos = (0, 0, -1)
        mountain_orn = p.getQuaternionFromEuler((0, 0, 0))
        
        # Make sure this filename is correct ("shapes/mountain_with_cubes.urdf")
        self.mountain_id = p.loadURDF("shapes/gaussian_pyramid.urdf", mountain_pos, mountain_orn, useFixedBase=1, physicsClientId=pid)

        # --- XML CREATION & SAVING ---
        # CHECK INDENTATION HERE: This line must start at the same column as the line above
        xml_file = 'temp' + str(self.sim_id) + '.urdf'
        xml_str = cr.to_xml()
        
        # WRITE AND FLUSH
        with open(xml_file, 'w') as f:
            f.write(xml_str)
            f.flush()
            os.fsync(f.fileno()) 

        # --- LOAD WITH ERROR CHECKING ---
        try:
            cid = p.loadURDF(xml_file, physicsClientId=pid)
        except Exception as e:
            print(f"\nFATAL ERROR LOADING URDF: {xml_file}")
            print("--- XML CONTENT START ---")
            print(xml_str)
            print("--- XML CONTENT END ---")
            raise e 

        # Setup Physics
        p.resetBasePositionAndOrientation(cid, [4, 4, 0.3], [0, 0, 0, 1], physicsClientId=pid)
        for link_index in range(p.getNumJoints(cid, physicsClientId=pid)):
            p.changeDynamics(cid, link_index, lateralFriction=5.0, spinningFriction=0.2, rollingFriction=0.2, physicsClientId=pid)
        p.changeDynamics(cid, -1, lateralFriction=4.0, physicsClientId=pid)

        # Initialize Stats
        cr.start_position = [4, 4, 0.2] 
        cr.last_position = [4, 4, 0.2]
        cr.peak_z = 0.0
        cr.verified_climb_z = 0.0
        
        # Simulation Loop
        for step in range(iterations):
            p.stepSimulation(physicsClientId=pid)
            if step % 24 == 0:
                self.update_motors(cid=cid, cr=cr)

            pos, orn = p.getBasePositionAndOrientation(cid, physicsClientId=pid)
            
            # PASS BOTH TO CREATURE
            cr.update_position(pos, orn)
            
            # Contact Check
            contacts = p.getContactPoints(bodyA=cid, bodyB=self.mountain_id, physicsClientId=pid)
            if len(contacts) > 0:
                if pos[2] > cr.verified_climb_z:
                    cr.verified_climb_z = pos[2]
        # --- XML CREATION & SAVING ---
        # CHECK INDENTATION HERE: This line must start at the same column as the line above
        xml_file = 'temp' + str(self.sim_id) + '.urdf'
        xml_str = cr.to_xml()
        
        # WRITE AND FLUSH
        with open(xml_file, 'w') as f:
            f.write(xml_str)
            f.flush()
            os.fsync(f.fileno()) 

        # --- LOAD WITH ERROR CHECKING ---
        try:
            cid = p.loadURDF(xml_file, physicsClientId=pid)
        except Exception as e:
            print(f"\nFATAL ERROR LOADING URDF: {xml_file}")
            print("--- XML CONTENT START ---")
            print(xml_str)
            print("--- XML CONTENT END ---")
            raise e 

        # Setup Physics
        p.resetBasePositionAndOrientation(cid, [4, 4, 0.3], [0, 0, 0, 1], physicsClientId=pid)
        for link_index in range(p.getNumJoints(cid, physicsClientId=pid)):
            p.changeDynamics(cid, link_index, lateralFriction=5.0, spinningFriction=0.2, rollingFriction=0.2, physicsClientId=pid)
        p.changeDynamics(cid, -1, lateralFriction=4.0, physicsClientId=pid)

        # Initialize Stats
        cr.start_position = [4, 4, 0.2] 
        cr.last_position = [4, 4, 0.2]
        cr.peak_z = 0.0
        cr.verified_climb_z = 0.0
        
        # Simulation Loop
        for step in range(iterations):
            p.stepSimulation(physicsClientId=pid)
            if step % 24 == 0:
                self.update_motors(cid=cid, cr=cr)

            pos, orn = p.getBasePositionAndOrientation(cid, physicsClientId=pid)
            
            # PASS BOTH TO CREATURE
            cr.update_position(pos, orn)
            
            # Contact Check
            contacts = p.getContactPoints(bodyA=cid, bodyB=self.mountain_id, physicsClientId=pid)
            if len(contacts) > 0:
                if pos[2] > cr.verified_climb_z:
                    cr.verified_climb_z = pos[2]
    
    def update_motors(self, cid, cr):
        for jid in range(p.getNumJoints(cid, physicsClientId=self.physicsClientId)):
            m = cr.get_motors()[jid]
            p.setJointMotorControl2(cid, jid, 
                    controlMode=p.VELOCITY_CONTROL, 
                    targetVelocity=m.get_output(), 
                    force = 80,  # <--- CHANGE from 85 to 150 (More Torque)
                    physicsClientId=self.physicsClientId)
        

    def eval_population(self, pop, iterations):
        for cr in pop.creatures:
            self.run_creature(cr, iterations) 


class ThreadedSim():
    def __init__(self, pool_size):
        self.sims = [Simulation(i) for i in range(pool_size)]

    # This part of the code is done by me
    @staticmethod
    def static_run_creature(sim, cr, iterations):
        sim.run_creature(cr, iterations)
        return cr
    
    def eval_population(self, pop, iterations):
        pool_args = [] 
        start_ind = 0
        pool_size = len(self.sims)
        while start_ind < len(pop.creatures):
            this_pool_args = []
            for i in range(start_ind, start_ind + pool_size):
                if i == len(pop.creatures):
                    break
                sim_ind = i % len(self.sims)
                this_pool_args.append([
                            self.sims[sim_ind], 
                            pop.creatures[i], 
                            iterations]   
                )
            pool_args.append(this_pool_args)
            start_ind = start_ind + pool_size

        new_creatures = []
        for pool_argset in pool_args:
            with Pool(pool_size) as p:
                creatures = p.starmap(ThreadedSim.static_run_creature, pool_argset)
                new_creatures.extend(creatures)
        pop.creatures = new_creatures


