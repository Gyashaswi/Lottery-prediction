# src/ingest/logger.py
import logging, sys

def get_logger(name="lottery"):
    log = logging.getLogger(name)
    if not log.handlers:
        log.setLevel(logging.INFO)
        h = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter("[%(levelname)s] %(message)s")
        h.setFormatter(fmt)
        log.addHandler(h)
    return log
