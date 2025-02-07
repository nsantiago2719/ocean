from inspect import getmembers
from typing import Type
from pydantic import BaseModel

import uvicorn

from port_ocean.bootstrap import create_default_app
from port_ocean.config.dynamic import default_config_factory
from port_ocean.config.settings import ApplicationSettings, LogLevelType
from port_ocean.core.defaults.initialize import initialize_defaults
from port_ocean.logger_setup import setup_logger
from port_ocean.ocean import Ocean
from port_ocean.utils import get_spec_file, load_module


def _get_default_config_factory() -> None | Type[BaseModel]:
    spec = get_spec_file()
    config_factory = None
    if spec is not None:
        config_factory = default_config_factory(spec.get("configurations", []))

    return config_factory


def run(
    path: str = ".",
    log_level: LogLevelType = "INFO",
    port: int = 8000,
    initialize_port_resources: bool | None = None,
) -> None:
    application_settings = ApplicationSettings(log_level=log_level, port=port)

    setup_logger(application_settings.log_level)
    config_factory = _get_default_config_factory()
    default_app = create_default_app(path, config_factory)

    main_path = f"{path}/main.py" if path else "main.py"
    app_module = load_module(main_path)
    app: Ocean = {name: item for name, item in getmembers(app_module)}.get(
        "app", default_app
    )

    # Override config with arguments
    if initialize_port_resources is not None:
        app.config.initialize_port_resources = initialize_port_resources
    if app.config.initialize_port_resources:
        initialize_defaults(
            app.integration.AppConfigHandlerClass.CONFIG_CLASS, app.config
        )

    uvicorn.run(app, host="0.0.0.0", port=application_settings.port)
