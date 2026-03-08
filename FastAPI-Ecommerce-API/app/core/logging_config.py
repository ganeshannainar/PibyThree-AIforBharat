import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Create logs directory
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Log file path
LOG_FILE = os.path.join(LOGS_DIR, 'ecommerce.log')

# Custom formatter with emojis for different log levels
class EmojiFormatter(logging.Formatter):
    """Custom formatter that adds emojis based on log level"""
    
    EMOJIS = {
        logging.DEBUG: '🔍',
        logging.INFO: '✅',
        logging.WARNING: '⚠️',
        logging.ERROR: '❌',
        logging.CRITICAL: '🚨'
    }
    
    def format(self, record):
        emoji = self.EMOJIS.get(record.levelno, '📝')
        record.emoji = emoji
        return super().format(record)


def setup_logging():
    """Setup application-wide logging configuration"""
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = EmojiFormatter(
        '%(emoji)s %(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation (10MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Create specific loggers for our modules
    loggers = {
        'dynamic_pricing': logging.getLogger('dynamic_pricing'),
        'promotions': logging.getLogger('promotions'),
        'gemini': logging.getLogger('gemini'),
        'ml_model': logging.getLogger('ml_model'),
        'api': logging.getLogger('api'),
    }
    
    for logger in loggers.values():
        logger.setLevel(logging.DEBUG)
    
    return loggers


# Initialize logging
loggers = setup_logging()

# Export individual loggers for easy import
dynamic_pricing_logger = loggers['dynamic_pricing']
promotions_logger = loggers['promotions']
gemini_logger = loggers['gemini']
ml_model_logger = loggers['ml_model']
api_logger = loggers['api']


def log_separator(logger, title=""):
    """Log a visual separator for better readability"""
    separator = "=" * 60
    if title:
        logger.info(f"\n{separator}\n  {title}\n{separator}")
    else:
        logger.info(separator)


def log_flow_start(logger, flow_name, **kwargs):
    """Log the start of a flow with parameters"""
    log_separator(logger, f"🚀 FLOW START: {flow_name}")
    for key, value in kwargs.items():
        logger.info(f"  📌 {key}: {value}")


def log_flow_end(logger, flow_name, success=True, **kwargs):
    """Log the end of a flow with results"""
    status = "✅ SUCCESS" if success else "❌ FAILED"
    logger.info(f"\n  {status}: {flow_name}")
    for key, value in kwargs.items():
        logger.info(f"  📊 {key}: {value}")
    log_separator(logger)


def log_step(logger, step_number, description, **kwargs):
    """Log a step in a flow"""
    logger.info(f"\n  📍 Step {step_number}: {description}")
    for key, value in kwargs.items():
        logger.debug(f"      └─ {key}: {value}")
