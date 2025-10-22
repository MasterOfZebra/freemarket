#!/usr/bin/env python3
"""
Background worker for processing matching tasks.
Run this script to process tasks from Redis queue.
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(__file__))

from backend.tasks import process_task_queue

def main():
    print("Starting background worker...")
    while True:
        try:
            process_task_queue()
            time.sleep(1)  # Sleep for 1 second between checks
        except KeyboardInterrupt:
            print("Worker stopped")
            break
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(5)  # Sleep longer on error

if __name__ == "__main__":
    main()
