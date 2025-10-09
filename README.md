# BPB_MVP: Backpack Battles Simulator & Editor

This project is a tool designed to simulate and analyze item builds for the game Backpack Battles. It consists of two main parts: a simulator for manually placing items and a GUI editor for creating and managing item data.

## Features

- **Data-Driven Design:** All item properties, shapes, and star effects are loaded from an external `items.json` file, making the project highly extensible.
- **Drag-and-Drop Simulator:** A Pygame-based interface to visually arrange items in a backpack.
- **Complex Calculation Engine:** Automatically calculates item synergies, star activations, and a final score for the build based on data-driven rules.
- **GUI Item Editor:** A user-friendly CustomTkinter application to create, view, edit, and delete items in the `items.json` database.

## Project Structure

The project is organized into several key files:

- `definitions.py`: A shared file containing common Python Enums (like `Rarity`, `ItemClass`, `Element`, etc.) used by both the simulator and the editor.
- `main.py`: The main Backpack Battles simulator application, built with Pygame.
- `editor.py`: The GUI application for editing item data, built with CustomTkinter.
- `items.json`: The central database for all item definitions.
- `requirements.txt`: Contains all Python dependencies required for the project.

## Deployment Guide

Follow these steps to set up and run the project on your local machine.

### 1\. Initial Setup

First, clone the repository and set up the Python virtual environment.

    # Navigate to your development folder
    cd path/to/your/projects

    # Clone the repository from GitHub
    git clone [https://github.com/BCSZSZ/BPB_MVP.git](https://github.com/BCSZSZ/BPB_MVP.git)

    # Navigate into the project folder
    cd BPB_MVP

    # Create a Python virtual environment
    python -m venv venv

### 2\. Activate Environment & Install Dependencies

You must activate the virtual environment each time you want to work on the project.

**On Windows:**

    # Activate the environment
    venv\Scripts\activate

    # Install all project dependencies
    pip install -r requirements.txt

**On macOS / Linux:**

    # Activate the environment
    source venv/bin/activate

    # Install all project dependencies
    pip install -r requirements.txt

### 3\. Running the Applications

With the environment active and dependencies installed, you can run either the simulator or the editor.

**To Run the Simulator:**

    python main.py

**To Run the Item Editor:**

    python editor.py

This project is open-source and contributions are welcome. Please refer to `CONTRIBUTING.md` for more details.
