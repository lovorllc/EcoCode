Local network access

1) Activate your virtualenv (if used) and run the server:

```powershell
venv\Scripts\Activate.ps1    # PowerShell
# or
venv\Scripts\activate         # cmd
python uvicorn_fixed.py
```

Or run the existing launcher:

```powershell
python run_server.py
```

2) Open Windows Firewall port 8000 (run as Administrator):

```powershell
netsh advfirewall firewall add rule name="EcoCalc 8000" dir=in action=allow protocol=TCP localport=8000
```

3) Find your host IP (on host machine):

```powershell
ipconfig
```

Look for the IPv4 address on the network adapter (e.g. 192.168.1.42). From another device browse:

    http://<host-ip>:8000/

4) If you still cannot connect:
- Ensure the server process is running and listening on 0.0.0.0:8000.
- Check for other firewall/antivirus blocks.
- Confirm both devices are on the same network.
