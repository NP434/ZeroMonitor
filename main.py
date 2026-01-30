"""
Filename: main.py
Author: Daniel Stone

File Description: Entry point for the ZeroMonitor UI. This launcher imports
App class from ui.display and starts main event loop.

Should later be integrated with backend to start all processes.
"""

from ui.display import App

if __name__ == "__main__":
    App().run()