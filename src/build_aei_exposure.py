"""
Build a SOC2020 -> AI automation-share table from the Anthropic Economic Index (free, MIT).

AEI classifies how Claude is used per O*NET task into collaboration modes. Following AEI's own
split: AUTOMATION = directive + feedback_loop; AUGMENTATION = validation + task_iteration +
learning. We compute an automation share per task, average to US O*NET-SOC, crosswalk to ISCO-08
(BLS ISCO<->SOC2010 crosswalk), then to UK SOC2020 (ONS coding-index crosswalk) via ISCO — the
common key the rest of the project already uses.

Output: reference/aei_automation_by_soc2020.csv  (SOC2020, aei_automation_share)
This is the Stanford 'automation vs augmentation' layer: high share = AI tends to DO the task
(displacement risk); low share = AI tends to ASSIST (augmentation). Run once; trackers read the CSV.
Run: python src/build_aei_exposure.py
"""
import os, io, requests, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "reference")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
AEI = "https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2025_03_27/"

def get_csv(url, **kw):
    return pd.read_csv(io.StringIO(requests.get(url, headers=UA, timeout=90).text), **kw)

# 1. automation share per US O*NET-SOC
aa = get_csv(AEI + "automation_vs_augmentation_by_task.csv")
aa["auto"] = aa.directive + aa.feedback_loop
aa["aug"] = aa.validation + aa.task_iteration + aa.learning
aa["auto_share"] = aa.auto / (aa.auto + aa.aug)
aa["key"] = aa.task_name.str.strip().str.lower()
on = get_csv(AEI + "onet_task_statements.csv")
on["key"] = on["Task"].str.strip().str.lower(); on["soc2010"] = on["O*NET-SOC Code"].str[:7]
occ = (aa.merge(on[["key", "soc2010"]], on="key", how="inner")
         .groupby("soc2010").auto_share.mean())

# 2. SOC2010 -> ISCO-08 (BLS crosswalk), aggregate automation per ISCO
raw = requests.get("https://www.bls.gov/soc/ISCO_SOC_Crosswalk.xls", headers=UA, timeout=60).content
bls = pd.read_excel(io.BytesIO(raw), header=6)
bls = bls.rename(columns={"ISCO-08 Code": "isco", "2010 SOC Code": "soc2010"})[["isco", "soc2010"]].dropna()
bls["isco"] = bls.isco.astype(str).str.extract(r"(\d+)")[0].str.zfill(4)
bls["soc2010"] = bls.soc2010.astype(str).str.strip()
isco_auto = (bls.merge(occ.rename("auto").reset_index(), on="soc2010", how="inner")
               .groupby("isco").auto.mean())

# 3. UK SOC2020 -> ISCO-08 (project crosswalk) -> attach automation share
cw = pd.read_csv(os.path.join(REF, "soc2020_isco08_crosswalk.csv"))[["SOC2020", "ISCO08"]]
cw["isco"] = cw.ISCO08.astype(str).str.extract(r"(\d+)")[0].str.zfill(4)
out = cw.merge(isco_auto.rename("aei_automation_share").reset_index(), on="isco", how="left")
out = out[["SOC2020", "aei_automation_share"]].dropna()
out.to_csv(os.path.join(REF, "aei_automation_by_soc2020.csv"), index=False)

print(f"AEI automation layer: {len(out)} SOC2020 occupations scored "
      f"(automation share {out.aei_automation_share.min():.2f}-{out.aei_automation_share.max():.2f}, "
      f"mean {out.aei_automation_share.mean():.2f})")
print("  saved -> reference/aei_automation_by_soc2020.csv")
