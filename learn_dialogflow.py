import json
import os

from dotenv import load_dotenv

from dialogflow import DialogFlow

load_dotenv()


def main():
    try:
        with open("questions.json", encoding="utf-8") as file:
            learning_data = json.load(file)

        project_id = os.getenv("DIALOGFLOW__PROJECT_ID")
        df = DialogFlow(project_id)

        for key in learning_data.keys():
            df.create_intent(
                key,
                learning_data[key]["questions"],
                [learning_data[key]["answer"]],
            )
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
