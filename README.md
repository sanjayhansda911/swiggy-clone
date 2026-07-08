# Swiggy Clone - Backend (Phase 1)

Welcome to the backend of your food delivery app! This folder contains a Python Flask project setup with a static database file (`restaurants.json`).

## Folder Structure

```text
Swiggy-clone/
├── backend/
│   ├── data/
│   │   └── restaurants.json   <-- Our static JSON database
│   ├── app.py                 <-- The main Flask application server
│   └── requirements.txt       <-- List of Python packages required for the project
└── README.md                  <-- This guide
```

## How the Database (`restaurants.json`) works

The `restaurants.json` file act as our temporary database. In a real-world app, you would use a real database (like PostgreSQL or MongoDB), but static JSON files are excellent for mock testing, prototyping, and understanding data flows.

Each restaurant has:
- `id`: A unique number identifying the restaurant.
- `name`: The name of the restaurant.
- `rating`: A decimal rating out of 5.
- `menu`: An array/list containing 3 food items. Each food item contains:
  - `name`: Name of the dish.
  - `price`: Price in INR.
  - `description`: A short explanation of the dish.

## Running the Server Locally

Follow these steps to run the backend on your machine:

### 1. Set up a virtual environment (Recommended)
This isolates the dependencies for this project so they don't interfere with your global Python setup.

Open your terminal in the root folder (`Swiggy-clone`) and run:
```bash
python -m venv venv
```

Activate the virtual environment:
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```

### 2. Install dependencies
Install the required packages (like Flask):
```bash
pip install -r backend/requirements.txt
```

### 3. Run the Flask application
Change directory to the backend and run the server:
```bash
python backend/app.py
```
You should see output indicating that the server is running on `http://127.0.0.1:5000`.

## API Endpoints Available

Once the server is running, you can test it by opening these links in your browser:
- **Get all restaurants**: `http://127.0.0.1:5000/api/restaurants`
- **Get a specific restaurant (e.g., ID 1)**: `http://127.0.0.1:5000/api/restaurants/1`
