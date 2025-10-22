import argparse
from pathlib import Path
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--input", required=True, help="path to .parquet")
ap.add_argument("--head", type=int, default=0, help="preview N rows")
ap.add_argument("--out", help="CSV output path")
args = ap.parse_args()

df = None
if args.head > 0:
    df = pd.read_parquet(args.input)
    print(df.shape)
    print(df.head(args.head))

if args.out:
    if df is None:
        df = pd.read_parquet(args.input)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"wrote: {args.out} rows={len(df):,}")
