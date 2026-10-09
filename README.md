# Microsoft Graph — Failed Sign-In Audit

A Python script that authenticates to Microsoft Graph API via device code flow, pulls sign-in audit logs from the last 30 days, and counts unsuccessful sign-in events per day.

## Prerequisitesites

1. **Azure AD App Registration** (one-time setup):
   - Go to [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → **New registration**
   - Name: `graph-signin-audit`
   - Supported account types: **Accounts in this organizational directory only**
   - Redirect URI: leave blank (device code flow doesn't need one)
   - Click **Register** and note the **Application (client) ID**
   - Go to **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions** → search `AuditLog.Read.All` → **Add**
   - Click **Grant admin consent** (requires admin rights)

2. **Python 3.8+**

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Copy `config_template.py` to `config.py` and fill in your credentials:

```bash
cp config_template.py config.py
```

Edit `config.py` and set:

```python
CLIENT_ID = "your-actual-client-id-here"
TENANT_ID = "common"  # or your specific tenant ID
```

Alternatively, set environment variables instead of using `config.py`:

```bash
export MSGRAPH_CLIENT_ID="your-client-id"
export MSGRAPH_TENANT_ID="common"
```

## Usage

```bash
python signin_audit.py
```

The script will:

1. Print a verification URL and code
2. Open the URL in your browser, enter the code, and sign in with your Microsoft account
3. Fetch all sign-in logs from the last 30 days (handling pagination automatically)
4. Display a table of failed sign-ins per day
5. Save a JSON report to `failed_signins_report.json`

## Output Example

```
Microsoft Graph — Failed Sign-In Audit
========================================
✓ Authenticated successfully

Date range: 2026-09-09 to 2026-10-09

Fetching sign-in logs...
  Fetched 1247 total sign-in records across 3 pages.

==================================================
  FAILED SIGN-INS PER DAY (Last 30 Days)
==================================================
  Date           Failed Count
--------------------------------------------------
  2026-09-09              12  ████████████
  2026-09-10               3  ███
  2026-09-11               0
  ...
--------------------------------------------------
  TOTAL                    156
==================================================

✓ Report saved to failed_signins_report.json
```

## Notes

- Microsoft Graph retains sign-in logs for **30 days** (Azure AD Free) or **30+ days** with P1/P2 licenses
- Sign-ins with `status.errorCode != 0` are counted as unsuccessful
- The script handles pagination automatically via `@odata.nextLink`
- Tokens are cached by MSAL for silent re-authentication on subsequent runs

## License

MIT
