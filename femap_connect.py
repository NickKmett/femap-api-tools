import pythoncom
import Pyfemap
from Pyfemap import constants as feConstants
import sys
sys.path.append(r"C:\Users\nicho\Documents\Projects\GitHub\femap-api-tools")
import win32com.client as win32

def connect():
    try:
        existObj = pythoncom.connect(Pyfemap.model.CLSID)
        App = Pyfemap.model(existObj)
        App.feAppMessage(0, "Python API Started")
        return App, feConstants
    except pythoncom.com_error:
        sys.exit("Femap not open - launch Femap and try again")
    except Exception as e:
        sys.exit(f"Unexpected error: {e}")