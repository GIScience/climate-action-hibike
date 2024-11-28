import logging.config

from climatoology.app.plugin import start_plugin

from bikeability.operator_worker import OperatorBikeability

log = logging.getLogger(__name__)


def init_plugin() -> None:
    operator = OperatorBikeability()

    log.info(f'Running plugin: {operator.info().name}')
    return start_plugin(operator=operator)


if __name__ == '__main__':
    exit_code = init_plugin()
    log.info(f'Plugin exited with code {exit_code}')
