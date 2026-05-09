# HurryUP_ToDo ::: MAYA TODO list Plugin

A lightweight Maya task management tool for artists, supporting WIP/TODO workflow, workspace-based JSON storage, focus priority system, and production-friendly task tracking.


## 📋 Requirements
- **Maya**: 2023 or later (Required for Python 3 support).



## ⚙️ Key Features

-   **Dockable UI**: The tool is designed as a Maya Panel that can be docked seamlessly into your workspace layout.
    
-   **Drag-and-Drop Workflow**: Tasks can be moved between the **WIP** (Work In Progress) and **TODO** sections simply by dragging them.
    
-   **Workspace Management**: Supports creating and switching between different task lists for specific departments (e.g., Modeling, Lighting, FX).


# Getting Started

 1. Copy the files** to your Maya scripts directory:  C:\Users\用户名\Documents\maya\20XX\scripts
 2. **Run the script** in Maya: - Open the **Script Editor**. - Create a new **Python** tab. - Paste the following code and run it:

```python
import HurryUP_ToDoIt.Main as htd
htd.show_todo_it()
```

Before adding any tasks, you **must save your Maya scene**. If the scene is not saved, the plugin will prompt you with a warning:

> "Please save Maya scene first before adding tasks."


### Managing Task Lists

Use the toggle buttons in the top right corner of the UI to manage your workspaces:

-   **[ N ] New List**: Create a new workspace by entering a unique identifier (e.g., MOD, LGT, or UVs). Once created, the identifier will be displayed at the top of the interface.
    
-   **[ R ] Load/Select**: Select an existing workspace from a dropdown menu. The tool will automatically detect lists associated with the current project directory.

**⭐ Set Focus**Marks the task as a high priority. A star icon will appear next to the task to highlight your current focus.

## 🛠️ UI Structure

-   **WIP Section**: Reserved for tasks currently being worked on.
    
-   **TODO Section**: A holding area for pending tasks and future plans.
