import pandas as pd
import glob
import os


def scale_or_initialise(entry, relative, init):
    """
    Scale the entry by a relative factor, unless the entry is zero,
    in which case return the initialisation value.
    """
    if entry > 0:
        return min(relative + entry, 1)
    else:
        return init


def get_target_elec_decarb(
    countries: list,
    use_historical: bool,
    elec_decarb_rel: float,
    elec_decarb_in_case_zero: float,
    sector_overwrite_dir: str,
    reference_sector_elec_decarb: str,
    output_file: str,
    country_specific_overwrite: str = None,
):
    """
    Get the target decarbonisation level for electricity for each country,
    accounting for all overwrites, prepared for the final calculation.
    The default is to use the referenced historical valuefor each country, unless
    explicitly specified by the user.

    Parameters:
    - countries: list - List of country codes to process, given in ISO3 codes.
    - use_historical: bool - Whether to directly use historical values in the
        reference year.
    - elec_decarb_rel: float - Decarbonisation of electricity relative (additional) to historical ones
        in case that hte historical ones are non-zero.
    - elec_decarb_in_case_zero: float - Decarbonisation of electricity assumed for sectors
        where historically the rate is zero.
    - sector_overwrite_dir: str - Path of the directory to store any user-given
        overwrite files.
    - country_specific_overwrite: str - Path of the file that stores country-level overwrites.
    - reference_sector_elec_decarb: str - Path to the sectoral electrification rate of the
        reference year.
    - output_file: str - Path to save the output file.
    """

    # Apply the config default values
    sector = "ELEC_DECARB"
    sectors = [
        "TOTIND",
        "TOTTRANS",
        "RESIDENT",
        "COMMPUB",
        "AGRICULT",
        "FISHING",
        "ONONSPEC",
        "NONENUSE",
    ]
    reference = pd.read_csv(reference_sector_elec_decarb, index_col=0)[[sector]]
    reference_df = pd.DataFrame(columns=sectors, index=reference.index)
    reference_df[:] = reference.values

    if not use_historical:
        target_df = reference_df.copy().map(
            lambda x: scale_or_initialise(x, elec_decarb_rel, elec_decarb_in_case_zero)
        )

        # Get all country specific overwrites (low priority, higher than config default)
        if country_specific_overwrite is not None:
            country_level_overwrite_df = pd.read_csv(
                country_specific_overwrite, index_col=0
            )
            for country in list(country_level_overwrite_df.index):
                # Users could choose to determine directly an absolute decarbonisation level,
                # or to define a relative increase compared to the current value, that is different
                # from that defined in config. But these two cannot exist at the same time.
                abs = country_level_overwrite_df.loc[country, "elec_decarb_abs"]
                rel = country_level_overwrite_df.loc[country, "elec_decarb_rel"]
                if pd.notna(abs) and pd.notna(rel):
                    print(
                        "Input error: relative values and absolute values cannot be given at the same time for "
                        "electricity decarbonisation level."
                    )
                elif pd.notna(abs):
                    target_df.loc[country] = abs
                    if reference_df.at[country, sector] > abs:
                        print(
                            "Input warning: given electricity decarbonisation level lower than historical value"
                            f" in {sector} sector in {country}."
                        )
                elif pd.notna(rel):
                    target_df.loc[country] = reference_df.loc[country].apply(
                        lambda x: scale_or_initialise(x, rel, elec_decarb_in_case_zero)
                    )
                else:
                    continue

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
                            sector, "elec_decarb_abs"
                        ]
                        rel = country_sector_specific_overwrite.loc[
                            sector, "elec_decarb_rel"
                        ]
                        if pd.notna(abs) and pd.notna(rel):
                            print(
                                "Input error: relative values and absolute values cannot be given at the same time for "
                                "electricity decarbonisation level."
                            )
                        elif pd.notna(abs):
                            target_df.at[country, sector] = abs
                            if reference_df.at[country, sector] > abs:
                                print(
                                    "Input warning: given electricity decarbonisation level lower than historical value"
                                    f" in {sector} sector in {country}."
                                )
                        elif pd.notna(rel):
                            target_df.at[country, sector] = scale_or_initialise(
                                reference_df.at[country, sector],
                                rel,
                                elec_decarb_in_case_zero,
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

    # Output the file
    target_df.to_csv(output_file)


if __name__ == "__main__":
    get_target_elec_decarb(
        countries=snakemake.params.countries,
        use_historical=snakemake.params.use_historical,
        elec_decarb_rel=snakemake.params.elec_decarb_rel,
        elec_decarb_in_case_zero=snakemake.params.elec_decarb_in_case_zero,
        sector_overwrite_dir=snakemake.params.sector_overwrite_dir,
        country_specific_overwrite=snakemake.params.country_overwrite,
        reference_sector_elec_decarb=snakemake.input.reference_sector_elec_decarb,
        output_file=snakemake.output.output_file,
    )
