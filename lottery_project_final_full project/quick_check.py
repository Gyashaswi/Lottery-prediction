import pandas as pd
from pathlib import Path

for csvfile in Path("data/processed").glob("*.csv"):
    print("\nChecking", csvfile)
    if csvfile.stat().st_size == 0:
        print("  empty file")
        continue
    df = pd.read_csv(csvfile)
    print(df.head())
    print("Rows:", len(df))