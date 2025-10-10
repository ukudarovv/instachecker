#!/usr/bin/env python3
"""Main entry point for the Telegram bot."""

import sys
import os

# Add project directory to Python path
project_dir = os.path.join(os.path.dirname(__file__), 'project')
sys.path.insert(0, project_dir)

# Now import and run the bot
from bot import main

if __name__ == "__main__":
    main()
