import sys, re
import pandas as pd

path = sys.argv[1]
df = pd.read_csv(path, low_memory=False)

# 風/波っぽい列を拾う（表記ゆれ想定）
cols = [c for c in df.columns if re.search(r'wind|wave|kaze|nami|風|波', c, re.I)]
print("report=", path)
print("candidate cols:", cols)

if not cols:
    print("NO wind/wave-like columns found.")
    sys.exit(0)

for c in cols:
    s = pd.to_numeric(df[c], errors="coerce")
    nn = int(s.notna().sum())
    print(f"{c}: non_null={nn} / total={len(df)}  sample={s.dropna().head(5).tolist()}")
