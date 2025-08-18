from datetime import datetime
import inspect
import logging
import os
from pathlib import Path
import sys
from typing import Optional


class CustomLogger:
    def __init__(self):
        self.name = os.getenv("LOGGER_NAME", "telegram_bot")
        self.level = self._get_log_level()
        self.console_output = os.getenv("LOGGER_CONSOLE", "true").lower() == "true"
        self.file_output = os.getenv("LOGGER_FILE", "false").lower() == "true"

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.level)

        self.logger.handlers.clear()

        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def _get_log_level(self) -> int:
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        env_level = os.getenv("LOGGER_LEVEL", "INFO").upper()
        return level_map.get(env_level, logging.INFO)

    def _get_caller_info(self) -> str:
        current_frame = inspect.currentframe()
        if current_frame and current_frame.f_back and current_frame.f_back.f_back:
            caller_frame = current_frame.f_back.f_back
            filename = caller_frame.f_code.co_filename
            lineno = caller_frame.f_lineno
            module_name = os.path.basename(filename).replace(".py", "")
            return f"{module_name}:{lineno}"
        return "unknown:0"

    def debug(self, message: str, *args, **kwargs):
        caller = self._get_caller_info()
        self.logger.debug(f"[{caller}] {message}", *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        caller = self._get_caller_info()
        self.logger.info(f"[{caller}] {message}", *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        caller = self._get_caller_info()
        self.logger.warning(f"[{caller}] {message}", *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        caller = self._get_caller_info()
        self.logger.error(f"[{caller}] {message}", *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        caller = self._get_caller_info()
        self.logger.critical(f"[{caller}] {message}", *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        caller = self._get_caller_info()
        self.logger.exception(f"[{caller}] {message}", *args, **kwargs)


logger = CustomLogger()
