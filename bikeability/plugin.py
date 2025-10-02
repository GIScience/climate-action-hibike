import logging.config

from climatoology.app.plugin import start_plugin
from climatoology.utility.Naturalness import NaturalnessUtility

from bikeability.operator_worker import OperatorBikeability
from bikeability.settings import Settings

log = logging.getLogger(__name__)


def init_plugin() -> None:
    settings = Settings()
    naturalness_utility = NaturalnessUtility(
        host=settings.naturalness_host,
        port=settings.naturalness_port,
        path=settings.naturalness_path,
    )
    operator = OperatorBikeability(naturalness_utility)

    log.info(f'Running plugin: {operator.info().name}')
    return start_plugin(operator=operator)


if __name__ == '__main__':
    exit_code = init_plugin()
    log.info(f'Plugin exited with code {exit_code}')
