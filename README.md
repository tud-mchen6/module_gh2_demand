# Global per-country estimates of electricity demand met by vRES and green hydrogen demand

This module helps producing the electricity needed to be produced by variable Renewable Energy Sources and green hydrogen demand based on assumptions of per capita total final energy use, sectoral electrification and decarbonisation level, as well as population of each country. It uses a top-down approach and allows different outputs with changing assumptions. For countries included in the IEA Energy Statistics Data Browser, the assumptions can be based on today's data as a reference.

A modular `snakemake` workflow built for [`clio`](https://clio.readthedocs.io/) data modules.

## Using this module

This module can be imported directly into any `snakemake` workflow.
Please consult the integration example in `tests/integration/Snakefile` for more information.


### Inputs of the module
To calculate the demand of specific countries in the end, the following data is needed (all in yearly aggregated form): total final consumption level (TFC) per person, sectoral share of TFC, sectoral electrification level, and decarbonisation level of both electrified and non-electrified parts of each sector. The users can specify the countries they want to include in the workflow. If not specified, the included countries are the countries with available data on the [IEA Energy Statistics Data Browser](https://www.iea.org/data-and-statistics/data-tools/energy-statistics-data-browser?country=WORLD&fuel=Energy%20supply&indicator=TESbySource).  

The users can choose to use historical data as input, or put overwrites. You can make assumptions that apply to all countries defined in the workflow, or make assumptions that apply to all sectors of specific countries, or specific sectors of specific countries. The more specific the overwrites are, the higher priority they have. The templates of these inputs are in `config/user_input_templates`; put your overwrite in exactly the same format into `resources/user` if you would like to use these overwrites.

The config file defines global parameters to be used in the workflow. There are required parameters and optional ones. Each run should be characterised by the scenario name (defined in `config/config.yaml`). Users should specify here if the default should be historical data; if not, they should define the default value in the `config` themselves. Additionally, the user can configure the selected list of contries, or the year whose data the user wants to download from IEA.  
The meanings of the user-definable parameters, such as `non_elec_decarb_abs`, see the config schema (`workflow\internal\config.schema.yaml`).

### Download data prerequisites (temporary, need to fix)

Place `config/automatic_input/country_codes.csv` under `resources/automatic`. This files records all countries that have data on the IEA dataset.

### Commands to run the module

Assume the user wants to get both vRES demand and green hydrogen demand, simply run the `all` rule. Specify the number of cores depending on the size of the problem.

`snakemake -c 4`

Assume the user only want to get a specific file that's an intermediate product of the whole workflow, the user can specify that file in the command to run snakemake. The specifics can be seen in the rule definitions.

`snakemake -c 4 "path/to/target/file"`

If the rule to run does not contain wildcards, the user can also just specify the rule name.

`snakemake -c 4 rule_name`

## Development

We use [`pixi`](https://pixi.sh/) as our package manager for development.
Once installed, run the following to clone this repo and install all dependencies.

```shell
git clone git@github.com:calliope-project/module_gh2_demand.git
cd module_gh2_demand
pixi install --all
```

For testing, simply run:

```shell
pixi run test-integration
```

To view the documentation locally, use:

```shell
pixi run serve-docs
```

To test a minimal example of a workflow using this module:

```shell
pixi shell    # activate this project's environment
cd tests/integration/  # navigate to the integration example
snakemake --use-conda --cores 2  # run the workflow!
```


### Structure of the module
![Rules of this workflow](rulegraph.pdf)
There are two outputs of this workflow: electricity needed to be produced by vRES and green hydrogen needed to be produced (assuming hydrogen are all produced by electrolysis powered by vRES). Both are presented as a yearly aggregated value; no time series are included.

The rules are classified into three types and are defined in three `.smk` files: `automatic`, `process_data`, and `calculate_demand`.

`automatic` rules are used to download data from external sources, such as the IEA energy balance or the UN population projection. (These rules are not shown on the rulegraph.)

`process_data` rules are used to process the downloaded data, put them into the format that is easier to deal with, pick the relevant information, and save them into a newer format though retaining the original data. Some rules also include some simple performing calculations on the downloaded data, such as electrification levels of sectors in each country.  
These downloaded data are mostly historical data, i.e., how the energy system has been. They can be used as a reference for the assumptions given to calculate the demands.

`calculate_demand` rules are the two rules that respectively produce what is called 'vRES demand' and 'green hydrogen demand'. These are based on the all the assumptions given.

### Temporary features
- This is now only tailored to national level demand and the data sources are strongly dependent on IEA. In the future, regional or continental data creation should be allowed.

### TODO lists
- Make it compatible to countries that have no data input in IEA
- Make the population rule compatible to other scenarios than Medium