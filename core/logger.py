# core/logger.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    log_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(module)s | %(message)s')
    log_file = "omni_audit_trail.log"

    # Roterer loggen så den ikke fylder uendeligt (gemmer max 5x 10MB filer)
    my_handler = RotatingFileHandler(log_file, mode='a', maxBytes=10*1024*1024, backupCount=5, encoding=None, delay=0)
    my_handler.setFormatter(log_formatter)
    my_handler.setLevel(logging.DEBUG)

    logger = logging.getLogger('OMNI_HUNTER')
    logger.setLevel(logging.DEBUG)
    
    # Undgå at tilføje handlere flere gange hvis modulet loades igen
    if not logger.handlers:
        logger.addHandler(my_handler)
        
    return logger

logger = setup_logger()