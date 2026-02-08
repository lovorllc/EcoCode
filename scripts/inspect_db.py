import sys, pathlib, importlib, inspect
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import database
importlib.reload(database)
print('database file:', database.__file__)
print('Database methods:', [m for m in dir(database.Database) if not m.startswith('__')])
print('\nSource head:')
print('\n'.join(inspect.getsource(database.Database).splitlines()[:200]))
