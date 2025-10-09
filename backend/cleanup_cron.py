#!/usr/bin/env python3
"""
Cron job script for cleaning up old matches.
Run this script periodically (e.g., daily) via cron.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tasks import enqueue_task

def main():
    # Enqueue cleanup task
    enqueue_task("cleanup_old_matches", {"days_old": 30})
    print("Cleanup task enqueued")

if __name__ == "__main__":
    main()
