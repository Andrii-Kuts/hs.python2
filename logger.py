import logging
import os
from datetime import datetime

timestamp = datetime.now().strftime('%d.%m.%y_%H:%M:%S')
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/{timestamp}.log")
    ]
)
logger = logging.getLogger(__name__)