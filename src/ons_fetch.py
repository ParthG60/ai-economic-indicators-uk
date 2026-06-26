"""Tiny ONS time-series fetcher. The old api.ons.gov.uk host is DEAD (decommissioned
Nov 2024) -> use www.ons.gov.uk/{topic-path}/timeseries/{cdid}/{dataset}/data which
returns JSON with 'months'/'quarters'/'years' arrays. Results cached to data/takeoff/raw/."""
import os, json, time, requests, pandas as pd

RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "takeoff", "raw")
os.makedirs(RAW, exist_ok=True)
HDRS = {"User-Agent": "uk-aiei-takeoff-tracker/0.1"}

def fetch_bytes(url, cache_name, max_age=86400):
    """Download a binary file (xlsx/zip), caching to data/takeoff/raw/. Returns bytes."""
    cache = os.path.join(RAW, cache_name)
    if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < max_age:
        return open(cache, "rb").read()
    r = requests.get(url, headers=HDRS, timeout=180); r.raise_for_status()
    open(cache, "wb").write(r.content)
    return r.content

def resolve_ons_current_xlsx(dataset_page_url):
    """Scrape an ONS dataset landing page for its /current/*.xlsx download link (filenames rotate)."""
    import re
    html = requests.get(dataset_page_url, headers=HDRS, timeout=60).text
    m = re.findall(r'/file\?uri=[^"\']*?/current/[^"\']*?\.xlsx', html)
    if not m: raise RuntimeError(f"no current xlsx found on {dataset_page_url}")
    return "https://www.ons.gov.uk" + m[0].replace("&amp;", "&")

def fetch_series(path, cdid, dataset, prefer="quarters"):
    """Return a tidy DataFrame [date, value] for an ONS series. Caches JSON locally."""
    cache = os.path.join(RAW, f"{cdid.lower()}_{dataset.lower()}.json")
    url = f"https://www.ons.gov.uk/{path}/timeseries/{cdid.lower()}/{dataset.lower()}/data"
    js = None
    if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < 86400:
        try: js = json.load(open(cache))
        except Exception: js = None
    if js is None:
        r = requests.get(url, headers=HDRS, timeout=30); r.raise_for_status(); js = r.json()
        json.dump(js, open(cache, "w"))
    rows = js.get(prefer) or js.get("quarters") or js.get("months") or js.get("years") or []
    if not rows: rows = js.get("years", [])
    df = pd.DataFrame([{"date": d.get("date"), "value": float(d["value"])} for d in rows if d.get("value") not in (None, "")])
    # normalise dates: "2026 Q1" / "2024" / "2026 JAN" -> period start timestamp
    def _to_ts(s):
        s = str(s).strip()
        try:
            if "Q" in s:
                y, q = s.split(" Q"); return pd.Timestamp(int(y), (int(q)-1)*3+1, 1)
            if len(s) == 4 and s.isdigit(): return pd.Timestamp(int(s), 1, 1)
            return pd.to_datetime(s)
        except Exception: return pd.NaT
    df["date"] = df["date"].map(_to_ts)
    return df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
