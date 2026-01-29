import pybullet as p
import pybullet_data
import time
import numpy as np
import random
import math

def make_arena(arena_size=10, wall_height=1, cid=0):
    wall_thickness = 0.5
    floor_collision_shape = p.createCollisionShape(shapeType=p.GEOM_BOX, halfExtents=[arena_size/2, arena_size/2, wall_thickness], physicsClientId=cid)
    floor_visual_shape = p.createVisualShape(shapeType=p.GEOM_BOX, halfExtents=[arena_size/2, arena_size/2, wall_thickness], rgbaColor=[1, 1, 0, 1], physicsClientId=cid)
    floor_body = p.createMultiBody(baseMass=0, baseCollisionShapeIndex=floor_collision_shape, baseVisualShapeIndex=floor_visual_shape, basePosition=[0, 0, -wall_thickness], physicsClientId=cid)

    # --- ADD THIS BLOCK ---
    # Increase Lateral Friction (Grip). Default is ~0.5. 
    # Setting it to 2.0 or 4.0 makes it like rubber on tarmac.
    p.changeDynamics(floor_body, -1, lateralFriction=4.0, physicsClientId=cid)

    wall_collision_shape = p.createCollisionShape(shapeType=p.GEOM_BOX, halfExtents=[arena_size/2, wall_thickness/2, wall_height/2], physicsClientId=cid)
    wall_visual_shape = p.createVisualShape(shapeType=p.GEOM_BOX, halfExtents=[arena_size/2, wall_thickness/2, wall_height/2], rgbaColor=[0.7, 0.7, 0.7, 1], physicsClientId=cid)

    p.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_collision_shape, baseVisualShapeIndex=wall_visual_shape, basePosition=[0, arena_size/2, wall_height/2], physicsClientId=cid)
    p.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_collision_shape, baseVisualShapeIndex=wall_visual_shape, basePosition=[0, -arena_size/2, wall_height/2], physicsClientId=cid)

    wall_collision_shape = p.createCollisionShape(shapeType=p.GEOM_BOX, halfExtents=[wall_thickness/2, arena_size/2, wall_height/2], physicsClientId=cid)
    wall_visual_shape = p.createVisualShape(shapeType=p.GEOM_BOX, halfExtents=[wall_thickness/2, arena_size/2, wall_height/2], rgbaColor=[0.7, 0.7, 0.7, 1], physicsClientId=cid)

    p.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_collision_shape, baseVisualShapeIndex=wall_visual_shape, basePosition=[arena_size/2, 0, wall_height/2], physicsClientId=cid)
    p.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_collision_shape, baseVisualShapeIndex=wall_visual_shape, basePosition=[-arena_size/2, 0, wall_height/2], physicsClientId=cid)

if __name__ == "__main__":
    import creature 
    p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -10)
    make_arena(arena_size=20)
    p.setAdditionalSearchPath('shapes/')
    p.loadURDF("gaussian_pyramid.urdf", (0,0,-1), useFixedBase=1)
    
    cr = creature.Creature(gene_count=3)
    with open('test.urdf', 'w') as f:
        f.write(cr.to_xml())
    p.loadURDF('test.urdf', (0, 0, 10))
    p.setRealTimeSimulation(1)
    while True:
        time.sleep(1/240)