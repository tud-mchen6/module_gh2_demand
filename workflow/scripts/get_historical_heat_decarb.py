import pandas as pd
import os


def safe_read_csv(path):
    if os.path.getsize(path) == 0:  # file exists but is empty
        return 0
    try:
        df = pd.read_csv(path)
        return df
    except Exception:
        return 0


def process_countries_heat_decarb(
    inputs: str, countries, output_dir: str, output_file: str, year: int = 2023
):
    """
    Processes IEA electricity and heat balance CSV files for specified countries to calculate decarbonisation
    level of heat produced in each country. When there is no heat data, the decarbonisation level is set to None.

    Assumption: No differentiation is made between different types and qualities of heat.

    Unit of data: TJ

    Parameters:
    - inputs: A collection of paths to the directory containing country-level IEA heat balance CSV files.
    - countries: list - List of country codes to process, given in ISO3 codes.
    - output_file: str - Path to save the processed one CSV file.
    - year: int - The year to process the data for.

    """

    # Hard-coded list of carriers
    list_nonCarb_carriers = [
        "EHBIOMASS",
        "EHWASTE",
        "EHNUCLEAR",
        "EHSOLARTH",
        "EHGEOTHERM",
    ]
    dict_country_heat_decarb = {}

    # Iterate over countries
    for country, file_path in zip(countries, inputs):
        df = safe_read_csv(file_path)
        # If the path is invalid or the csv is empty
        if type(df) is int:
            dict_country_heat_decarb[country] = None
        else:
            # Step 0. Filter out the countries with a csv but no useful data
            years = df["year"].unique()
            if year not in years:
                dict_country_heat_decarb[country] = None
                continue
            else:
                sub_df = df[df["year"] == year]
                if sub_df["value"].isna().any() or sub_df["value"].sum() == 0:
                    dict_country_heat_decarb[country] = None
                    continue
            # Step 1. Get heat production by carrier of the given year
            df_year = df[df["year"] == year]
            if "HEAT" in df_year["product"].unique():
                df_year = df_year[df_year["product"] == "HEAT"]
                # df_year = df_year.pivot(index="short", columns="flow", values="value")
                # Step 2. Calculate the decarbonisation level
                # Sum up heat production from all carriers
                if "EHINDPROD" not in df_year["flow"].unique():
                    dict_country_heat_decarb[country] = None
                    continue
                else:
                    CALC_TOTAL = df_year.loc[df_year["flow"] == "EHINDPROD"][
                        "value"
                    ].values[0]
                    CALC_NONCARB = 0
                    # Sum up heat production from non-carbon carriers
                    for carrier in list_nonCarb_carriers:
                        if carrier in df_year["flow"].unique():
                            CALC_NONCARB += df_year.loc[df_year["flow"] == carrier][
                                "value"
                            ].values[0]
                    HEAT_DECARB = CALC_NONCARB / CALC_TOTAL
            else:
                HEAT_DECARB = None

            # Append the current country to the total countries dictionary
            dict_country_heat_decarb[country] = HEAT_DECARB

    # Do some cleaning
    df_all = (
        pd.Series(dict_country_heat_decarb)
        .to_frame(name="HEAT_DECARB")
        .reset_index()
        .rename(columns={"index": "ISO3"})
    )
    # Keep the None values
    df_all = df_all.round(4)

    # Create the folder to keep the processed csv
    os.makedirs(output_dir, exist_ok=True)
    df_all.to_csv(output_file, index=False)


if __name__ == "__main__":
    process_countries_heat_decarb(
        inputs=list(snakemake.input),
        countries=snakemake.params.countries,
        output_dir=snakemake.params.output_dir,
        output_file=snakemake.output.output_file,
        year=snakemake.params.year,
    )
