# BPB\_MVP: Backpack Battles Simulator & Solver

This project is an advanced tool designed to simulate, analyze, and solve optimal item builds for the game Backpack Battles. It consists of a manual simulator, a GUI item editor, and a suite of powerful automated layout solvers.

For a brief video introduction (in Chinese), please see: 【背包乱斗摆盘求解小玩具-功能介绍与画面展示】 [https://www.bilibili.com/video/BV14v4czhEwQ/](https://www.bilibili.com/video/BV14v4czhEwQ/)

* * *

## Features

-   **Data-Driven Design**: All item properties, shapes, and effects are loaded from an external `items.json` file, making the project highly extensible.
    
-   **Drag-and-Drop Simulator**: A Pygame-based interface to visually arrange items in a backpack, with support for item rotation and on-screen debug info.
    
-   **GUI Item Editor**: A user-friendly CustomTkinter application to create, view, edit, and delete items in the `items.json` database.
    
-   **Advanced Calculation Engine**: A sophisticated engine that processes builds according to a multi-stage rule system, including:
    
    -   **Star Activation Logic**: Correctly handles activation of multiple star types (`STAR_A`, `STAR_B`, `STAR_C`).
        
    -   **Rich Conditional Effects**: Supports conditions based on item types, elements, names, and more.
        
    -   **Diverse Effect Payloads**: Implements score changes, temporary element additions, and a **Neutral Pool** for global score modifications.
        
    -   **Dynamic Values**: Calculates effect values based on game state, like the number of activated stars.
        
-   **Automated Layout Solvers**: A modular framework for finding the optimal backpack layout for a given set of items. Includes multiple algorithms:
    
    -   **Genetic Algorithms**: Two distinct GA implementations—a high-quality **"Star-Seeker"** version that intelligently optimizes for star synergy, and a high-speed **"Parent Swap"** version for rapid results.
        
    -   **Reinforcement Learning**: A state-of-the-art solver trained using PyTorch and Stable Baselines3. It uses **Action Masking** to guarantee valid placements and learns optimal strategies through a sophisticated reward system.
        
    -   **Random Solver**: A simple baseline for comparison.
        

* * *

## Project Structure

The project is organized into several key files and directories:

-   `main.py`: The main simulator application (Pygame) that handles visuals, user interaction, and solver integration.
    
-   `engine.py`: Contains the core logic, including the `Item` class and the `CalculationEngine`.
    
-   `editor.py`: The GUI application for editing `items.json` (CustomTkinter).
    
-   `solvers/`: A directory containing all automated layout solvers, built on a common `base_solver.py`.
    
-   `BackpackEnv.py`: A custom `gymnasium` environment that teaches the reinforcement learning agent how to play the game.
    
-   `train.py`: The script used to train the reinforcement learning model with your GPU.
    
-   `items.json`: The central database for all item definitions.
    
-   `definitions.py`: Shared Python Enums (like `Rarity`, `ItemClass`) used across the project.
    
-   `requirements.txt`: Contains all Python dependencies.
    

* * *

## Deployment Guide

Follow these steps to set up and run the project on your local machine.

### 1\. Initial Setup

First, clone the repository and set up a Python virtual environment.

Bash

    # Navigate to your development folder
    cd path/to/your/projects
    
    # Clone the repository from GitHub
    git clone https://github.com/BCSZSZ/BPB_MVP.git
    
    # Navigate into the project folder
    cd BPB_MVP
    
    # Create a Python virtual environment
    python -m venv venv

### 2\. Activate Environment & Install Dependencies

You must activate the virtual environment before installing dependencies.

**On Windows:**

Bash

    # Activate the environment
    venv\Scripts\activate

**On macOS / Linux:**

Bash

    # Activate the environment
    source venv/bin/activate

### 3\. Install PyTorch (GPU Support)

The reinforcement learning components require PyTorch with CUDA support. This must be installed separately **before** installing the other dependencies. For a machine with an NVIDIA GPU (like an RTX 4080), run the following command:

Bash

    pip3 install torch --index-url https://download.pytorch.org/whl/cu121

### 4\. Install All Other Dependencies

Now, install the remaining packages from `requirements.txt`.

Bash

    pip install -r requirements.txt

### 5\. Running the Applications

With the environment active and all dependencies installed, you can train the RL model or run the main applications.

**To Train the RL Model (Required for the RL Solver):** The `RLSolver` needs a trained model file to function. Run the training script to generate it. This process is computationally intensive and will leverage your GPU.

Bash

    python train.py

You can monitor the training progress by opening a **second terminal**, activating the environment, and running:

Bash

    tensorboard --logdir ./ppo_maskable_backpack_tensorboard/

**To Run the Simulator:**

Bash

    python main.py

**To Run the Item Editor:**

Bash

    python editor.py



