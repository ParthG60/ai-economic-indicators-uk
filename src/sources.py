"""Live parsers for UK Takeoff-Tracker series that have no ONS CDID (xlsx / zip only).
Each returns a tidy DataFrame [date, value] or raises (caller falls back to curated values)."""
import csv, io, re, zipfile, openpyxl, requests, pandas as pd
from ons_fetch import fetch_bytes, resolve_ons_current_xlsx, HDRS

# ---- ONS Capital Stocks (net, current prices) -> asset shares of total fixed assets ----
CAPSTOCK_URL = ("https://www.ons.gov.uk/file?uri=/economy/nationalaccounts/uksectoraccounts/datasets/"
                "grossandnetcapitalstocksfortotaleconomybyindustryandassetincurrentpricesandchainedvolumemeasures/"
                "current/grossandnetcapitalstockbyassetandindustry.xlsx")

def _capstock_table():
    raw = fetch_bytes(CAPSTOCK_URL, "capital_stocks.xlsx")
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb["Current prices"]; rows = list(ws.iter_rows(values_only=True))
    years = [c for c in rows[4][5:] if isinstance(c, (int, float))]
    out = {}  # asset_code -> {year: value}
    for r in rows[5:]:
        asset_code, measure, icode = r[3], r[1], r[4]
        if icode == "_T" and measure and "Net" in str(measure):
            vals = {}
            for yi, y in enumerate(years):
                v = r[5 + yi]
                try: vals[int(y)] = float(v)
                except (TypeError, ValueError): pass
            out[asset_code] = vals
    return out

def capital_stock_shares():
    """Net-stock asset shares mirroring Stanford's BEA capital-composition indicators:
      ip_equipment    = computer hardware / total fixed assets (IP-equipment share)
      software_share  = software / (software + R&D)                 [Stanford #9]
      intangible_share= (software + R&D) / total fixed assets       [Stanford #10]
    """
    t = _capstock_table()
    def ratio(num_codes, den_codes):
        yrs = sorted(set.intersection(*[set(t[c]) for c in (num_codes + den_codes)]))
        return pd.DataFrame({"date": pd.to_datetime([f"{y}-01-01" for y in yrs]),
                             "value": [sum(t[c][y] for c in num_codes) / sum(t[c][y] for c in den_codes) * 100 for y in yrs]})
    return {"ip_equipment":     ratio(["N11321N"], ["N11N"]),                 # computer hardware / total
            "software_share":   ratio(["N1173N"], ["N1173N", "N1171N"]),      # software / (software+R&D)
            "intangible_share": ratio(["N1173N", "N1171N"], ["N11N"])}        # (software+R&D) / total

# ---- BoE index-linked (real) gilt yield curve: 10-year spot, quarter-end ----
BOE_REAL_ZIP = "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/glcrealddata.zip"

def boe_real_yield_10y(since_year=1985):
    raw = fetch_bytes(BOE_REAL_ZIP, "boe_real.zip", max_age=86400)
    z = zipfile.ZipFile(io.BytesIO(raw))
    frames = []
    for name in z.namelist():
        if not name.lower().endswith(".xlsx"): continue
        if "glc real daily data" not in name.lower(): continue   # read ALL period files (1985->present)
        wb = openpyxl.load_workbook(io.BytesIO(z.read(name)), read_only=True, data_only=True)
        sn = [s for s in wb.sheetnames if "spot" in s.lower() and "short" not in s.lower()][0]
        rows = list(wb[sn].iter_rows(values_only=True))
        yrs = rows[3]
        col = min((i for i, v in enumerate(yrs) if isinstance(v, (int, float))),
                  key=lambda i: abs(float(yrs[i]) - 10.0))
        for r in rows[5:]:
            if r[0] and isinstance(r[col], (int, float)):
                frames.append((pd.Timestamp(r[0]), float(r[col])))
    df = pd.DataFrame(frames, columns=["date", "value"]).sort_values("date")
    df = df[df.date.dt.year >= since_year]
    q = df.set_index("date").resample("QE").last().dropna().reset_index()  # quarter-end
    return q

# ---- ONS UK trade in services by service type: computer-services imports (BoP, CP NSA) ----
# The Pink Book CDID FJDL is the annual source of record, but it publishes ~10 months after
# year-end. This granular dataset runs a year ahead on the same NSA basis (its values match
# FJDL exactly on the overlap), so the tracker can advance to the latest calendar year without
# waiting for the next Pink Book.
SERVICETYPE_PAGE = ("https://www.ons.gov.uk/businessindustryandtrade/internationaltrade/datasets/"
                    "uktradeinservicesservicetypebypartnercountrynonseasonallyadjusted")

def computer_services_imports():
    """Annual UK computer-services imports, current prices NSA, world total. Tidy [date, value]."""
    url = resolve_ons_current_xlsx(SERVICETYPE_PAGE)
    raw = fetch_bytes(url, "service_type_by_country.xlsx")
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb["Sheet 1. Time Series"]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[2]
    year_cols = {j: int(c) for j, c in enumerate(header)
                 if isinstance(c, str) and len(c) == 4 and c.isdigit()}   # annual cols only
    for r in rows[3:]:
        if r[0] == "Imports" and str(r[2]).strip() == "Computer services" and str(r[4]).strip() == "World total":
            recs = [(pd.Timestamp(f"{y}-01-01"), float(r[j])) for j, y in year_cols.items()
                    if j < len(r) and isinstance(r[j], (int, float))]
            return pd.DataFrame(recs, columns=["date", "value"]).sort_values("date").reset_index(drop=True)
    raise RuntimeError("computer services imports row not found in service-type dataset")

# ---- ONS Growth Accounting: Multi-Factor Productivity (market sector), annual ----
MFP_PAGE = ("https://www.ons.gov.uk/economy/economicoutputandproductivity/productivitymeasures/datasets/"
            "growthaccountingannualuk")

def mfp_market_sector(since_year=1995):
    url = resolve_ons_current_xlsx(MFP_PAGE)
    raw = fetch_bytes(url, "mfp.xlsx")
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb["Table_7"]; rows = list(ws.iter_rows(values_only=True))
    recs = []
    for r in rows:
        try:
            y = int(str(r[0]).strip()); v = float(r[1])  # col A year, col B Total (Market Sector)
            if 1900 < y < 2100: recs.append((pd.Timestamp(f"{y}-01-01"), v))
        except (TypeError, ValueError): pass
    df = pd.DataFrame(recs, columns=["date", "value"])
    return df[df.date.dt.year >= since_year].reset_index(drop=True)

# ---- DESNZ Energy Trends ET 5.1: total UK electricity generated (TWh), annual ----
ELEC_PAGE = "https://www.gov.uk/government/statistics/electricity-section-5-energy-trends"

def electricity_consumption(since_year=1998):
    """Total UK electricity SUPPLIED (incl. net interconnector imports), annual, TWh — the demand
    met, regardless of whether generated here or imported. ET 5.1 'Annual' sheet is transposed
    (years across columns, fuel rows down). The total is Table 5.1c 'electricity supplied by fuel'
    -> 'All generating companies / Total all generating companies' (already in TWh)."""
    import re
    html = __import__("requests").get(ELEC_PAGE, headers={"User-Agent": "uk-aiei/0.1"}, timeout=60).text
    links = sorted(set(re.findall(r'https://assets\.publishing\.service\.gov\.uk/media/[^"\']*?ET_5[._]1[^"\']*?\.xlsx', html)))
    if not links: raise RuntimeError("no ET 5.1 xlsx link on DESNZ page")
    raw = fetch_bytes(links[0], "energy_et51.xlsx")
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    sn = next(s for s in wb.sheetnames if s.strip().lower().startswith("annual"))
    rows = list(wb[sn].iter_rows(values_only=True))
    def yr(c):
        try: v = int(str(c).strip()); return v if 1900 < v < 2100 else None
        except (TypeError, ValueError): return None
    i5b = next(i for i, r in enumerate(rows) if isinstance(r[0], str) and "electricity supplied by fuel" in r[0].strip().lower())
    i_tot = next(i for i in range(i5b, len(rows))
                 if len(rows[i]) > 1 and isinstance(rows[i][1], str) and "total all generating companies" in rows[i][1].lower())
    i_hdr = max(i for i in range(0, i_tot) if sum(1 for c in rows[i] if yr(c)) >= 5)  # nearest year header above
    year_cols = {j: yr(c) for j, c in enumerate(rows[i_hdr]) if yr(c)}
    tot = rows[i_tot]
    recs = [(pd.Timestamp(f"{y}-01-01"), float(tot[j])) for j, y in year_cols.items()
            if j < len(tot) and isinstance(tot[j], (int, float))]
    df = pd.DataFrame(recs, columns=["date", "value"]).sort_values("date")
    if df.empty: raise RuntimeError("ET 5.1 parse found no annual generation rows")
    return df[df.date.dt.year >= since_year].reset_index(drop=True)

# ---- DESNZ Energy Trends ET 1.2: inland primary energy consumption (Mtoe), annual ----
ENERGY_PAGE = "https://www.gov.uk/government/statistics/total-energy-section-1-energy-trends"

def primary_energy(since_year=2000):
    import re
    html = __import__("requests").get(ENERGY_PAGE, headers={"User-Agent": "uk-aiei/0.1"}, timeout=60).text
    links = sorted(set(re.findall(r'https://assets\.publishing\.service\.gov\.uk/media/[^"\']*?ET_1[._]2[^"\']*?\.xlsx', html)))
    if not links: raise RuntimeError("no ET 1.2 xlsx link on DESNZ page")
    raw = fetch_bytes(links[0], "energy_et12.xlsx")
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb["Annual"]; recs = []
    for r in ws.iter_rows(values_only=True):
        try:
            y = int(str(r[0]).strip()); v = float(r[1])  # col A year, col B unadjusted total
            if 1900 < y < 2100: recs.append((pd.Timestamp(f"{y}-01-01"), v))
        except (TypeError, ValueError): pass
    df = pd.DataFrame(recs, columns=["date", "value"])
    return df[df.date.dt.year >= since_year].reset_index(drop=True)

# ================================================================ ADOPTION (surveys)
_MONTHS = {m: f"{i:02d}" for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}

# ---- ONS BICS: canonical firm AI adoption (10+ employees) ----
# The BICS workbook itself carries only the DSIT-consistent-definition "All businesses" series
# and per-size-band rows. The canonical 10+ employees headline ONS now leads with lives in the
# "Artificial intelligence in UK businesses" article (Figure 1), downloadable as a chart CSV.
BICS_AI_SEARCH = "https://www.ons.gov.uk/search?q=artificial+intelligence+in+UK+businesses"

def bics_firm_adoption():
    """Live canonical BICS firm AI-adoption (10+ employees) from the latest ONS 'Artificial
    intelligence in UK businesses' article. Returns tidy [date (YYYY-MM), firm_10plus_pct]."""
    html = requests.get(BICS_AI_SEARCH, headers=HDRS, timeout=60).text
    arts = re.findall(r"(/businessindustryandtrade/business/businessservices/articles/"
                      r"artificialintelligenceinukbusinesses/\d{4}to\d{4})", html)
    if not arts:
        raise RuntimeError("no BICS AI article found in ONS search")
    art = "https://www.ons.gov.uk" + sorted(set(arts))[-1]
    art_html = requests.get(art, headers=HDRS, timeout=60).text
    m = re.search(r'href="(/generator\?uri=[^"]*artificialintelligenceinukbusinesses[^"]*&format=csv)"', art_html)
    if not m:
        raise RuntimeError("no Figure 1 chart CSV on BICS AI article")
    csv_text = requests.get("https://www.ons.gov.uk" + m.group(1), headers=HDRS, timeout=60).text
    recs = []
    for cells in csv.reader(io.StringIO(csv_text)):
        if len(cells) < 2:
            continue
        try:
            val = float(cells[1].strip())
        except (TypeError, ValueError):
            continue
        d = re.search(r"(\d{1,2}\s+[A-Za-z]+)\s+(\d{4})", cells[0])     # first (start) date in period
        if d:
            mon = d.group(1).split()[1].lower()
            if mon in _MONTHS:
                recs.append({"date": f"{d.group(2)}-{_MONTHS[mon]}", "firm_10plus_pct": val})
    if not recs:
        raise RuntimeError("BICS AI Figure 1 CSV parse found no rows")
    return (pd.DataFrame(recs).drop_duplicates("date", keep="last")
            .sort_values("date").reset_index(drop=True))

# ---- ONS OPN: AI sentiment (Table 7 trend) ----
OPN_AI_PAGE = ("https://www.ons.gov.uk/peoplepopulationandcommunity/wellbeing/datasets/"
               "publicopinionsandsocialtrendsgreatbritainartificialintelligenceai")

def opn_ai_sentiment():
    """ONS Opinions and Lifestyle Survey AI module Table 7: % GB adults agreeing AI will benefit
    them (Nov 2023 onward). Returns tidy [date (YYYY-MM), agree_ai_benefits_me_pct]."""
    html = requests.get(OPN_AI_PAGE, headers=HDRS, timeout=60).text
    xlsxs = [x for x in re.findall(r'href="(/file\?uri=[^"]*\.xlsx)"', html)
             if "artificialintelligence" in x.lower() or "publicawareness" in x.lower()]
    if not xlsxs:
        raise RuntimeError("no OPN AI xlsx found")
    raw = fetch_bytes("https://www.ons.gov.uk" + xlsxs[0], "opn_ai.xlsx")   # newest listed first
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    recs = []
    for row in wb["Table_7"].iter_rows(values_only=True):
        if not row or row[0] is None or row[1] is None:
            continue
        try:
            val = float(row[1])
        except (TypeError, ValueError):
            continue
        m = re.search(r"([A-Za-z]+)\s+(20\d{2})", str(row[0]))
        if m and m.group(1).lower() in _MONTHS:
            recs.append({"date": f"{m.group(2)}-{_MONTHS[m.group(1).lower()]}",
                         "agree_ai_benefits_me_pct": int(val)})
    if not recs:
        raise RuntimeError("OPN Table 7 parse found no rows")
    return (pd.DataFrame(recs).drop_duplicates("date", keep="last")
            .sort_values("date").reset_index(drop=True))
