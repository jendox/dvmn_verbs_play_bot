import argparse
import json
import os

from dotenv import load_dotenv

from dialogflow import create_intent

load_dotenv()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Скрипт для обучения Dialogflow новыми интентами.",
        epilog="Примеры использования:\n"
               "  python3 learn_dialogflow.py\n"
               "  python3 learn_dialogflow.py -f data/health_questions.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-f", "--filepath",
        default="questions.json",
        help=(
            "Путь к JSON-файлу с обучающими данными. "
            "Если аргумент не указан, используется файл questions.json в текущей директории."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    try:
        with open(args.filepath, encoding="utf-8") as file:
            learning_data = json.load(file)

        project_id = os.getenv("DIALOGFLOW_PROJECT_ID")

        for key in learning_data.keys():
            create_intent(
                project_id,
                key,
                learning_data[key]["questions"],
                [learning_data[key]["answer"]],
            )
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    load_dotenv()
    main()
