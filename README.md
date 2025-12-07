# check-secure-boot

This project consists of two a Python and a PowerShell script. The Python runs an API endpoint that receives data from the PowerShell script. The PowerShell script reports whether the 2023 Microsoft Secure Boot certificates are in the active DB and/or default db.




## Run Locally with uv

Make sure you have [uv](https://github.com/astral-sh/uv) installed and clone the project. Edit `Check-Secure-Boot-Certs.ps1` and specify the target host `$uri = "http://localhost:8000/api"`

Clone the project.

```bash
  git clone https://github.com/redeuxx/check-secure-boot.git
```

Go to the project directory

```bash
  cd check-secure-boot
```

Run the API endpoint.

```bash
  uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Run `Check-Secure-Boot-Certs.ps1` on a Windows computer in an elevated mode.