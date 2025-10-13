import logging
import os

from dotenv import load_dotenv

import vk_bot
from dialog_flow import dialogflow_project_id

load_dotenv()


def setup_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


def main():
    dialogflow_project_id.set(os.getenv("PROJECT_ID"))
    vk_bot.start_bot()


if __name__ == "__main__":
    main()
