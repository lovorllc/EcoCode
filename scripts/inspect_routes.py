import sys, pathlib, inspect
ROOT=pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import main

for r in main.app.routes:
    if getattr(r, 'path', None) == '/auth/register':
        print('Route found:', r)
        print('endpoint:', r.endpoint)
        import inspect as _i
        print('\nEndpoint source:\n')
        print('\n'.join(_i.getsource(r.endpoint).splitlines()[:200]))
        print('\nsignature:', inspect.signature(r.endpoint))
        print('dependant params:', getattr(r, 'dependant', None))
        break
else:
    print('route /auth/register not found')
