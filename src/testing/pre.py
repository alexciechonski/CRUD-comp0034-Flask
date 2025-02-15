import pandas as pd

df = pd.read_csv("src/testing/deaths.csv")
df = df.drop(columns=["Unnamed: 0"], errors="ignore")
df.to_csv("src/testing/deaths.csv", index=False)

