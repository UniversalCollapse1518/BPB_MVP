# **Backpack Battles \- MVP Simulator**

This project is a minimal viable product (MVP) for a Backpack Battles simulator. The primary goal is to create a tool that allows users to place items within a backpack grid to visually simulate builds. The long-term vision is to develop a solver that can analyze item layouts and determine their combat effectiveness.

This repository contains the initial version with a basic GUI where items can be dragged and dropped into a backpack.

## **Features**

* A visual backpack grid.  
* Two sample items ("Sword" and "Shield") that can be selected.  
* Drag-and-drop functionality for placing items.  
* Items snap to the grid inside the backpack.

## **Getting Started**

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### **Prerequisites**

* [Python 3.8](https://www.python.org/downloads/) or newer  
* [Git](https://git-scm.com/downloads/)

### **Installation Guide**

1. Clone the Repository  
   Open your terminal or command prompt and clone the repository to your local machine:  
   git clone \[https://github.com/BCSZSZ/BPB\_MVP.git\](https://github.com/BCSZSZ/BPB\_MVP.git)

2. **Navigate to the Project Directory**  
   cd BPB\_MVP

3. Create a Python Virtual Environment  
   It's highly recommended to use a virtual environment to keep project dependencies isolated.  
   ```python \-m venv venv```

4. Activate the Virtual Environment  
   You must activate the environment every time you work on the project.  
   * **On Windows (Command Prompt):**  
     ```venv\\Scripts\\activate```

   * On Windows (PowerShell):  
     You may first need to adjust your script execution policy for the current session.  
     ```Set-ExecutionPolicy \-ExecutionPolicy RemoteSigned \-Scope Process```

     Then, you can activate the environment:  
     ```venv\\Scripts\\activate```

   * **On macOS and Linux:**  
     ```source venv/bin/activate```

Your terminal prompt should now be prefixed with (venv).

5. Install Dependencies  
   With the virtual environment active, install the necessary Python packages.  
   ```pip install \-r requirements.txt```

## **Usage**

Once the installation is complete, you can run the simulator with the following command:

```python main.py```

A window should appear displaying the backpack grid and the draggable items.

## **Contributing**

Contributions are welcome\! If you have ideas for improvements or want to fix a bug, please feel free to fork the repository and submit a pull request. For more details, see the CONTRIBUTING.md file.

## **License**

This project is licensed under the MIT License \- see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.
