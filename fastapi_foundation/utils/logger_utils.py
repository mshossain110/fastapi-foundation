import logging
import logging.config
import json
import sys
import os
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record),
            "module": record.module,
            "function": record.funcName,
            "name": record.name,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging(settings):
    # Custom logging configuration
    log_level = settings.log_level.upper() if settings.log_level else 'INFO'
    env = 'dev' if settings.environment and settings.environment=='development' else None
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Create log filename based on date
    log_filename = f"logs/app_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Custom logging configuration
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': JsonFormatter,
            },
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
        },
        'handlers': {
            'console': {
                'level': log_level,
                'formatter': 'standard' if env == "dev" else 'json',
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
            },
            'file': {
                'level': log_level,
                'formatter': 'json',
                'class': 'logging.FileHandler',
                'filename': log_filename,
                'mode': 'a',
            },
            'request_response_file': {
                'level': log_level,
                'formatter': 'json',
                'class': 'logging.FileHandler',
                'filename': f"logs/requests_{datetime.now().strftime('%Y-%m-%d')}.log",
                'mode': 'a',
            },
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': False
            },
            'request_response': {
                'handlers': ['console', 'request_response_file'],
                'level': log_level,
                'propagate': False
            },
        },
    }

    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)

    # Get the root logger
    logger = logging.getLogger()

    return logger