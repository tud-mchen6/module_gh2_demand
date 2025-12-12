import pandas as pd
import glob
import os


def get_target_sector_TFC_share(
        countries : list, 
        use_historical : bool,
        sector_overwrite_dir : str,
        reference_sector_TFC_share : str,
        output_file : str,
        use_historical_per_capita_TFC: bool,
        tot_per_capita_TFC: float,
        country_overwrite: str = None,
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
    - reference_sector_TFC_share: str - Path to the sectoral share of the
        reference year.
    - output_file: str - Path to save the output file.
    - use_historical_per_capita_TFC: bool - Whether to use historical values of per 
        capita total final consumption for each country.
    - country_overwrite: str - User-given overwrites of country-specific data.
    """

    # Get the historical reference values
    reference_df = pd.read_csv(reference_sector_TFC_share, index_col=0)
    target_df = reference_df.copy()

    if not use_historical:
        # Get all the files in the user folder (no template)
        all_files = glob.glob(os.path.join(sector_overwrite_dir,"*.csv"))
        for file in all_files:
            # Only get the ones with the naming convention; hard-coded
            file_name = file.replace(sector_overwrite_dir, "").replace(".csv","").replace("\\","")
            if 'sectorShare' in file_name:
                country = file_name.split("_")[-1]
                # Only get the ones where country is within the countries list
                if country in countries:
                    country_overwrite = pd.read_csv(file,index_col=0)
                    # Check if the value that the user gives is coherent. If not,
                    # use the reference values instead
                    if 'sector_share' in country_overwrite:
                        if country_overwrite['sector_share'].sum() == 1:
                            target_df = target_df.drop(index=country)
                            target_df = pd.concat([target_df, country_overwrite['sector_share'].to_frame().
                                            rename(columns={'sector_share':country}).T])
                        else:
                            print("Input error: sector share not adding up to 1.")
                    else:
                        print("Input error: sector share not defined in user inputs.")
                elif country=="template":
                    continue
                else:
                    print("Input error: given country not present in analysed countries.")
    target_df = target_df.sort_index().round(4)

    # If TFC per person exceeds a certain threshold, cap the share of residential + tertiary
    if not use_historical_per_capita_TFC:
        TFC_df = pd.DataFrame({'TFC_per_capita':tot_per_capita_TFC}, index=target_df.index)
        # Check if any country-specific input is defined by user
        if country_overwrite is not None:
            overwrite_TFC_df = pd.read_csv(country_overwrite, index_col=0)[['TFC_per_capita']]
            overwrite_countries = list(overwrite_TFC_df.index)
            for country in overwrite_countries:
                if overwrite_TFC_df.at[country, 'TFC_per_capita'] > 0:
                    TFC_df.at[country, 'TFC_per_capita'] = overwrite_TFC_df.at[country, 'TFC_per_capita']
        for country in TFC_df.index:
            # Assume the threshold for adjusting sectoral share is 70 GJ/year/capita; could be changed to a config parameter if needed
            if TFC_df.at[country, 'TFC_per_capita'] > 70:
                res_ter_share = target_df.at[country, 'RESIDENT'] + target_df.at[country, 'COMMPUB']
                if res_ter_share > 0.4:
                    scaling_factor = 0.4 / res_ter_share
                    target_df.at[country, 'RESIDENT'] *= scaling_factor
                    target_df.at[country, 'COMMPUB'] *= scaling_factor
                    # Re-normalise the other sectors
                    other_sectors = target_df.columns.difference(['RESIDENT', 'COMMPUB'])
                    other_sum = target_df.loc[country, other_sectors].sum()
                    for sector in other_sectors:
                        target_df.at[country, sector] = target_df.at[country, sector] / other_sum * (1 - 0.4)
        


    # Output the file
    target_df = target_df.round(4)
    target_df.to_csv(output_file)


if __name__ == "__main__":
    get_target_sector_TFC_share(
        countries=snakemake.params.countries,
        use_historical=snakemake.params.use_historical,
        sector_overwrite_dir=snakemake.params.sector_overwrite_dir,
        reference_sector_TFC_share=snakemake.input.reference_sector_TFC_share,
        output_file=snakemake.output.output_file,
        use_historical_per_capita_TFC=snakemake.params.use_historical_per_capita_TFC,
        tot_per_capita_TFC=snakemake.params.tot_per_capita_TFC,
        country_overwrite=snakemake.params.country_overwrite,
    )