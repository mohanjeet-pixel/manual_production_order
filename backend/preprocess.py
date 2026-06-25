import pandas as pd
from pathlib import Path


def preprocess_excel(input_file, output_file):
    """
    Read Excel file and convert to cleaned CSV
    """

    # Create output folder if not exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # Read Excel
    df = pd.read_excel(input_file)

    # Clean column names
    df.columns = [
        str(col).strip().lower().replace("_", " ")
        for col in df.columns
    ]

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Remove duplicates
    df = df.drop_duplicates()

    # Save CSV
    df.to_csv(output_file, index=False)

    print(f"✅ Preprocessed file saved: {output_file}")

    return output_file


if __name__ == "__main__":
    preprocess_excel(
        "data/Dev Part.xlsx",
        "output/clean_data.csv"
    )
