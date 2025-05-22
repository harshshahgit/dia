"""
Launcher script for Dia application.
This redirects to the actual app in the debugger directory.
"""
import os
import sys

# Add the debugger directory to the path
debugger_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debugger')
sys.path.insert(0, debugger_path)

# Change to the debugger directory for proper file resolution
os.chdir(debugger_path)

# Import the app from debugger directory
from app import app

if __name__ == '__main__':
    app.run(debug=True, port=5001) 