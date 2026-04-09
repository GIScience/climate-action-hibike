import logging.config

from climatoology.app.plugin import start_plugin
from climatoology.utility.naturalness import NaturalnessUtility
from mobility_tools.settings import ORSSettings, S3Settings

from bikeability.core.operator_worker import OperatorBikeability
from bikeability.core.settings import Settings

log = logging.getLogger(__name__)


def init_plugin(
    initialized_settings: Settings, initialized_ors_settings: ORSSettings, initialized_s3_settings: S3Settings
) -> int | None:
    settings = Settings()
    naturalness_utility = NaturalnessUtility(
        base_url=f'http://{settings.naturalness_host}:{settings.naturalness_port}{settings.naturalness_path}',
    )
    operator = OperatorBikeability(
        naturalness_utility, ors_settings, s3_settings
    )  # todo: confirm there should be initialized settings or global settings.

    log.info(f'Running plugin: {operator.info().name}')
    return start_plugin(operator=operator)


if __name__ == '__main__':
    settings = Settings()
    ors_settings = ORSSettings()
    s3_settings = S3Settings()
    exit_code = init_plugin(settings, ors_settings, s3_settings)
    log.info(f'Plugin exited with code {exit_code}')
