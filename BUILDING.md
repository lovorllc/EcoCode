Packaging with PyInstaller (Windows)

Steps to produce a single-file executable (onefile):

1. Install PyInstaller in your env:

   pip install pyinstaller

2. From the project root (where `run_server.py` and `database.db` live), run:

   pyinstaller --onefile \
     --add-data "templates;templates" \
     --add-data "database.db;." \
     --hidden-import "jinja2" \
     --hidden-import "markupsafe" \
     --hidden-import "passlib" \
     --hidden-import "phonenumbers" \
     run_server.py

Notes:
- On Windows use semicolon (`;`) between source and destination in `--add-data`.
- Include any other data files you need (e.g., `users.db.bak`) using additional `--add-data` flags.
- If PyInstaller misses imports at runtime, add them with `--hidden-import`.

Testing the built exe:
- After build, run `dist\run_server.exe` and open http://127.0.0.1:8000 in your browser.

Troubleshooting:
- If you see template-loading errors, ensure `main.py` uses the bundled templates path (`sys._MEIPASS`) — this repo already includes that change.
- For runtime DB writes: onefile executables unpack to a temporary folder at runtime and are read-only; if you want a writable DB, point the app at a writable path (e.g., next to the exe) or copy `database.db` to the user's app data folder on first run.

Spec file (optional): if you prefer a .spec file, generate it with `pyinstaller run_server.py` and then edit the `datas` list to include `('templates','templates')` and `('database.db','.')` before re-running `pyinstaller run_server.spec`.
