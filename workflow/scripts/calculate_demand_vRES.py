import pandas as pd
import os


def calculate_vRES_demand(
    output_dir: str,
    output_file: str,
    TFC_per_capita: str,
    sector_TFC_share: str,
    sector_electrification: str,
    sector_elec_decarb: str,
    population: str,
    elec_loss_rate: str,
    other_renewables: str,
):
    """
    Calculate the electricity demand of a country that needs to be met by
    variable renewable energy sources. Given the top-down approach. If needed,
    processed IEA data can be used for reference.

    Assumption: no import/export between countries. Each country only meet their
    own demand.

    Unit: TJ/year

    Parameters:
    - output_dir: str - Path of the directory to save the target file.
    - output_file: str - Path to save the processed one CSV file.
    - TFC_per_capita: str - Path to the target per capita total final consumption for each country.
    - sector_TFC_share: str - Target share of total final consumption for each sector in
        each country.
    - sector_electrification: str - Target electrification rate for each sector in each
        country.
    - sector_elec_decarb: str - Target decarbonisation level of the electrified part in
        each sector in each country.
    - population: str - Path the the population file used in the calculation.
    - elec_loss_rate: str - Path to the file recording the share of
        transmission & distribution losses as share of the total electricity production plus
        net import.
    - other_renewables: str - Yearly aggregated production of other renewables such as hydropower and nuclear
        technologies. Assumed that the production doesn't change compared to the reference year.
    """

    # Initialise final output df by reading one input file
    df_sector_TFC_share = pd.read_csv(sector_TFC_share, index_col=0)

    # Get target TFC per capita for each country
    TFC_df = pd.read_csv(TFC_per_capita, index_col=0)
    # Get sector-specific TFC with sectoral share
    df_sector_TFC = df_sector_TFC_share.mul(TFC_df["TFC_per_capita"], axis=0)
    # Calculate the electrified parts
    elec_rate = pd.read_csv(sector_electrification, index_col=0)
    df_elec = df_sector_TFC * elec_rate
    # Get electricity transmission & distribution losses (ignore the energy industry own use)
    df_loss_rate = pd.read_csv(elec_loss_rate, index_col=0)
    # Scale to actual production needed to meet this demand
    breakpoint()
    df_elec_prod = df_elec.div(1 - df_loss_rate["ELEC_LOSS_RATE"], axis=0)
    # Get the decarbonised part
    elec_decarb = pd.read_csv(sector_elec_decarb, index_col=0)
    df_elec_decarb = df_elec_prod * elec_decarb
    # Get population
    population = pd.read_csv(population, index_col=0)
    population = population.loc[population.index.intersection(df_elec_prod.index)]
    # Scale from per capita value to national value
    df_elec_decarb_tot = (
        df_elec_decarb.mul(population[population.columns[0]], axis=0) * 1e-3
    )  # switch from GJ to TJ
    # Sum up across all sectors
    df_elec_decarb_sum = df_elec_decarb_tot.sum(axis=1).to_frame(name="total")
    # Get production of other renewables, such as hydro and nuclear, biomass, waste
    df_other_renewables = pd.read_csv(other_renewables, index_col=0)
    # Total vRES production needed is total decarbonised production minus other renewables production
    df_vres_demand = (
        df_elec_decarb_sum["total"]
        - df_other_renewables[df_other_renewables.columns[0]]
    ).clip(lower=0)
    df_vres_demand = df_vres_demand.to_frame(name="VRES_DEMAND")
    df_vres_demand["UNIT"] = "TJ/year"

    # Create the output directory if not existing
    os.makedirs(output_dir, exist_ok=True)
    # Export the final df
    df_vres_demand.to_csv(output_file)


if __name__ == "__main__":
    calculate_vRES_demand(
        output_dir=snakemake.params.output_dir,
        output_file=snakemake.output.output_file,
        TFC_per_capita=snakemake.input.TFC_per_capita,
        sector_TFC_share=snakemake.input.sector_TFC_share,
        sector_electrification=snakemake.input.sector_electrification,
        sector_elec_decarb=snakemake.input.sector_elec_decarb,
        population=snakemake.input.population,
        elec_loss_rate=snakemake.input.elec_loss_rate,
        other_renewables=snakemake.input.other_renewables,
    )
