import json

with open("api_test_results.json", encoding="utf-8") as f:
    data = json.load(f)

summary = data["summary"]
print("=" * 80)
print("AUDIT RESULTS SUMMARY:")
print(f"Total Endpoints Tested: {summary['total']}")
print(f"Successful (2xx): {summary['success']}")
print(f"Server Crashes (500): {summary['server_errors']}")
print(f"Client Errors (4xx): {summary['client_errors']}")
print(f"Auth Forbidden (401/403): {summary['auth_forbidden']}")
print("=" * 80)

crashes = [r for r in data["results"] if r["classification"] == "SERVER_ERROR"]
print(f"\nAnalyzing {len(crashes)} Server Crashes...")

grouped = {}
for c in crashes:
    exc = c.get("exception") or {}
    etype = exc.get("error_type", "Unknown")
    emsg = exc.get("error_msg", str(c.get("response", "")))
    first_line = emsg.split("\n")[0] if emsg else "Unknown error"
    
    # Extract root cause category
    category = "Other"
    if "relation" in emsg and "does not exist" in emsg:
        # e.g. relation "interview_experiences" does not exist
        table = emsg.split('relation "')[1].split('"')[0] if 'relation "' in emsg else "unknown_table"
        category = f"Missing PostgreSQL Table: '{table}'"
    elif "column" in emsg and "does not exist" in emsg:
        col = emsg.split('column "')[1].split('"')[0] if 'column "' in emsg else "unknown_col"
        category = f"Missing PostgreSQL Column: '{col}'"
    elif "GEMINI_API_KEY" in emsg or "gemini" in emsg.lower() or "google" in emsg.lower() or "api_key" in emsg.lower():
        category = "LLM / Gemini API Configuration Missing or Failed"
    elif "Connection refused" in emsg or "10061" in emsg or "redis" in emsg.lower():
        category = "External Service Connection Failed (Redis / Celery / Superset)"
    elif "AttributeError" in etype:
        category = f"AttributeError: {first_line}"
    elif "TypeError" in etype:
        category = f"TypeError: {first_line}"
    elif "KeyError" in etype:
        category = f"KeyError: {first_line}"
    else:
        category = f"{etype}: {first_line}"

    grouped.setdefault(category, []).append({
        "index": c["index"],
        "method": c["method"],
        "path": c["path_pattern"],
        "resolved": c["resolved_url"],
        "error_type": etype,
        "first_line": first_line,
        "traceback_tail": "\n".join((exc.get("traceback") or "").split("\n")[-6:])
    })

print(f"\nFound {len(grouped)} distinct Root Cause Categories:\n")
for cat, items in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"[{len(items):2d} endpoints] -> {cat}")
    for item in items[:5]:
        print(f"     #{item['index']:3d}: {item['method']:6} {item['path']}")
    if len(items) > 5:
        print(f"     ... and {len(items)-5} more endpoints")
    print()

# Check client errors (4xx)
client_errs = [r for r in data["results"] if r["classification"] == "CLIENT_ERROR"]
print("=" * 80)
print(f"Analyzing {len(client_errs)} Client Errors (4xx)...")
for ce in client_errs:
    print(f"#{ce['index']:3d}: [{ce['status_code']}] {ce['method']:6} {ce['resolved_url']:45} -> {ce['response']}")

