import pandas as pd
import os


def download_WPP_population(output_file: str):
    """
    Downloads the United Nations World Population Prospects data and saves it as a CSV file.

    Unit: thousands of persons.

    Parameters:
    - output_path: str - The path to save the downloaded CSV file.
    - scenario: str - The population projection scenario to filter the data by. Default is 'Medium' - there is real-world data
    before 2025.
    """

    URL = "https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/CSV_FILES/WPP2024_TotalPopulationBySex.csv.gz"
    df = pd.read_csv(URL, compression="gzip")

    # Hard-code the needed rows by us
    needed_rows = [
        "ISO3_code",
        "ISO2_code",
        "Location",
        "Variant",
        "Time",
        "LocTypeName",
        "PopTotal",
        "PopDensity",
    ]
    df = df[needed_rows]
    # Select only countries, not regions
    country_csv = df[df["ISO3_code"].notna()]
    # Hard-code the relevant years defined by us
    years = [2020, 2023, 2024, 2025, 2030, 2035, 2040, 2045, 2050]
    country_csv_years = country_csv[country_csv["Time"].isin(years)]

    # Select only the scenario defined by us
    population_scenario = snakemake.wildcards.population_scenario
    country_csv_scenario = country_csv_years[
        country_csv_years["Variant"] == population_scenario
    ]
    # Save to csv
    # Create the folder to keep the original csvs
    output_path = output_file.split("WPP_population/")[0]
    os.makedirs(output_path, exist_ok=True)
    country_csv_scenario.to_csv(output_file, index=False)


if __name__ == "__main__":
    download_WPP_population(output_file=snakemake.output.output_file)
