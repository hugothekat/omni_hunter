# -*- coding: utf-8 -*-
import logging
import os
import re
from logging.handlers import RotatingFileHandler
from core.utils import session

class OpsecFormatter(logging.Formatter):
    """GOLIATH V8: Auto-Redaction Engine - Maskerer sensitive data i logfilen (OPSEC)"""
    def format(self, record):
        # Formatér den originale besked først
        log_message = super().format(record)
        
        # 1. Maskerer klassiske API nøgler, passwords, secrets og tokens
        # Fanger mønstre som: api_key="sk-12345...", password: secret123
        log_message = re.sub(
            r'(?i)(api[_-]?key|password|secret|token|pwd|auth)[\s=:]+[\'"]?([A-Za-z0-9\-_]{8,})[\'"]?', 
            r'\1=[REDACTED_OPSEC]', 
            log_message
        )
        
        # 2. Maskerer Bearer / JWT HTTP headers
        log_message = re.sub(
            r'(?i)Bearer\s+[A-Za-z0-9\-._~+/]+', 
            'Bearer [REDACTED_JWT_TOKEN]', 
            log_message
        )
        
        return log_message

def setup_logger():
    # Sikrer at log-mappen eksisterer pænt inde i dit loot-miljø
    loot_dir = session.get("loot_folder", "loot_evidence")
    log_dir = os.path.join(loot_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "goliath_audit_trail.log")

    # Udvidet V8 Formatter (Inkluderer nu præcist linjenummer for lynhurtig debugging)
    log_formatter = OpsecFormatter('%(asctime)s | %(levelname)-8s | [%(module)s:%(lineno)d] | %(message)s')

    # Roterer loggen så den ikke fylder uendeligt (gemmer max 5x 10MB filer)
    # NY V8 FIX: encoding='utf-8' sikrer at Darkweb/Kinesiske tegn ikke crasher loggeren!
    my_handler = RotatingFileHandler(log_file, mode='a', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8', delay=0)
    my_handler.setFormatter(log_formatter)
    my_handler.setLevel(logging.DEBUG)

    logger = logging.getLogger('GOLIATH_V8')
    logger.setLevel(logging.DEBUG)
    
    # Undgå at tilføje handlere flere gange hvis modulet loades igen
    if not logger.handlers:
        logger.addHandler(my_handler)
        
    return logger

# Global GOLIATH logger instans
logger = setup_logger()