# EcoCode Backend

EcoCode je web aplikacija za praćenje ekološkog utjecaja korisnika.

## Automatsko pokretanje

### Windows (jednostavno)
Dvokliknite na `start_server.bat` - sve će se automatski podesiti i pokrenuti!

### PowerShell (detaljnije)
```powershell
.\start_server.ps1
```

### Ručno
```bash
# Aktiviraj virtual environment
.venv\Scripts\activate

# Instaliraj dependencies
pip install -r requirements.txt

# Pokreni server
python uvicorn_fixed.py
```

## Git kolaboracija

### Automatsko testiranje
Prije svakog commit-a automatski se provjerava sintaksa i import-ovi.

### Workflow
1. `git pull origin main` - povuci najnovije promjene
2. Radi na kodu
3. `git add . && git commit -m "Opis promjene"`
4. `git push origin main` - gurni promjene

### Branch-evi za veće promjene
```bash
git checkout -b nova-feature
# radi na feature-u
git push origin nova-feature
```

## API Endpoints

- `GET /` - Početna stranica
- `GET /login` - Login forma
- `POST /auth/login` - Prijava
- `GET /users` - Lista korisnika (admin)
- `GET /api/users/{id}/metrics` - Metrike korisnika

## Development

Server se pokreće na `http://localhost:8000`

Za debug mode koristite:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Mobile / Android notes

- CORS middleware has been enabled for development in `main.py` to allow calls from mobile clients. For production, restrict `allow_origins`.
- New JSON endpoints for the Android frontend:
  - `POST /api/signup` (JSON) -> returns `{token, id, username}`
  - `POST /api/login` (JSON) -> returns `{token, id, username}`
  - `GET /api/me` (Authorization: Bearer <token>) -> returns current user info
- Use `ngrok http 8000` to expose your local server publicly and paste the generated url into the Android app's "Server URL" field.