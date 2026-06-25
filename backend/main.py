from preprocess import preprocess_excel
from db_connection import load_to_postgres


def run_pipeline():

    print("=" * 50)
    print("🚀 MANUAL ORDER ETL PIPELINE STARTED")
    print("=" * 50)

    input_excel = "../data/Dev Part.xlsx"
    output_csv = "output/clean_data.csv"

    csv_file = preprocess_excel(
        input_excel,
        output_csv
    )

    load_to_postgres(
        csv_file,
        "products"
    )

    print("=" * 50)
    print("🎉 ETL PIPELINE COMPLETED")
    print("=" * 50)


if __name__ == "__main__":
    run_pipeline()