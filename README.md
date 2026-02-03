# <img src="resources/gitlabicon.png" width="5%"> hiBike

The hiBike plugin, created in cooperation with [Radlobby](https://www.radlobby.at/).

## Contributing

To contribute, install the dependencies

```shell
poetry install
```

and the pre-commit hooks:

```shell
poetry run pre-commit install
```

### Tests

To run all tests:
```shell
poetry run pytest
```

#### Coverage

To get a coverage report of how much of your code is run during testing, execute
`poetry run pytest --ignore test/core/ --cov`.
We ignore the `test/core/` folder when assessing coverage because the core tests run the whole plugin to be sure
everything successfully runs with a very basic configuration.
Yet, they don't actually test functionality and therefore artificially inflate the test coverage results.

To get a more detailed report including which lines in each file are **not** tested,
run `poetry run pytest --ignore test/core/ --cov --cov-report term-missing`


### Linting and formatting

It is important that the code created by the different plugin developers adheres to a certain standard.
We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting the code as part of our pre-commit hooks.
Please activate pre-commit by running `poetry run pre-commit install`.
It will now run automatically before each commit and apply fixes for a variety of lint errors to your code.
Note that we have increased the maximum number of characters per line to be 120 to make better use of large modern displays.
If you want to keep short lines explicitly seperate (e.g. in the definition of functions or list) please use ["magic trailing commas"](https://docs.astral.sh/ruff/settings/#format_skip-magic-trailing-comma).

### Logging

Using the environment variable `LOG_Level` you can adjust the amount of log messages produced by the plugin.
Please make sure to use logging throughout your plugin.
This will make debugging easier at a later stage.

## Docker (for admins and interested devs)

If the infrastructure is reachable you can copy [.env.base_template](.env.base_template) to `.env.base` and then run

```shell
docker build . --tag repo.heigit.org/climate-action/bikeability:devel
docker run --env-file .env.base --network=host heigit/{bikeability}:devel
```


To deploy this plugin to the central docker repository run

```shell
docker build . --tag repo.heigit.org/climate-action/bikeability:devel
docker image push heigit/{bikeability}:devel
```

To mimic the build behaviour of the CI you have to add --build-arg CI_COMMIT_SHORT_SHA=$(git rev-parse --short HEAD)
to the above command.

To build a canary version with the latest `climatoology` (depending on your dependency declaration) also add
`--build-arg "CANARY=true"`, i.e. run
`docker build . --build-arg CANARY=true --build-arg CI_COMMIT_SHORT_SHA=$(git rev-parse --short HEAD) --tag repo.heigit.org/climate-action/bikeability:canary --push`
