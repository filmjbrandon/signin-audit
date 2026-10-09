#!/usr/bin/env python3
"""
Microsoft Graph API — Failed Sign-In Audit

Authenticates via device code flow, pulls sign-in logs from the last 30 days,
and counts unsuccessful events per day.

Usage:
    1. Set CLIENT_ID in config.py (or as env var MSGRAPH_CLIENT_ID)
    2. python signin_audit.py
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import msal
import requests

try:
    from config import CLIENT_ID, TENANT_ID
except ImportError:
    import os
    CLIENT_ID = os.environ.get("MSGRAPH_CLIENT_ID", "")
    TENANT_ID = os.environ.get("MSGRAPH_TENANT_ID", "common")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["AuditLog.Read.All"]
GRAPH_API = "https://graph.microsoft.com/v1.0"
DAYS_BACK = 30


def authenticate():
    """Authenticate using device code flow and return an access token."""
    if not CLIENT_ID:
        print("ERROR: No client ID configured.")
        print("Create a config.py file with CLIENT_ID set, or set MSGRAPH_CLIENT_ID env var.")
        sys.exit(1)

    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

    # Try to get a token silently first (from cache)
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPE, account=accounts[0])
        if result and "access_token" in result:
            print("✓ Authenticated silently (cached token)")
            return result["access_token"]

    # Fall back to device code flow
    flow = app.initiate_device_flow(scopes=SCOPE)
    if "user_code" not in flow:
        print("ERROR: Could not create device flow. Check your CLIENT_ID.")
        sys.exit(1)

    print(f"\nTo authenticate, go to: {flow['verification_uri']}")
    print(f"Enter code: {flow['user_code']}\n")

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        print(f"ERROR: Authentication failed — {result.get('error_description', 'unknown error')}")
        sys.exit(1)

    print("✓ Authenticated successfully")
    return result["access_token"]


def fetch_signins(access_token, start_date, end_date):
    """Fetch sign-in logs from Microsoft Graph within the date range, handling pagination."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    filter_str = (
        f"createdDateTime ge {start_date.isoformat()} "
        f"and createdDateTime le {end_date.isoformat()}"
    )

    url = f"{GRAPH_API}/auditLogs/signIns"
    params = {"$filter": filter_str, "$top": 999}

    all_signins = []
    page_count = 0

    while url:
        page_count += 1
        print(f"  Fetching page {page_count}...", end="\r")

        response = requests.get(url, headers=headers, params=params if page_count == 1 else None)

        if response.status_code != 200:
            print(f"\nERROR: Graph API returned {response.status_code}")
            print(response.text)
            sys.exit(1)

        data = response.json()
        all_signins.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
        params = None

    print(f"  Fetched {len(all_signins)} total sign-in records across {page_count} pages.")
    return all_signins


def count_failures_per_day(signins, start_date, end_date):
    """Count unsuccessful sign-in events per day."""
    failure_counts = {}
    current = start_date.date()
    end = end_date.date()
    while current <= end:
        failure_counts[current.isoformat()] = 0
        current += timedelta(days=1)

    for signin in signins:
        status = signin.get("status", {})
        error_code = status.get("errorCode", 0)
        if error_code != 0:
            created = signin.get("createdDateTime", "")
            if created:
                day = created[:10]
                if day in failure_counts:
                    failure_counts[day] += 1

    return failure_counts


def print_results(failure_counts):
    """Print the results in a readable table."""
    print("\n" + "=" * 50)
    print("  FAILED SIGN-INS PER DAY (Last 30 Days)")
    print("=" * 50)
    print(f"  {'Date':<14} {'Failed Count':>12}")
    print("-" * 50)

    total = 0
    for date_str in sorted(failure_counts.keys()):
        count = failure_counts[date_str]
        total += count
        bar = "█" * min(count, 40)
        print(f"  {date_str:<14} {count:>12}  {bar}")

    print("-" * 50)
    print(f"  {'TOTAL':<14} {total:>12}")
    print("=" * 50)


def main():
    print("Microsoft Graph — Failed Sign-In Audit")
    print("=" * 40)

    access_token = authenticate()

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=DAYS_BACK)

    print(f"\nDate range: {start_date.date()} to {end_date.date()}")

    print("\nFetching sign-in logs...")
    signins = fetch_signins(access_token, start_date, end_date)

    if not signins:
        print("\nNo sign-in records found in this period.")
        return

    failure_counts = count_failures_per_day(signins, start_date, end_date)
    print_results(failure_counts)

    output_file = "failed_signins_report.json"
    with open(output_file, "w") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "date_range": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
            },
            "total_records_fetched": len(signins),
            "failed_signins_per_day": failure_counts,
        }, f, indent=2)
    print(f"\n✓ Report saved to {output_file}")


if __name__ == "__main__":
    main()
