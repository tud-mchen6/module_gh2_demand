import pandas as pd
import os


def get_population(
    population_file: str, population_ref_year: int, population_output: str
):
    """
    Given population reference year, get the clean by-country population file for final calculation.

    Parameters:
    - population_file: str - Path to the file that is extracted from the data source.
    - population_ref_year: int - The year in the population trajectory to locate to,
        as the reference year for the demand calculation.
    - population_output: str - Path to store the output file for this function.

    Unit: originally thousand people, converted to people here.
    """

    # Hard-code the needed columns
    df_all = pd.read_csv(population_file)[["ISO3_code", "Time", "PopTotal"]]
    df_all = df_all.rename(columns={"ISO3_code": "ISO3"})
    df_all = (
        df_all.pivot(columns="Time", index="ISO3", values="PopTotal") * 1e3
    )  # switch unit
    # Check the data type of the columns in terms of years
    col_dtype = df_all.columns.dtype
    population_ref_year = col_dtype.type(population_ref_year)

    output_dir = population_output.split("population")[0]
    os.makedirs(output_dir, exist_ok=True)
    df_all[[population_ref_year]].round(0).rename(
        columns={population_ref_year: "population"}
    ).to_csv(population_output)


if __name__ == "__main__":
    get_population(
        population_file=snakemake.input.population_file,
        population_ref_year=snakemake.params.population_ref_year,
        population_output=snakemake.output.population_output,
    )
