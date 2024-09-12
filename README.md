# <img src="resources/info/icon.jpeg" width="5%"> Plugin Blueprint

This repository is a blueprint for operator creators. Operators are science2production facilitators that will make it easy for you to bring your ideas and research results to the Climate Action (CA) platform. Operators are the main workers inside plugins. You will create a plugin but all you need to do is code the operator functionality, the plugin wrapper is already set to go. The terms Operator and Plugin are therefore mostly synonymous for you. For more information on the architecture, please contact the [CA team](https://heigit.org/).

Please follow the subsequent steps to bring your plugin to life.

## Preparation

A new plugin should be thoroughly discussed with the CA team. But don't be hesitant, they are very welcoming to new ideas :-) !

### Git

The CA team will fork **this** repository for you and you will get full access to the fork (see below for admins). You can then `git clone` the fork and work on it as in any other git project.

Create a new branch by running `git checkout -b <my_new_plugin_name>`.
After you have finished your implementation, you can create a merge request (MR) to the `main` branch that can be reviewed by the CA team.
Yet, we highly encourage you to create smaller intermediate MRs for review!

### Python Environment

We use [poetry](https://python-poetry.org) as an environment management system.
Make sure you have it installed.
Apart from some base dependencies, there is only one fixed dependency for you, which is the [climatoology](https://gitlab.heigit.org/climate-action/climatoology) package that holds all the infrastructure functionality.
Make sure you have read-access to the climatoology repository (i.e. you can clone it).

Head over to the [pyproject.toml](pyproject.toml) and replace the name description and author attributes with your plugins information.
If you don't want to get creative you can simply mimic the repository name for you project name.

Now run

```shell
poetry install --no-root
```

and you are ready to code within your poetry environment.

### Testing

We use [pytest](pytest.org) as testing engine.
Ensure all tests are passing on the unmodified repository by running `poetry run pytest`.

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

## Start Coding

### Names

We have to replace names at multiple level.

Let's start with refactoring the name of the package ([plugin_blueprint/](bikeability)).
Rename it to the project name you have defined above in your `pyproject.toml`.
This directory is also copied to the Docker container we use for deployment.
Therefore, you have to change the name also in the [Dockerfile](Dockerfile) and the [Dockerfile.Kaniko](Dockerfile.Kaniko).

Next there is one class that should be name-related to your plugin:
The `OperatorBlueprint` in [plugin.py](bikeability/plugin.py).
Refactor-rename this class with reasonable names related to your idea.

**Make these changes your first MR** and add your CA-team contact as reviewer.

### Functionality

We have seperated the code into multiple files by their functionality.
Three files are relevant for you:

1. The [operator_worker.py](bikeability/operator_worker.py) that defines your operator logic,
2. the [input.py](bikeability/input.py) that defines the user inputs required to run your plugin and
3. [test_plugin.py](test/test_plugin.py) where you define the unit tests for your plugin.

We will go through these files step by step.

#### Tests in [test_plugin.py](test/test_plugin.py)

We highly encourage [test driven development](https://en.wikipedia.org/wiki/Test-driven_development).
In fact, we require two predefined tests to successfully run on your plugin.

 - The first test confirms that your plugin announcement is working as expected (`test_plugin_info_request`).
 - The second test ensures that your computation runs as expected in a test environment (`test_plugin_compute_request`).

These tests ensure that the development contract is met.

Therefore, before you start coding, please take some time to sketch the outline of your plugin.
You will need a clear _definition and description_ of your plugin as well as an idea of the required _input_ and the produced _output_.
You can of course adapt this later, but you should have a rough idea from the start.

Then open [conftest.py](test/conftest.py).
Adapt the content of the following three `pytest.fixture` functions to meet your expectations:

 1. The `expected_info_output` fixture is quite easy to write:
simply declare an `Info` element.
Have a look at the classes source code to see all required attributes.
Make sure you add the referenced files to your repository.
The list of concerns is limited on purpose to have a curated set of keywords.
If you feel that your plugin would benefit from an extension of that list, feel free to contact the CA team or create a MR in the [climatoology](https://gitlab.heigit.org/climate-action/climatoology) repository.

 2. For now, you can leave the `expected_compute_input` as is.
It is better to update it, once you have made the first changes to the actual working code later.

 3. The `expected_compute_output` will probably grow over time.
But you should define a first output result you would like to create through your plugin.
Define it in the test and add the required file to the repository.

That's it, the tests should fail, and you can start coding towards making them succeed.

You will notice that not only the tests in [`test_plugin.py`](test/test_plugin.py) failed, but also in [`test_operator_worker.py`](test/test_operator_worker.py).
Testing the plugin only asserts the functionality within the architecture.
It does not assert the intended functionality of the operator.
The Blueprint creates an example output for each supported output type.
Each of the data creation methods is also thoroughly tested.
We expect you do the same for your code.
Yet, the provided tests will only be of limited use for you.
We therefore suggest you replace them along with the current operator code (see below).
Start simple by coding a single operator method and a single operator test.

If you use external services, they should be mocked.
This will, among other benefits, reduce the resource consumption for testing.
You can have a look at the other fixtures in [conftest.py](test/conftest.py) for some examples how we mocked external APIs but don't get overwhelmed.
The CA team can help you implement these setups, when the need arises.

But let's create some code first:

#### Operator in [operator_worker.py](bikeability/operator_worker.py)

##### Info Function

Now lets make the tests succeed.
For the info function this is very simple.
Just copy the test info declaration over to the plugin file.
Done.

##### Compute Function

Now, *finally*, comes the main coding part.
This function is where you can explode your genius and create ohsome results.
You are free to create additional classes or methods as needed or write a single script just as you would in jupyter.

You will probably also use external services like [ohsome-py](https://github.com/GIScience/ohsome-py).
In addition, you can use the provided utilities of the CA team.
A list of utilities can be found in the [climatoology](https://gitlab.heigit.org/climate-action/climatoology) repository, but we also provide examples for their usage in this repository.

The only requirement is to return a (potentially empty) list of Artifacts i.e. results.

#### Input parameters in [input.py](bikeability/input.py)

Keep in mind to update the input parameter class and the tests while you are coding away.

### Development stages

The first MR you created above paved the way for the future development of the plugin.

#### Dummy

Your next step will be to create a dummy version of your plugin.
The dummy version will help you formalise the data creation pipeline.
It will _not_ create real output but rather return a mocked result that in its type, color etc. resembles the real output.
Therefore, it will not be shared outside the climate action group!

To create your dummy you can either hand-craft a very small dataset or you can use a subset of an existing dataset.
For example if you want to output highways colored by certain attributes, your dummy could be to output all lines from OSM having the tag `highway=path` in the area of interest.
Nothing more.

To accomplish this goal, first go through the existing code and remove all methods, tests and dependencies that are not required for this dummy.
Reduce the code and documentation (like *this* README) to a bare minimum.
Don't worry, you can later go back to the [plugin blueprint](https://gitlab.heigit.org/climate-action/plugin-blueprint) repository and recover methods that you deleted earlier, if you need them.

Next, hand-craft your dummy in the code and return it as an artifact.
Don't forget to adapt the tests and update the documentation.
If you are satisfied with the results and the tests pass, you have succeeded!
Please create a MR to `main` and ask the CA team for a review.
Make sure to follow the [companies' guidelines](https://heigit.atlassian.net/wiki/spaces/SD/pages/3735635/Guidelines) on commits and merge requests.

After your MR was accepted and merged create a release ([see how-to below](#releasing-a-new-plugin-version)) called `dummy` (https://docs.gitlab.com/ee/user/project/releases/#create-a-release-in-the-releases-page).
Then ask the climate action admins to deploy your plugin to the [staging environment](https://staging.climate-action.heigit.org).

#### Demo

The next step is your demo.
You should have established an outline and a definition of the content of your demo content with your content supervisor.
The goal of the demo is to create output that has real content but is extremely limited.
It will be the first version that is also communicated to the respective partners.

Follow the same process as for the Dummy

1. Add the methods, tests, dependencies and documentation required to accomplish the goal
2. Create a MR
3. Create a release called `demo`

#### Version 1 and beyond

From now on you can repeat this process for each release target that you, your content supervisor and the partner define.


## Development setup

By now your plugin should be up and running on the climate action infrastructure.
Because you are doing rigorous testing we can have trust in the code and be sure it works in deployment.

Yet, you may still want to run your plugin locally.
Unfortunately, running you plugin locally takes a bit more setup:

1. Set up the [infrastructure](https://gitlab.heigit.org/climate-action/infrastructure) locally in `dev` mode
2. Copy [.env_template](.env_template) to `.env` and update it

You now have two options:

1. Run `env $(cat .env | xargs) poetry run python {plugin-name}/plugin.py` or add the env-vars to your IDE and run the plugin OR
2. Build a docker container and run the plugin dockerised (see [below](#Docker-for-admins-and-interested-devs))

## Releasing a new plugin version

To release a new plugin version

1. update the version attribute in the [pyproject.toml](pyproject.toml) (e.g. by running `poetry version {patch|minor|major}`)
2. update the version in the plugin `info` method
3. create a [release](https://docs.gitlab.com/ee/user/project/releases/) on GitLab, preferably including a changelog

Once your plugin outgrew the 'special versions' `dummy` and `demo`, we suggest to adhere to the [Semantic Versioning](https://semver.org/) scheme.
You can think of your plugin methods (info method, input parameters and artifacts) as the public API of your plugin.


## Docker (for admins and interested devs)

If the infrastructure is reachable you can copy [.env_template](.env_template) to `.env` and then run

```shell
DOCKER_BUILDKIT=1 docker build --secret id=CI_JOB_TOKEN . --tag heigit/{plugin-name}:devel
docker run --env-file .env --network=host heigit/{plugin-name}:devel
```

Make sure the cone-token is copied to the text-file named `CI_JOB_TOKEN` that is mounted to the container build process as secret.

To deploy this plugin to the central docker repository run

```shell
DOCKER_BUILDKIT=1 docker build --secret id=CI_JOB_TOKEN . --tag heigit/{plugin-name}:devel
docker image push heigit/{plugin-name}:devel
```

### Kaniko

To test the docker build from Kaniko run

```shell
docker run -v ./:/workspace \
    -v ./CI_JOB_TOKEN:/kaniko/CI_JOB_TOKEN \
    gcr.io/kaniko-project/executor:v1.14.0-debug \
    --dockerfile /workspace/Dockerfile.Kaniko \
    --context dir:///workspace/ \
    --no-push
```

Don't forget to add the plugin to the [infrastructure](https://gitlab.heigit.org/climate-action/infrastructure) and deploy it, once ready.

## Forking this repository (for admins)

To enable a plugin contribution [fork](https://docs.gitlab.com/ee/user/project/repository/forking_workflow.html) this repository.
The following changes are necessary in the new fork:

1. [Unlink the fork](https://docs.gitlab.com/ee/user/project/repository/forking_workflow.html#unlink-a-fork) to make it an independent repository
2. In the Merge-Request settings set
   1. Fast-forward merge
   2. Delete source branch by default
   3. Require squashing
   4. Pipelines must be successful
3. [Protect tags](https://docs.gitlab.com/ee/user/project/protected_tags.html) in order to have access to the protected docker credentials when creating releases
4. Assign the appointed person as maintainer
5. Create an issue for the appointed maintainer stating `Please choose an appropriate repository icon and name`
6. Create the necessary (private!) docker repositories to push images
   1. the main repository with read and write access set to `climateactionreader` and `climateactionwriter` respectively
   2. the `[...]-cache` repository with equal access
