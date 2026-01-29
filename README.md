# Training an AI Creature to Climb a Mountain using a Genetic Algorithm  
**Evolutionary Robotics • PyBullet • Genetic Algorithms • Sensory Control**

This project explores how evolutionary algorithms can be used to train an AI-controlled creature to climb a mountain in a physically realistic simulation. It was developed as part of the CM3020 Artificial Intelligence coursework and focuses on how **fitness design, morphology, control encoding, and sensory feedback** affect learning in embodied AI systems.

The system uses a **Genetic Algorithm (GA)** to evolve both the body structure and motor control of a creature inside a **PyBullet** physics environment. Through multiple experiments, the project demonstrates that:

- Fitness shaping alone is insufficient if the morphology is mechanically unsuitable.
- Stable embodiment is critical for meaningful learning.
- Co-evolving body and control produces the strongest climbing behavior.
- Adding minimal sensory input greatly improves learning efficiency and reliability.

---

## 🧠 Core Concepts

- Genetic Algorithms for continuous optimization  
- Embodied intelligence  
- Physics-based simulation  
- Evolution of morphology and control  
- Closed-loop sensory feedback  

---

## 🏔 Environment

- PyBullet physics simulation  
- Sandbox arena with:
  - Fixed spawn location
  - Gaussian pyramid-style mountain at center
  - High-friction ground and creature contacts
- Creatures are evaluated for a fixed number of simulation steps each generation.

---

## 🧬 Genetic Algorithm

- Population-based evolution
- Tournament selection
- Mutation-only reproduction (no crossover)
- Real-valued genome
- Parallel simulation for faster evaluation

Genome parameters include:

| Category        | Genes Control                                   |
|----------------|------------------------------------------------|
| Motor Control  | Speed, power/torque, frequency, phase          |
| Morphology     | Leg length, leg radius, body radius, leg count |

---

## 🧪 Experiments Implemented

### Experiment 1 – Height Only Fitness
- Fitness = max vertical height
- Failed due to exploitative tall morphologies.

### Experiment 2 – Stability Weighted Fitness
- Encouraged stability but discouraged movement.
- Creatures became static.

### Experiment 3 – Guided Explorer Fitness
- Added distance and anti-cheating constraints.
- Over-constrained search, no meaningful climbing.

### Experiments 4 & 5 – Population Scaling
- Larger populations (50 & 100).
- No improvement, confirmed morphology was limiting factor.

---

### Experiment 6 – Fixed Morphology, Evolvable Control
- Introduced stable **octopod body**.
- Only motor parameters evolved.
- Immediate non-zero fitness.
- Demonstrated importance of mechanical stability.

---

### Experiment 7 – Full Co-Evolution (Body + Brain)
- Morphology and control evolved together.
- Best performance:
  - Fitness > 380
  - Verified climb ≈ 2.75m
- Emergent spring-like jumping behavior.

---

### Experiment 8 – Sensory Control (Exceptional Criterion)
- Added heading sensor toward mountain center.
- Closed-loop motor control:
  - Forward motion when aligned
  - Rotation when misaligned
- Faster convergence and more reliable navigation.

---

## 🛠 Technologies Used

- Python  
- PyBullet  
- NumPy  
- Genetic Algorithms  
- Physics simulation  
- Evolutionary robotics techniques  

---


## ▶️ How to Run

### 1. Install Python (3.8+ recommended)

python --version

### 2. Install Dependencies

pip install pybullet numpy matplotlib

### 3. Extract the Project

cd src

4. Run the Simulation

python cw_envt_ga.py
