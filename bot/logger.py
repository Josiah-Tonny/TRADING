import logging
import os
import sys

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("trading_bot")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    os.makedirs("logs", exist_ok=True)
    fh = logging.FileHandler("logs/bot.log", encoding="utf-8")
    
    # Configure StreamHandler with UTF-8 encoding for Windows compatibility
    sh = logging.StreamHandler()
    if hasattr(sh.stream, 'reconfigure'):
        # Python 3.7+
        sh.stream.reconfigure(encoding='utf-8')
    elif sys.platform == "win32":
        # Fallback for older Python or Windows - use UTF-8 via codecs
        import codecs
        sh.stream = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='ignore')

    fmt = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger
