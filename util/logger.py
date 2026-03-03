import logging


_LOGGER_CONFIGURED = False


def _configure_root_logger():
	global _LOGGER_CONFIGURED
	if _LOGGER_CONFIGURED:
		return

	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
	)
	_LOGGER_CONFIGURED = True


def get_logger(name):
	_configure_root_logger()
	return logging.getLogger(name)
