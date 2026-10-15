"""Run one queued mission in an independent process."""
import sys
from src.agent import run_mission

if __name__ == '__main__':
    run_mission(sys.argv[1])
