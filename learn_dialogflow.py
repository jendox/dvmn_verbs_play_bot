import json
import os

from dotenv import load_dotenv
from google.cloud import dialogflow

load_dotenv()


def create_intent(project_id, display_name, training_phrases_parts, message_texts):
    intents_client = dialogflow.IntentsClient()

    parent = dialogflow.AgentsClient.agent_path(project_id)
    training_phrases = []
    for training_phrases_part in training_phrases_parts:
        part = dialogflow.Intent.TrainingPhrase.Part(text=training_phrases_part)
        training_phrase = dialogflow.Intent.TrainingPhrase(parts=[part])
        training_phrases.append(training_phrase)

    text = dialogflow.Intent.Message.Text(text=message_texts)
    message = dialogflow.Intent.Message(text=text)

    intent = dialogflow.Intent(
        display_name=display_name, training_phrases=training_phrases, messages=[message],
    )

    response = intents_client.create_intent(
        request={"parent": parent, "intent": intent},
    )
    print(f"Intent created: {response}")


def main():
    project_id = os.getenv("PROJECT_ID")
    with open("questions.json", encoding="utf-8") as file:
        learning_data = json.load(file)

    for key in learning_data.keys():
        create_intent(
            project_id,
            key,
            learning_data[key]["questions"],
            [learning_data[key]["answer"]],
        )


if __name__ == "__main__":
    main()
