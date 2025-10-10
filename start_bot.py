#!/usr/bin/env python
"""Bot starter with auto-restart functionality."""

import sys
import os
import time
import subprocess
from datetime import datetime

def print_log(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def main():
    """Main loop with auto-restart."""
    restart_count = 0
    max_quick_restarts = 5
    quick_restart_window = 60  # seconds
    last_restart_time = None
    
    print_log("=" * 60)
    print_log("Bot Auto-Restart Manager Started")
    print_log("=" * 60)
    print_log("Press Ctrl+C to stop")
    print_log("")
    
    while True:
        try:
            current_time = time.time()
            
            # Check for too many quick restarts
            if last_restart_time and (current_time - last_restart_time) < quick_restart_window:
                restart_count += 1
                if restart_count >= max_quick_restarts:
                    print_log(f"⚠️ Too many restarts ({restart_count}) in {quick_restart_window}s")
                    print_log("⚠️ Waiting 60 seconds before next attempt...")
                    time.sleep(60)
                    restart_count = 0
            else:
                restart_count = 0
            
            last_restart_time = current_time
            
            # Start the bot
            print_log("🚀 Starting bot...")
            
            # Use run_bot.py if it exists, otherwise use project/bot.py
            if os.path.exists("run_bot.py"):
                result = subprocess.run(
                    [sys.executable, "run_bot.py"],
                    cwd=os.getcwd()
                )
            else:
                result = subprocess.run(
                    [sys.executable, "-m", "project.bot"],
                    cwd=os.getcwd()
                )
            
            exit_code = result.returncode
            
            # Check exit code
            if exit_code == 0:
                print_log("✅ Bot stopped gracefully (exit code 0)")
                print_log("🔄 Restarting in 3 seconds...")
                time.sleep(3)
            elif exit_code == 2:
                # Special exit code for "stop without restart"
                print_log("🛑 Bot requested permanent stop (exit code 2)")
                print_log("Exiting auto-restart manager...")
                break
            else:
                print_log(f"⚠️ Bot crashed (exit code {exit_code})")
                print_log("🔄 Restarting in 5 seconds...")
                time.sleep(5)
        
        except KeyboardInterrupt:
            print_log("")
            print_log("⛔ Keyboard interrupt received")
            print_log("Stopping auto-restart manager...")
            break
        
        except Exception as e:
            print_log(f"❌ Error in restart manager: {e}")
            print_log("🔄 Retrying in 10 seconds...")
            time.sleep(10)
    
    print_log("")
    print_log("=" * 60)
    print_log("Bot Auto-Restart Manager Stopped")
    print_log("=" * 60)

if __name__ == "__main__":
    main()

