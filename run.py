"""
Entry point for Phishy.
Run from the project root: python run.py
"""
from backend.app import app

if __name__ == "__main__":
    app.run(debug=True)
