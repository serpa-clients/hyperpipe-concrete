import logging
from typing import ParamSpec
from functools import wraps

P = ParamSpec('P')

class Logger(logging.Logger):
    def __init__(
        self, 
        name: str, 
        level: int = logging.DEBUG,
        handler: None|logging.Handler = None,
        format: str = f'%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
    ):

        super().__init__(name, level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(format)
        handler.setFormatter(formatter)
        self.addHandler(handler)
    
    @wraps(logging.Logger.debug)
    def debug(self, msg: str, *args: P.args, **kwargs: P.kwargs) -> None:
        super().debug(msg, *args, **kwargs)
    
    @wraps(logging.Logger.info)
    def info(self, msg: str, *args: P.args, **kwargs: P.kwargs) -> None:
        super().info(msg, *args, **kwargs)
    
    @wraps(logging.Logger.warning)
    def warning(self, msg: str, *args: P.args, **kwargs: P.kwargs) -> None:
        super().warning(msg, *args, **kwargs)
    
    @wraps(logging.Logger.error)
    def error(self, msg: str, *args: P.args, **kwargs: P.kwargs) -> None:
        super().error(msg, *args, **kwargs)
    
    @wraps(logging.Logger.exception)
    def exception(self, msg: str, *args: P.args, **kwargs: P.kwargs) -> None:
        super().exception(msg, *args, **kwargs)