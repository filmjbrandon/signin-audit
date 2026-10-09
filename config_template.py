# Copy this file to config.py and fill in your Azure AD app registration details.
#
# To create an app registration:
#   1. Go to https://portal.azure.com → Microsoft Entra ID → App registrations → New registration
#   2. Name: graph-signin-audit
#   3. Supported account types: Accounts in this organizational directory only
#   4. Redirect URI: leave blank (device code flow doesn't need one)
#   5. Click Register → note the Application (client) ID
#   6. API permissions → Add permission → Microsoft Graph → Delegated → AuditLog.Read.All → Add
#   7. Click Grant admin consent

CLIENT_ID = "YOUR_CLIENT_ID_HERE"
TENANT_ID = "common"  # Use "common" for multi-tenant, or your specific tenant ID
