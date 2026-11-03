import pandas as pd
import glob
import os


def scale_or_initialise(entry, relative, init):
    if entry > 0:
        return min(relative + entry, 1)
    else:
        return init


def get_target_elec_rate(
    countries: list,
    config: dict,
    sector_overwrite_dir: str,
    reference_sector_elec_rate: str,
    output_file: str,
):
    """
    Get the target sectoral electrification rate for each country,
    accounting for all overwrites, prepared for the final calculation.
    The default is to use the referenced historical valuefor each country, unless
    explicitly specified by the user.

    Parameters:
    - countries: list - List of country codes to process, given in ISO3 codes.
    - config: dict - User-given configurations of the module.
    - sector_overwrite_dir: str - Path of the directory to store any user-given
        overwrite files.
    - reference_sector_elec_rate: str - Path to the sectoral electrification rate of the
        reference year.
    - output_file: str - Path to save the output file.
    """

    # Get the parameters within config
    use_historical = config["historical_elec_rate"]
    sector_elec_rate_rel = config["sector_elec_rate_rel"]
    elec_rate_in_case_zero = config["elec_rate_in_case_zero"]

    # Get the historical reference values
    reference_df = pd.read_csv(reference_sector_elec_rate, index_col=0)
    if not use_historical:
        # If not use the historical values, go for the config-defined defaults
        target_df = reference_df.copy().map(
            lambda x: scale_or_initialise(
                x, sector_elec_rate_rel, elec_rate_in_case_zero
            )
        )

        # Get all country specific overwrites (low priority, higher than config default)
        if "overrides" in config and config["overrides"] is not None:
            for country, country_config in config["overrides"].items():
                if "sector_elec_rate_rel" in country_config:
                    sector_elec_rate_rel = country_config.get(
                        "sector_elec_rate_rel", None
                    )
                if "elec_rate_in_case_zero" in country_config:
                    elec_rate_in_case_zero = country_config.get(
                        "elec_rate_in_case_zero", None
                    )
                target_df.loc[country] = reference_df.loc[country].apply(
                    lambda x: scale_or_initialise(
                        x, sector_elec_rate_rel, elec_rate_in_case_zero
                    )
                )

        # Get all sector specific overwrites (highest priority)
        all_files = glob.glob(os.path.join(sector_overwrite_dir, "*.csv"))
        for file in all_files:
            # Only get the ones with the naming convention; hard-coded
            file_name = (
                file.replace(sector_overwrite_dir, "")
                .replace(".csv", "")
                .replace("\\", "")
            )
            if "sectorShare" in file_name:
                country = file_name.split("_")[-1]
                # Only get the ones where country is within the countries list
                if country in countries:
                    country_sector_specific_overwrite = pd.read_csv(file, index_col=0)
                    # Check if the value that the user gives is coherent. If not,
                    # fall back to the default
                    for sector in list(country_sector_specific_overwrite.index):
                        abs = country_sector_specific_overwrite.loc[
                            sector, "sector_elec_rate_abs"
                        ]
                        rel = country_sector_specific_overwrite.loc[
                            sector, "sector_elec_rate_rel"
                        ]
                        if pd.notna(abs) and pd.notna(rel):
                            print(
                                "Input error: relative values and absolute values cannot be given at the same time for "
                                "electrification rate."
                            )
                        elif pd.notna(abs):
                            target_df.at[country, sector] = abs
                            if reference_df.at[country, sector] > abs:
                                print(
                                    "Input warning: given electrification lower than historical value"
                                    f" in {sector} sector in {country}."
                                )
                        elif pd.notna(rel):
                            target_df.at[country, sector] = scale_or_initialise(
                                reference_df.at[country, sector],
                                rel,
                                elec_rate_in_case_zero,
                            )
                        else:
                            continue
                elif country == "template":
                    continue
                else:
                    print(
                        "Input error: given country not present in analysed countries."
                    )
        target_df = target_df.sort_index().round(4)
    else:
        target_df = reference_df

    # Clean the output file; non-energy use of other carriers cannot be electrified
    target_df["NONENUSE"] = 0

    # Output the file
    target_df.to_csv(output_file)


if __name__ == "__main__":
    get_target_elec_rate(
        countries=snakemake.params.countries,
        config=snakemake.params.config,
        sector_overwrite_dir=snakemake.params.sector_overwrite_dir,
        reference_sector_elec_rate=snakemake.input.reference_sector_elec_rate,
        output_file=snakemake.output.output_file,
    )
