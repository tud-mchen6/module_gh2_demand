import pandas as pd
import os


def get_countries_non_elec_renew_consum(
    inputs: str,
    heat_decarb: str,
    countries,
    output_dir: str,
    output_file: str,
    year: int,
):
    """
    Processes IEA energy balance CSV files for specified countries to extract non-electricity renewable energy
    consumption.

    Parameters:
    - inputs: A collection of paths to the directory containing country-level IEA energy balance CSV files.
    - heat_decarb: Path to the heat decarbonization rate file.
    - countries: list - List of country codes to process, given in ISO3 codes.
    - output_dir: str - Path of the directory to save the target file.
    - output_file: str - Path to save the processed one CSV file.
    - year: int - The year to get production data from.

    Unit: TJ

    """

    # Hard-coded list of sectors and carriers
    product_list = ["COMRENEW", "GEOTHERM"]

    # Initialise the dataframe (as dict)
    dict_all = {"ISO3": [], "NON_ELEC_RENEW_CONSUM": []}

    # Iterate over countries
    for country, file_path in zip(countries, inputs):
        df = pd.read_csv(file_path)
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
                * df[(df["flow"] == "TFC") & (df["product"] == "HEAT")]["value"].values[
                    0
                ]
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
    os.makedirs(output_dir, exist_ok=True)
    df_all.to_csv(output_file, index=False)


if __name__ == "__main__":
    get_countries_non_elec_renew_consum(
        inputs=snakemake.input.inputs,
        heat_decarb=snakemake.input.heat_decarb,
        countries=snakemake.params.countries,
        output_dir=snakemake.params.output_dir,
        output_file=snakemake.output.output_file,
        year=snakemake.params.year,
    )
