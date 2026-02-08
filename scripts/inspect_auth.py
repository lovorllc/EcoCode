import sys, inspect, pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import importlib
import auth
importlib.reload(auth)
print('auth.register signature:', inspect.signature(auth.register))
print('auth.register annotations:', auth.register.__annotations__)
