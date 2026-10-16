import pandas as pd
from pathlib import Path
import os


def get_elec_TnD_loss_rate(input_dir: str, countries: str, year: int, output_file: str):
    """
    Calculate the transmission & distribution loss rates of each country from the
    electricity balance data.

    Assume this rate does not change significantly over the years. If data is missing,
    assign 0 loss rate.

    Parameters:
    - input_dir: str - Directory to extract all the downloaded files.
    - countries: list - List of country codes to process, given in ISO3 codes.
    - output_file: str - Path of the final output file.
    - year: int - The year to get IEA data from.

    Unit of data: GWh, but the output is dimensionless
    """

    dict_all = {"ISO3": [], "ELEC_LOSS_RATE": []}

    input_path = Path(input_dir)
    files = [str(file) for file in input_path.iterdir() if file.is_file()]
    for file in files:
        if (str(year) in file) & (file.split("_")[-2] in countries):
            # Extract country name from the filepath, hard-coded
            country = file.replace(".csv", "").split("_")[-2]
            df = pd.read_csv(file)
            # Get the electricity total production
            matches = df.loc[
                (df["flow"] == "EHINDPROD") & (df["product"] == "ELECTR"), "value"
            ]
            tot_prod = matches.iloc[0] if not matches.empty else 0
            # Get the net import
            matches_import = df.loc[
                (df["flow"] == "IMPORTS") & (df["product"] == "ELECTR"), "value"
            ]
            imports = matches_import.iloc[0] if not matches_import.empty else 0
            matches_export = df.loc[
                (df["flow"] == "EXPORTS") & (df["product"] == "ELECTR"), "value"
            ]
            exports = matches_export.iloc[0] if not matches_export.empty else 0
            net_import = imports + exports
            # Get the total transmission and distribution losses
            matches_loss = df[(df["flow"] == "DISTLOSS") & (df["product"] == "ELECTR")][
                "value"
            ]
            TnD_loss = matches_loss.iloc[0] if not matches_loss.empty else 0
            dict_all["ISO3"].append(country)
            # Check if data is available; if not, aassign 0 loss rate
            if net_import + tot_prod > 0:
                dict_all["ELEC_LOSS_RATE"].append(TnD_loss / (net_import + tot_prod))
            else:
                dict_all["ELEC_LOSS_RATE"].append(0)

    output_dir = output_file.split("IEA")[0]
    os.makedirs(output_dir, exist_ok=True)
    pd.DataFrame.from_dict(dict_all).to_csv(output_file, index=False)


if __name__ == "__main__":
    get_elec_TnD_loss_rate(
        input_dir=snakemake.input.input_dir,
        countries=snakemake.params.countries,
        year=snakemake.params.year,
        output_file=snakemake.output.output_file,
    )
