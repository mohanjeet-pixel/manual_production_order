import pandas as pd
from pathlib import Path


def preprocess_excel(input_file, output_file):

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_file)

    df.columns = [
        str(col).strip().lower().replace("_", " ")
        for col in df.columns
    ]

    df = df.dropna(how="all")

    df = df.drop_duplicates()

    df.to_csv(output_file, index=False)

    print(f"✅ Preprocessed file saved: {output_file}")

    return output_file
