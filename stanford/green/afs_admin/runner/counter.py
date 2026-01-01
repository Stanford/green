"""Keep track of external commands called.
"""

import logging
import threading

logger = logging.getLogger(__name__)

class CommandCounter:
    """
    Code is from ChatGPT 4.1
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, verbose=False):
        logger.debug("entering CommandCoutner new() method")
        with cls._lock:
            logger.info("got CommandCounter lock")
            if cls._instance is None:
                cls._instance = super(CommandCounter, cls).__new__(cls)
                cls._instance._count     = 0
                cls._instance._lap_count = 0
                cls._instance._verbose   = verbose

                logger.info("created CommandCounter singleton")

        return cls._instance

    def increment(self):
        with self._lock:
            self._count     += 1
            self._lap_count += 1

        msg = f"incremented counter; new value {self.get_count()}"
        logger.debug(msg)

    def get_count(self):
        with self._lock:
            return self._count

    def get_lap_count(self):
        with self._lock:
            return self._lap_count

    def reset_lap(self):
        with self._lock:
            self._lap_count = 0

        msg = f"reset counter lap counter to zero"
        logger.debug(msg)
