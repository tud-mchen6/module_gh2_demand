import pandas as pd
import glob
import os


def get_elec_TnD_loss_rate(inputs: str, output_dir: str, output_file: str):
    """
    Calculate the transmission & distribution loss rates of each country from the
    electricity balance data.

    Assume this rate does not change significantly over the years. If data is missing,
    assign 0 loss rate.

    Parameters:
    - inputs: str - Paths to the energy balances country-specific CSV files.
    - output_dir: str - Path to save the calculated CSV file.
    - output_file: str - Path of the final output file.

    Unit of data: GWh, but the output is dimensionless
    """

    dict_all = {"ISO3": [], "ELEC_LOSS_RATE": []}

    for filepath in list(inputs):
        # Extract country name from the filepath, hard-coded
        country = filepath.replace(".csv", "").split("_")[-2]
        df = pd.read_csv(filepath)
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

    os.makedirs(output_dir, exist_ok=True)
    pd.DataFrame.from_dict(dict_all).to_csv(output_file, index=False)


if __name__ == "__main__":
    get_elec_TnD_loss_rate(
        inputs=snakemake.input.inputs,
        output_dir=snakemake.params.output_dir,
        output_file=snakemake.output.output_file,
    )
