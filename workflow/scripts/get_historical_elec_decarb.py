import pandas as pd
import requests
import os
from io import StringIO
from pathlib import Path


def process_countries_elec_decarb(input_dir: str, countries, output_file: str, year):
    """
    Processes IEA energy balance CSV files for specified countries to calculate decarbonisation
    level of electricity produced in each country. Calculated based on the share of electricity
    produced from non-carbon carriers (hydro, nuclear, solar, wind, etc.), not based on the final
    energy spent for producing electricity (efficiency already included).

    Assumption: the whole country, in all sectors, shares the same grid.

    Note that if the country haavily imports electricity, the electricity production decarbonisation
    level in this country may not reflect the actual decarbonisation level of electricity consumed
    in this country.

    Unit of data: GWh, not TJ! But this does not affect the output as it is dimensionless.


    Parameters:
    - input_dir: Directory to extract all the downloaded files.
    - countries: list - List of country codes to process, given in ISO3 codes.
    - output_file: str - Path to save the processed one CSV file.
    - year: int - The year to process the data for.

    """

    # Hard-coded list of carriers
    list_nonCarb_carriers = [
        "EHBIOMASS",
        "EHWASTE",
        "EHNUCLEAR",
        "EHYDRO",
        "ESOLARPV",
        "EWIND",
        "EHSOLARTH",
        "EHGEOTHERM",
        "ETIDE",
    ]
    list_carriers = ["EHOIL", "EHNATGAS", "EHCOAL"] + list_nonCarb_carriers

    # Iterate over countries
    input_path = Path(input_dir)
    files = [str(file) for file in input_path.iterdir() if file.is_file()]
    i = 0  # flag for initialise
    for file in files:
        if (str(year) in file) & (file.split("_")[-2] in countries):
            country = file.split("_")[-2]
            df = pd.read_csv(file)
            # Step 1. Get electricity production by carrier of the given year
            df_year = df[
                (df["year"] == year)
                & (df["product"] == "ELECTR")
                & (df["flow"].isin(list_carriers))
            ]
            df_year = df_year.pivot(index="short", columns="flow", values="value")
            # Step 2. Calculate the decarbonisation level
            # Sum up electricity production from all carriers
            df_year["CALC_TOTAL"] = df_year.loc[df["short"].unique()[0], :].sum()
            df_year["CALC_NONCARB"] = 0
            # Sum up electricity production from non-carbon carriers
            for carrier in list_nonCarb_carriers:
                if carrier in df_year.columns:
                    df_year.loc[df["short"].unique()[0], "CALC_NONCARB"] += df_year.loc[
                        df["short"].unique()[0], carrier
                    ]
            # Divide such production by total production to get decarbonisation level
            df_year["ELEC_DECARB"] = df_year["CALC_NONCARB"] / df_year["CALC_TOTAL"]
            # Add country code
            df_year["ISO3"] = country
            # Append the current country to the total countries dataframe
            if i == 0:
                df_all = df_year
            else:
                df_all = pd.concat([df_all, df_year], ignore_index=True)
            i += 1

    # Do some cleaning
    # Move the country code to the front of the dataframe
    df_all = df_all[["ISO3"] + [c for c in df_all.columns if c != "ISO3"]]
    # Move the calculations to the back of the dataframe
    df_all = df_all[
        [
            c
            for c in df_all.columns
            if c not in ["CALC_TOTAL", "CALC_NONCARB", "ELEC_DECARB"]
        ]
        + ["CALC_TOTAL", "CALC_NONCARB", "ELEC_DECARB"]
    ]
    df_all = df_all.fillna(0).round(4)

    # Create the folder to keep the processed csv
    output_dir = output_file.split("IEA")[0]
    os.makedirs(output_dir, exist_ok=True)
    df_all.to_csv(output_file, index=False)


if __name__ == "__main__":
    process_countries_elec_decarb(
        input_dir=snakemake.input.input_dir,
        countries=snakemake.params.countries,
        output_file=snakemake.output.output_file,
        year=snakemake.params.year,
    )
