import pandas as pd
import os
from pathlib import Path


def process_countries_other_renewables_prod(
    input_dir: str, countries, output_file: str, year: int
):
    """
    Processes IEA electricity balance CSV files for specified countries to extract other_renewables
     such as hydropower and nuclear electricity production (final output).

    Parameters:
    - input_dir: Directory to extract all the downloaded files.
    - countries: list - List of country codes to process, given in ISO3 codes.
    - output_file: str - Path to save the processed one CSV file.
    - year: int - The year to get production data from.

    Unit: GWh, converted into TJ

    """

    # Hard-coded list of sectors and carriers
    flow_labels = [
        "EHYDRO",
        "EHNUCLEAR",
        "EHBIOMASS",
        "EHWASTE",
        "EHGEOTHERM",
        "EHOTHER",
    ]

    # Iterate over countries
    input_path = Path(input_dir)
    files = [str(file) for file in input_path.iterdir() if file.is_file()]
    i = 0  # flag for initialise
    for file in files:
        if (str(year) in file) & (file.split("_")[-2] in countries):
            country = file.split("_")[-2]
            df = pd.read_csv(file)
            # Step 1. Get electricity production by carrier of the given year
            df_year = df[(df["year"] == year) & (df["product"] == "ELECTR")]
            df_year = df_year.pivot(
                index="short", columns="flow", values="value"
            ).fillna(0)
            # Step 2. Get other renewables output
            # Sum up electricity production from all carriers
            df_year["OTHER_RENEWABLES"] = 0
            for flow_label in flow_labels:
                if flow_label in df_year:
                    df_year["OTHER_RENEWABLES"] += df_year[flow_label]
            # Convert from GWh to TJ
            df_year["OTHER_RENEWABLES"] *= 3600 / 1e3
            # Add country code
            df_year["ISO3"] = country
            # Append the current country to the total countries dataframe
            if i == 0:
                df_all = df_year
            else:
                df_all = pd.concat([df_all, df_year], ignore_index=True)
            i += 1

    # Do some cleaning
    df_all = df_all[["ISO3", "OTHER_RENEWABLES"]].fillna(0).round(4)

    # Create the folder to keep the processed csv
    output_dir = output_file.split("IEA")[0]
    os.makedirs(output_dir, exist_ok=True)
    df_all.to_csv(output_file, index=False)


if __name__ == "__main__":
    process_countries_other_renewables_prod(
        input_dir=snakemake.input.input_dir,
        countries=snakemake.params.countries,
        output_file=snakemake.output.output_file,
        year=snakemake.params.year,
    )
