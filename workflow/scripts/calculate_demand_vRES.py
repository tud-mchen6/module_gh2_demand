import pandas as pd
import os


def calculate_vRES_demand(
    output_dir: str,
    output_file: str,
    use_historical_per_capita_TFC: bool,
    historical_per_capita_TFC: str,
    sector_TFC_share: str,
    sector_electrification: str,
    sector_elec_decarb: str,
    population: str,
    elec_loss_rate: str,
    other_renewables: str,
    tot_per_capita_TFC: float,
    country_overwrite: str = None,
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
    - use_historical_per_capita_TFC: bool - Whether to use historical values of per
        capita total final consumption for each country.
    - historical_per_capita_TFC: str - Path to the historical values of per capita TFC
        in case needed.
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
    - tot_per_capita_TFC: float - User-given universal default per capita total final energy
        consumption for all countries. Given in config. Unit: GJ/year/capita.
    - country_overwrite: str - User-given overwrites of country-specific data, specifically
        TFC per capita for this script.
    """

    # Initialise final output df by reading one input file
    df_sector_TFC_share = pd.read_csv(sector_TFC_share, index_col=0)

    # Construct a dataframe to put all TFC per capita of all countries
    frame = pd.read_csv(sector_TFC_share, index_col=0)
    # See if TFC per capita follows historical values
    if use_historical_per_capita_TFC:
        TFC_df = pd.read_csv(historical_per_capita_TFC, index_col=0)
    else:
        TFC_df = pd.DataFrame({"TFC_per_capita": tot_per_capita_TFC}, index=frame.index)
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
    # Get sector-specific TFC with sectoral share
    df_sector_TFC = df_sector_TFC_share.mul(TFC_df["TFC_per_capita"], axis=0)
    # Calculate the electrified parts
    elec_rate = pd.read_csv(sector_electrification, index_col=0)
    df_elec = df_sector_TFC * elec_rate
    # Get electricity transmission & distribution losses (ignore the energy industry own use)
    df_loss_rate = pd.read_csv(elec_loss_rate, index_col=0)
    # Scale to actual production needed to meet this demand
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
        use_historical_per_capita_TFC=snakemake.params.use_historical_per_capita_TFC,
        historical_per_capita_TFC=snakemake.input.historical_per_capita_TFC,
        sector_TFC_share=snakemake.input.sector_TFC_share,
        sector_electrification=snakemake.input.sector_electrification,
        sector_elec_decarb=snakemake.input.sector_elec_decarb,
        population=snakemake.input.population,
        elec_loss_rate=snakemake.input.elec_loss_rate,
        other_renewables=snakemake.input.other_renewables,
        tot_per_capita_TFC=snakemake.params.tot_per_capita_TFC,
        country_overwrite=snakemake.params.country_overwrite,
    )
