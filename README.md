# BPB_MVP: Backpack Battles Simulator & Editor

This project is a tool designed to simulate and analyze item builds for the game Backpack Battles. It consists of two main parts: a simulator for manually placing items and a GUI editor for creating and managing item data.
refer to a Bilibili intro video by me, in Chinese.
【背包乱斗摆盘求解小玩具-功能介绍与画面展示】 https://www.bilibili.com/video/BV14v4czhEwQ/?share_source=copy_web&vd_source=6ca11da6fac510effe333bdc3286e565

## Features

- **Data-Driven Design**: All item properties, shapes, and effects are loaded from an external `items.json` file, making the project highly extensible without code changes.
- **Drag-and-Drop Simulator**: A Pygame-based interface to visually arrange items in a backpack, with support for item rotation.
- **Advanced Calculation Engine**: A sophisticated engine that processes item builds according to a multi-stage rule system:

  - **Star Activation Logic**: Correctly handles activation of multiple star types (`STAR_A`, `STAR_B`, `STAR_C`), ensuring effects trigger only once per unique target item.
  - **Rich Conditional Effects**: Supports a wide range of conditions for effects, such as requiring specific item types, elements, names, or even empty adjacent slots.
  - **Diverse Effect Payloads**: Implements various outcomes including additive/multiplicative score changes and temporary element additions to other items.
  - **Dynamic Values**: Can calculate effect values dynamically based on other game state, such as the number of other activated stars.

- **GUI Item Editor**: A user-friendly CustomTkinter application to create, view, edit, and delete items in the `items.json` database.

## Project Structure

The project is organized into several key files:

- `definitions.py`: A shared file containing common Python Enums (like `Rarity`, `ItemClass`, `Element`, etc.) used by both the simulator and the editor.
- `main.py`: The main Backpack Battles simulator application, built with Pygame, that handles visuals and user interaction.
- `engine.py`: Contains the core logic classes, including the `Item` definition and the `CalculationEngine` that runs the simulation rules.
- `editor.py`: The GUI application for editing item data, built with CustomTkinter.
- `items.json`: The central database for all item definitions.
- `requirements.txt`: Contains all Python dependencies required for the project.

## Deployment Guide

Follow these steps to set up and run the project on your local machine.

### 1\. Initial Setup

First, clone the repository and set up the Python virtual environment.

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

You must activate the virtual environment each time you want to work on the project.

**On Windows:**

Bash

    # Activate the environment
    venv\Scripts\activate

    # Install all project dependencies
    pip install -r requirements.txt

**On macOS / Linux:**

Bash

    # Activate the environment
    source venv/bin/activate

    # Install all project dependencies
    pip install -r requirements.txt

### 3\. Running the Applications

With the environment active and dependencies installed, you can run either the simulator or the editor.

**To Run the Simulator:**

Bash

    python main.py

**To Run the Item Editor:**

Bash

    python editor.py

This project is open-source and contributions are welcome. Please refer to `CONTRIBUTING.md` for more details.
