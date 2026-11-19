import pandas as pd
import requests
import os
from io import StringIO


def get_EnergyBalance_df(
    country, year
):  # if given an invalid string, this function just returns every country's value
    URL = "https://api.iea.org/stats?year={year}&countries={country}&series=BALANCES"
    r = requests.get(URL.format(country=country, year=year))
    return pd.read_json(StringIO(r.text))


def download_iea_balances(country_codes_path: str, output_dir: str, year: int = 2023):
    """
    Downloads IEA energy balances for specified country codes and saves as CSV files to resources/automatic as intermediary files.

    Parameters:
    - country_codes_path: str - path to the country codes csv to get the data.
    - output_dir: str - The path to save the downloaded CSV files.
    - year: int - The year to download the data for.
    """

    # Get the list of country codes from the provided CSV file
    country_codes = pd.read_csv(country_codes_path)

    # Create the folder to keep the original csvs
    os.makedirs(output_dir, exist_ok=True)

    # Download the raw data from IEA
    for i, country in country_codes.iterrows():
        if type(country["IEA"]) is not float:
            get_EnergyBalance_df(country["IEA"], year).to_csv(
                output_dir
                + "/IEA_EnergyBalance_"
                + country["ISO3"]
                + "_"
                + str(year)
                + ".csv",
                index=False,
            )


if __name__ == "__main__":
    download_iea_balances(
        country_codes_path=snakemake.input.country_codes_file,
        output_dir=snakemake.output.output_dir,
        year=snakemake.params.year,
    )
