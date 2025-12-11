import pandas as pd
import os

# test

def calculate_GH2_demand(output_dir : str, output_file : str, 
                         use_historical_per_capita_TFC : bool,
                         historical_per_capita_TFC : str,
                          sector_TFC_share: str, sector_electrification : str, 
                          sector_non_elec_decarb : str, population: str,
                          tot_per_capita_TFC: float,
                          country_overwrite: str = None,
                          ):
    
    """
    Calculate the electricity demand of a country that needs to be met by the 
    production of variable renewable energy sources. Given the top-down approach.
    If needed, processed IEA data can be used for reference.

    Unit: TJ/year

    Parameters:
    - output_dir: str - Path of the directory to save the target file.
    - output_file: str - Path to save the processed one CSV file.
    - use_historical_per_capita_TFC: bool - Whether to use historical values of per 
        capita total final consumption for each country.
    - historical_per_capita_TFC: str - Path to the historical values of per capita TFC
        in case needed.
    - sector_TFC_share: str - Target share of total final consumption for each sector in
        each country.
    - sector_electrification: str - Target electrification rate for each sector in each
        country.
    - sector_non_elec_decarb: str - Target decarbonisation level of the non-electrified part in 
        each sector in each country.
    - population: str - Path the the population file used in the calculation.
    - tot_per_capita_TFC: float - User-given universal default per capita total final energy
        consumption for all countries. Given in config. Unit: GJ/year/capita.
    - country_overwrite: str - User-given overwrites of country-specific data, specifically
        TFC per capita for this script.
    """

    # Rreading one input file in total final consumption shared by each sector
    df_sector_TFC_share = pd.read_csv(sector_TFC_share, index_col=0)

    # Construct a dataframe to put all TFC per capita of all countries
    frame = pd.read_csv(sector_TFC_share, index_col=0)
    # See if TFC per capita follows historical values
    if use_historical_per_capita_TFC:
        TFC_df = pd.read_csv(historical_per_capita_TFC, index_col=0)
    else:
        TFC_df = pd.DataFrame({'TFC_per_capita':tot_per_capita_TFC}, index=frame.index)
        # Check if any country-specific input is defined by user
        if country_overwrite is not None:
            overwrite_TFC_df = pd.read_csv(country_overwrite, index_col=0)[['TFC_per_capita']]
            overwrite_countries = list(overwrite_TFC_df.index)
            for country in overwrite_countries:
                if overwrite_TFC_df.at[country, 'TFC_per_capita'] > 0:
                    TFC_df.at[country, 'TFC_per_capita'] = overwrite_TFC_df.at[country, 'TFC_per_capita']
    # Get the sectoral TFC from the share
    df_sector_TFC = df_sector_TFC_share.mul(TFC_df['TFC_per_capita'], axis=0)
    # Calculate the electrified parts
    elec_rate = pd.read_csv(sector_electrification, index_col=0)
    df_non_elec = df_sector_TFC * (1 - elec_rate)
    # For the not electrified part, calculate the decarbonisation level
    non_elec_decarb = pd.read_csv(sector_non_elec_decarb, index_col=0)
    df_decarb_non_elec = df_non_elec * non_elec_decarb
    # Get population
    population = pd.read_csv(population, index_col=0)
    population = population.loc[population.index.intersection(df_decarb_non_elec.index)]
    df_decarb_non_elec_tot = df_decarb_non_elec.sum(axis=1) * population[population.columns[0]] * 1e-3 # switch from GJ to TJ
    df_GH2_demand = df_decarb_non_elec_tot.to_frame(name='GH2_DEMAND')
    df_GH2_demand['UNIT'] = 'TJ/year'


    # Create the output directory if not existing
    os.makedirs(output_dir, exist_ok=True)
    # Export the final df
    df_GH2_demand.to_csv(output_file)




if __name__ == "__main__":
    calculate_GH2_demand(
        output_dir=snakemake.params.output_dir,
        output_file=snakemake.output.output_file,
        use_historical_per_capita_TFC=snakemake.params.use_historical_per_capita_TFC,
        historical_per_capita_TFC=snakemake.input.historical_per_capita_TFC,
        sector_TFC_share=snakemake.input.sector_TFC_share,
        sector_electrification=snakemake.input.sector_electrification,
        sector_non_elec_decarb=snakemake.input.sector_non_elec_decarb,
        population=snakemake.input.population,
        tot_per_capita_TFC=snakemake.params.tot_per_capita_TFC,
        country_overwrite=snakemake.params.country_overwrite,
    )
