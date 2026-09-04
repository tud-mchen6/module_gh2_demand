import pandas as pd
from pathlib import Path
import os


def get_historical_per_capita_TFC(
    input_dir: str, countries: str, year, population_input: str, output_file: str
):
    """
    Get historical values of per capita total final energy consumption of each country.
    Using IEA energy balance data, and match the year with the population year.

    Parameters:
    - input_dir: Directory to extract all the downloaded files.
    - countries: list - List of country codes to process, given in ISO3 codes.
    - year: int - The year to get TFC data from.
    - population_input: str - Path to the extracted population number for the specific
        year of the energy balances.
    - output_file: str - Path of the final output file.

    Unit: GJ/capita, unit conversion performed as energy balance data is in TJ
    """

    dict_all = {"ISO3": [], "TFC_per_capita": []}

    input_path = Path(input_dir)
    files = [str(file) for file in input_path.iterdir() if file.is_file()]
    for file in files:
        if (str(year) in file) & (file.split("_")[-2] in countries):
            # Extract country name from the filepath, hard-coded
            country = file.replace(".csv", "").split("_")[-2]
            df = pd.read_csv(file)
            TFC_country = df[(df["flow"] == "TFC") & (df["product"] == "TOTAL")][
                "value"
            ].values[0]
            # Get population data
            population_country = pd.read_csv(population_input, index_col=0)
            population_country = population_country.at[country, "population"]
            TFC_per_capita = TFC_country / population_country * 1e3  # Switch unit
            dict_all["ISO3"].append(country)
            dict_all["TFC_per_capita"].append(TFC_per_capita)

    output_dir = output_file.split("historical")[0]
    os.makedirs(output_dir, exist_ok=True)
    pd.DataFrame.from_dict(dict_all).to_csv(output_file, index=False)


if __name__ == "__main__":
    get_historical_per_capita_TFC(
        input_dir=snakemake.input.input_dir,
        countries=snakemake.params.countries,
        year=snakemake.params.year,
        population_input=snakemake.input.population_input,
        output_file=snakemake.output.output_file,
    )
