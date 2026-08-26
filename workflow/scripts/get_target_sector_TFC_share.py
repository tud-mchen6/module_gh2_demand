import pandas as pd
import glob
import os


def get_target_sector_TFC_share(
    countries: list,
    use_historical: bool,
    sector_overwrite_dir: str,
    historical_per_capita_TFC: str,
    reference_sector_TFC_share: str,
    output_file: str,
    TFC_per_capita: str,
    country_overwrite: str,
):
    """
    Get the target sectoral share in total final consumption for each country,
    accounting for all overwrites.
    The default is to use the referenced historical valuefor each country, unless
    explicitly specified by the user.

    Parameters:
    - countries: list - List of country codes to process, given in ISO3 codes.
    - use_historical: bool - Whether to directly use historical values in the
        reference year.
    - sector_overwrite_dir: str - Path of the directory to store any user-given
        overwrite files.
    - historical_per_capita_TFC: str - Path to the historical values of per capita TFC.
    - reference_sector_TFC_share: str - Path to the sectoral share of the
        reference year.
    - output_file: str - Path to save the output file.
    - TFC_per_capita: str - Path to the target per capita total final consumption data.
    - country_overwrite: str - User-given overwrites of country-specific data.
    """

    # Get the historical reference values
    reference_df = pd.read_csv(reference_sector_TFC_share, index_col=0)
    target_df = reference_df.copy()

    if not use_historical:
        # Get all the files in the user folder (no template)
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
                    country_overwrite = pd.read_csv(file, index_col=0)
                    # Check if the value that the user gives is coherent. If not,
                    # use the reference values instead
                    if "sector_share" in country_overwrite:
                        if country_overwrite["sector_share"].sum() == 1:
                            target_df = target_df.drop(index=country)
                            target_df = pd.concat(
                                [
                                    target_df,
                                    country_overwrite["sector_share"]
                                    .to_frame()
                                    .rename(columns={"sector_share": country})
                                    .T,
                                ]
                            )
                        else:
                            print("Input error: sector share not adding up to 1.")
                    else:
                        print("Input error: sector share not defined in user inputs.")
                elif country == "template":
                    continue
                else:
                    print(
                        "Input error: given country not present in analysed countries."
                    )
    target_df = target_df.sort_index().round(4)

    # Cap the residential and commercial/public TFC based on current day highest level of the world
    # But also for countries whose TFC is scaling down, set a minimum level of TFC for residential and commercial/public
    # Get the current TFC per capita for countries
    TFC_df = pd.read_csv(TFC_per_capita, index_col=0)
    TFC_per_sector = target_df.mul(TFC_df["TFC_per_capita"], axis=0)
    historical_TFC = pd.read_csv(historical_per_capita_TFC, index_col=0)
    hist_TFC_per_sector = reference_df.mul(historical_TFC["TFC_per_capita"], axis=0)
    # assume 0.9 quantile cutoff to avoid outliers. 0.9 quantile should be sufficient for decent living
    remaining_sectors_limited = ["TOTTRANS", "AGRICULT", "FISHING"]
    remaining_sectors_unlimited = ["TOTIND", "NONENUSE", "ONONSPEC"]
    dict_max_TFC = {}
    dict_min_TFC = {}
    for sector in [remaining_sectors_limited, "RESIDENT", "COMMPUB"]:
        if isinstance(sector, list):
            for s in sector:
                dict_max_TFC[s] = hist_TFC_per_sector[s].quantile(0.9)
        else:
            dict_max_TFC[sector] = hist_TFC_per_sector[sector].quantile(0.9)
            dict_min_TFC[sector] = hist_TFC_per_sector[sector].quantile(0.5)
    for country in TFC_df.index:
        excess = 0
        deficit = 0
        if TFC_per_sector.at[country, "RESIDENT"] > dict_max_TFC["RESIDENT"]:
            excess += TFC_per_sector.at[country, "RESIDENT"] - dict_max_TFC["RESIDENT"]
            TFC_per_sector.at[country, "RESIDENT"] = dict_max_TFC["RESIDENT"]
        if TFC_per_sector.at[country, "RESIDENT"] < dict_min_TFC["RESIDENT"]:
            deficit += dict_min_TFC["RESIDENT"] - TFC_per_sector.at[country, "RESIDENT"]
            TFC_per_sector.at[country, "RESIDENT"] = dict_min_TFC["RESIDENT"]
        if TFC_per_sector.at[country, "COMMPUB"] > dict_max_TFC["COMMPUB"]:
            excess += TFC_per_sector.at[country, "COMMPUB"] - dict_max_TFC["COMMPUB"]
            TFC_per_sector.at[country, "COMMPUB"] = dict_max_TFC["COMMPUB"]
        else:
            remaining_sectors_limited.append("COMMPUB")
        if TFC_per_sector.at[country, "COMMPUB"] < dict_min_TFC["COMMPUB"]:
            deficit += dict_min_TFC["COMMPUB"] - TFC_per_sector.at[country, "COMMPUB"]
            TFC_per_sector.at[country, "COMMPUB"] = dict_min_TFC["COMMPUB"]
        # Re-distribute the other sectors. Assume industry, non-energy use and non
        # specified can increase withouout limit, but everything else is capped.
        excess_per_sector = excess / len(
            remaining_sectors_limited + remaining_sectors_unlimited
        )
        additional_excess = 0
        for sector in remaining_sectors_limited:
            if (TFC_per_sector.at[country, sector] + excess_per_sector) > dict_max_TFC[
                sector
            ]:
                additional_excess += (
                    TFC_per_sector.at[country, sector] + excess_per_sector
                ) - dict_max_TFC[sector]
                TFC_per_sector.at[country, sector] = dict_max_TFC[sector]
            else:
                TFC_per_sector.at[country, sector] += excess_per_sector
        for sector in remaining_sectors_unlimited:
            TFC_per_sector.at[country, sector] += (
                excess_per_sector + additional_excess / len(remaining_sectors_unlimited)
            )
            TFC_per_sector.at[country, sector] -= deficit / len(
                remaining_sectors_unlimited
            )
    target_df = TFC_per_sector.div(TFC_df["TFC_per_capita"], axis=0)

    # Output the file
    target_df = target_df.round(4)
    target_df.to_csv(output_file)


if __name__ == "__main__":
    get_target_sector_TFC_share(
        countries=snakemake.params.countries,
        use_historical=snakemake.params.use_historical,
        sector_overwrite_dir=snakemake.params.sector_overwrite_dir,
        historical_per_capita_TFC=snakemake.input.reference_per_capita_TFC,
        reference_sector_TFC_share=snakemake.input.reference_sector_TFC_share,
        output_file=snakemake.output.output_file,
        TFC_per_capita=snakemake.input.TFC_per_capita,
        country_overwrite=snakemake.input.country_overwrite,
    )
