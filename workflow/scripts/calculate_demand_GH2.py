import pandas as pd
import os


def calculate_GH2_demand(
    output_dir: str,
    output_file: str,
    TFC_per_capita: str,
    sector_TFC_share: str,
    sector_electrification: str,
    sector_non_elec_decarb: str,
    population: str,
    hist_non_elec_renew_consum: str,
):
    """
    Calculate the electricity demand of a country that needs to be met by the
    production of variable renewable energy sources. Given the top-down approach.
    If needed, processed IEA data can be used for reference.

    Unit: TJ/year

    Parameters:
    - output_dir: str - Path of the directory to save the target file.
    - output_file: str - Path to save the processed one CSV file.
    - TFC_per_capita: str - Path to the target per capita total final consumption for each country.
    - sector_TFC_share: str - Target share of total final consumption for each sector in
        each country.
    - sector_electrification: str - Target electrification rate for each sector in each
        country.
    - sector_non_elec_decarb: str - Target decarbonisation level of the non-electrified part in
        each sector in each country.
    - population: str - Path the the population file used in the calculation.
    - hist_non_elec_renew_consum: str - Path to the historical non-electricity renewable
        energy consumption data.
    - country_overwrite: str - User-given overwrites of country-specific data, specifically
        TFC per capita for this script.
    """

    # Rreading one input file in total final consumption shared by each sector
    df_sector_TFC_share = pd.read_csv(sector_TFC_share, index_col=0)

    # Get target TFC per capita for each country
    TFC_df = pd.read_csv(TFC_per_capita, index_col=0)
    # Get the sectoral TFC from the share
    df_sector_TFC = df_sector_TFC_share.mul(TFC_df["TFC_per_capita"], axis=0)
    # Calculate the electrified parts
    elec_rate = pd.read_csv(sector_electrification, index_col=0)
    df_non_elec = df_sector_TFC * (1 - elec_rate)
    # For the not electrified part, calculate the decarbonisation level
    non_elec_decarb = pd.read_csv(sector_non_elec_decarb, index_col=0)
    df_decarb_non_elec = df_non_elec * non_elec_decarb
    # Get population
    population = pd.read_csv(population, index_col=0)
    population = population.loc[population.index.intersection(df_decarb_non_elec.index)]
    df_decarb_non_elec_tot = (
        df_decarb_non_elec.sum(axis=1) * population[population.columns[0]] * 1e-3
    )  # switch from GJ to TJ
    # Subtract historical bio-waste consumption on TFC level
    hist_non_elec_renew_consum_df = pd.read_csv(hist_non_elec_renew_consum, index_col=0)
    df_decarb_non_elec_tot = df_decarb_non_elec_tot.sub(
        hist_non_elec_renew_consum_df["NON_ELEC_RENEW_CONSUM"], fill_value=0
    )
    # In case existing bio-waste consumption is higher than the calculated non-elec decarb demand, no need for further demand
    df_decarb_non_elec_tot[df_decarb_non_elec_tot < 0] = 0
    df_GH2_demand = df_decarb_non_elec_tot.to_frame(name="GH2_DEMAND")
    df_GH2_demand["UNIT"] = "TJ/year"
    # Create the output directory if not existing
    os.makedirs(output_dir, exist_ok=True)
    # Export the final df
    df_GH2_demand = df_GH2_demand.round(4)
    df_GH2_demand.to_csv(output_file)


if __name__ == "__main__":
    calculate_GH2_demand(
        output_dir=snakemake.params.output_dir,
        output_file=snakemake.output.output_file,
        TFC_per_capita=snakemake.input.TFC_per_capita,
        sector_TFC_share=snakemake.input.sector_TFC_share,
        sector_electrification=snakemake.input.sector_electrification,
        sector_non_elec_decarb=snakemake.input.sector_non_elec_decarb,
        population=snakemake.input.population,
        hist_non_elec_renew_consum=snakemake.input.hist_non_elec_renew_consum,
    )
