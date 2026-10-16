import pandas as pd
import os
from pathlib import Path


def get_countries_non_elec_renew_consum(
    input_dir: str, heat_decarb: str, countries, output_file: str, year: int
):
    """
    Processes IEA energy balance CSV files for specified countries to extract non-electricity renewable energy
    consumption.

    Parameters:
    - input_dir: Directory to extract all the downloaded files.
    - heat_decarb: Path to the heat decarbonization rate file.
    - countries: list - List of country codes to process, given in ISO3 codes.
    - output_file: str - Path to save the processed one CSV file.
    - year: int - The year to get production data from.

    Unit: TJ

    """

    # Hard-coded list of sectors and carriers
    product_list = ["COMRENEW", "GEOTHERM"]

    # Initialise the dataframe (as dict)
    dict_all = {"ISO3": [], "NON_ELEC_RENEW_CONSUM": []}

    # Iterate over countries
    input_path = Path(input_dir)
    files = [str(file) for file in input_path.iterdir() if file.is_file()]
    i = 0  # flag for initialise
    for file in files:
        if (str(year) in file) & (file.split("_")[-2] in countries):
            country = file.split("_")[-2]
            df = pd.read_csv(file)
            df_select = df[
                (df["year"] == year)
                & (df["product"].isin(product_list))
                & (df["flow"] == "TFC")
            ]
            heat_decarb_df = pd.read_csv(heat_decarb, index_col=0)
            if ("HEAT" in df["product"].unique()) & (
                heat_decarb_df.at[country, "HEAT_DECARB"] > 0
            ):
                value = (
                    df_select["value"].sum()
                    + heat_decarb_df.at[country, "HEAT_DECARB"]
                    * df[(df["flow"] == "TFC") & (df["product"] == "HEAT")][
                        "value"
                    ].values[0]
                )
            else:
                value = df_select["value"].sum()
            dict_all["ISO3"].append(country)
            dict_all["NON_ELEC_RENEW_CONSUM"].append(value)

    # Convert to dataframe
    df_all = pd.DataFrame(dict_all)

    # Do some cleaning
    df_all = df_all.round(4)

    # Create the folder to keep the processed csv
    output_dir = output_file.split("IEA")[0]
    os.makedirs(output_dir, exist_ok=True)
    df_all.to_csv(output_file, index=False)


if __name__ == "__main__":
    get_countries_non_elec_renew_consum(
        input_dir=snakemake.input.input_dir,
        heat_decarb=snakemake.input.heat_decarb,
        countries=snakemake.params.countries,
        output_file=snakemake.output.output_file,
        year=snakemake.params.year,
    )
