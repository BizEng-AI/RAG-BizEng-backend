"""
Temp admin endpoint probe.
Writes results into ./admin_test_results/ as <endpoint>.json and <endpoint>_headers.txt
Usage:
  python temp_admin_probe.py --token <TOKEN> --base-url <BASE_URL>
Or set env vars: ADMIN_PROBE_TOKEN, BASE_URL
"""
from __future__ import annotations

import os
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def build_session(retries: int = 3, backoff: float = 0.5) -> requests.Session:
    s = requests.Session()
    retry = Retry(total=retries, backoff_factor=backoff, status_forcelist=(500,502,503,504), allowed_methods=("GET",))
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


def run_probe(token: str, base: str, out_dir: Path) -> Dict[str, Any]:
    if not token:
        raise ValueError("No token provided. Use --token or set ADMIN_PROBE_TOKEN env var")
    if not base.startswith("http://") and not base.startswith("https://"):
        base = "https://" + base

    headers = {"Authorization": f"Bearer {token}"}
    session = build_session()

    endpoints = [
        "overview",
        "activity_events",
        "exercise_attempts",
        "attempts",
        "events",
        "sessions",
        "users",
        "users_signups",
        "user_roles",
        "roles",
        "skill_map_id",
        "skill_map_type",
        "vw_attempts",
        "playing_with_neon",
        "refresh_tokens",
    ]

    summary: Dict[str, Any] = {}

    out_dir.mkdir(parents=True, exist_ok=True)

    for ep in endpoints:
        url = f"{base.rstrip('/')}/admin/monitor/{ep}"
        try:
            r = session.get(url, headers=headers, timeout=20)
            status = r.status_code
            # try to parse JSON
            try:
                body = r.json()
                body_text = json.dumps(body, indent=2, ensure_ascii=False)
            except Exception:
                body_text = r.text

            body_file = out_dir / f"{ep}.json"
            body_file.write_text(body_text, encoding="utf-8")

            headers_file = out_dir / f"{ep}_headers.txt"
            hdrs = "\n".join([f"{k}: {v}" for k, v in r.headers.items()])
            headers_file.write_text(hdrs, encoding="utf-8")

            summary[ep] = {"status": status, "body_file": str(body_file), "headers_file": str(headers_file)}
        except Exception as e:
            summary[ep] = {"error": str(e)}

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv=None):
    p = argparse.ArgumentParser(description="Probe admin monitor endpoints and save responses")
    p.add_argument("--token", help="Access token to use (or set ADMIN_PROBE_TOKEN env var)")
    p.add_argument("--base-url", help="Base URL of server (or set BASE_URL env var)", default=os.environ.get("BASE_URL", "https://bizeng-server.fly.dev"))
    p.add_argument("--out", help="Output directory", default="admin_test_results")
    args = p.parse_args(argv)

    token = args.token or os.environ.get("ADMIN_PROBE_TOKEN") or os.environ.get("TOKEN")
    base = args.base_url
    out_dir = Path(args.out)

    try:
        summary = run_probe(token, base, out_dir)
    except Exception as e:
        print("Probe failed:", e, file=sys.stderr)
        sys.exit(2)

    # Print concise summary to stdout
    print(f"WROTE {out_dir} with summary.json")
    compact = {k: (v.get("status") if isinstance(v, dict) else None) for k, v in summary.items()}
    print(json.dumps(compact, indent=2))


if __name__ == '__main__':
    main()
