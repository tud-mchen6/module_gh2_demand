import pandas as pd


def get_target_TFC_per_capita(
    use_historical_per_capita_TFC: bool,
    historical_per_capita_TFC: str,
    tot_per_capita_TFC: float,
    country_overwrite: str,
    output_file: str,
):
    """
    Get the target TFC per capita for each country. If needed, processed IEA data can be used for reference.

    Parameters:
    - use_historical_per_capita_TFC: bool - Whether to use historical values of per capita total final consumption for each country.
    - historical_per_capita_TFC: str - Path to the historical values of per capita TFC in case needed.
    - tot_per_capita_TFC: float - User-given universal default per capita total final energy consumption for all countries. Given in config. Unit: GJ/year/capita.
    - country_overwrite: str - User-given overwrites of country-specific data, specifically TFC per capita for this script.
    - output_file: str - Path to save the processed one CSV file.
    """

    historical_TFC_df = pd.read_csv(historical_per_capita_TFC, index_col=0)
    breakpoint()
    if use_historical_per_capita_TFC:
        TFC_df = historical_TFC_df
    else:
        TFC_df = pd.DataFrame(
            {"TFC_per_capita": tot_per_capita_TFC}, index=historical_TFC_df.index
        )
        # Check if any country-specific input is defined by user
        if country_overwrite is not None:
            overwrite_TFC_df = pd.read_csv(country_overwrite, index_col=0)[
                ["TFC_per_capita"]
            ]
            overwrite_countries = list(overwrite_TFC_df.index)
            for country in overwrite_countries:
                if overwrite_TFC_df.at[country, "TFC_per_capita"] > 0:
                    TFC_df.at[country, "TFC_per_capita"] = overwrite_TFC_df.at[
                        country, "TFC_per_capita"
                    ]

    TFC_df = TFC_df.sort_index().round(4)
    TFC_df.to_csv(output_file)


if __name__ == "__main__":
    get_target_TFC_per_capita(
        use_historical_per_capita_TFC=snakemake.params.use_historical,
        historical_per_capita_TFC=snakemake.input.reference_per_capita_TFC,
        tot_per_capita_TFC=snakemake.params.tot_per_capita_TFC,
        country_overwrite=snakemake.params.country_overwrite,
        output_file=snakemake.output.output_file,
    )
