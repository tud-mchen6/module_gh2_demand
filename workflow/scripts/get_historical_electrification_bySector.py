import pandas as pd
import os


def process_countries_electrification_bySector(
    inputs: str, countries, output_file: str
):
    """
    Processes IEA energy balance CSV files for specified countries to extract electrification rate by sector.

    Parameters:
    - inputs: A collection of paths to the directory containing country-level IEA energy balance CSV files.
    - countries: list - List of country codes to process, given in ISO3 codes.
    - output_file: str - Path to save the processed one CSV file.

    """

    # Hard-coded list of sectors and carriers
    list_sectors = [
        "TOTIND",
        "TOTTRANS",
        "RESIDENT",
        "COMMPUB",
        "AGRICULT",
        "FISHING",
        "ONONSPEC",
        "NONENUSE",
    ]

    # Iterate over countries
    for country, file_path in zip(countries, inputs):
        df = pd.read_csv(file_path)
        # Step 1. Get electricity consumption in each sector
        df_electricity = df[
            (df["flow"].isin(list_sectors)) & (df["product"] == "ELECTR")
        ].pivot(index="short", columns="flow", values="value")
        # Step 2. Get TFC in each sector
        df_TFC = df[(df["flow"].isin(list_sectors)) & (df["product"] == "TOTAL")].pivot(
            index="short", columns="flow", values="value"
        )
        # Step 3. Divide electricity consumption by TFC to get electrification rate by sector
        df_sector_electrification = df_electricity / df_TFC
        df_sector_electrification["ISO3"] = country

        # Append the current country to the total countries dataframe
        if country == countries[0]:
            df_all = df_sector_electrification
        else:
            df_all = pd.concat([df_all, df_sector_electrification], ignore_index=True)

    # Do some cleaning
    # Move the country code to the front of the dataframe
    df_all = df_all[["ISO3"] + [c for c in df_all.columns if c != "ISO3"]]
    df_all = df_all.fillna(0).round(4)

    # Create the folder to keep the processed csv
    output_dir = output_file.split("IEA")[0]
    os.makedirs(output_dir, exist_ok=True)
    df_all.to_csv(output_file, index=False)


if __name__ == "__main__":
    process_countries_electrification_bySector(
        inputs=list(snakemake.input),
        countries=snakemake.params.countries,
        output_file=snakemake.output.output_file,
    )
