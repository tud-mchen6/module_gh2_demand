import pandas as pd
import os


def get_target_TFC_per_capita(
    reference_per_capita_TFC: str,
    config: dict,
    country_overwrite: str,
    output_file: str,
):
    """
    Get the target TFC per capita for each country. If needed, processed IEA data can be used for reference.

    Parameters:
    - reference_per_capita_TFC: str - Path to the historical values of per capita TFC in case needed.
    - config: dict - User-given configurations.
    - country_overwrite: str - User-given overwrites of country-specific data, specifically TFC per capita for this script.
    - output_file: str - Path to save the processed one CSV file.
    """

    use_historical_per_capita_TFC = config["historical_per_capita_TFC"]
    tot_per_capita_TFC = config["tot_per_capita_TFC"]
    historical_TFC_df = pd.read_csv(reference_per_capita_TFC, index_col=0)
    if use_historical_per_capita_TFC:
        TFC_df = historical_TFC_df
    else:
        TFC_df = pd.DataFrame(
            {"TFC_per_capita": tot_per_capita_TFC}, index=historical_TFC_df.index
        )
        # Check if any country-specific input is defined by user
        overwrite_TFC_df = pd.read_csv(country_overwrite, index_col=0)[
            ["TFC_per_capita"]
        ]
        # If the overwrite csv does have value
        if (overwrite_TFC_df.sum() > 0).values[0]:
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
        reference_per_capita_TFC=snakemake.input.reference_per_capita_TFC,
        config=snakemake.params.config,
        country_overwrite=snakemake.input.country_overwrite,
        output_file=snakemake.output.output_file,
    )
