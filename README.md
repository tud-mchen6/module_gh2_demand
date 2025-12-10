# Global per-country estimates of electricity demand met by vRES and green hydrogen demand

This module helps producing the demand number for electricity
    demand met by variable Renewable Energy Sources and green hydrogen demand based
    on assumptions of per capita total final energy use, sectoral electrification
    and decarbonisation level, and population of each country. It uses a top-down
    approach and allows different outputs with changing assumptions. For countries
    included in the Energy Statistics Data Browser, the assumptions can be based on
    today's data as a reference.

A modular `snakemake` workflow built for [`clio`](https://clio.readthedocs.io/) data modules.

## Using this module

This module can be imported directly into any `snakemake` workflow.
Please consult the integration example in `tests/integration/Snakefile` for more information.

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
