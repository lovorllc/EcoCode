import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators import validate_phone

for num in ['000', '0996662838', '+385996662838']:
    try:
        validate_phone(num, 'HR')
        print(num, 'OK')
    except Exception as e:
        print(num, 'ERR', e)
