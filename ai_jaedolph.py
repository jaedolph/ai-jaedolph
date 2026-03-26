"""AI Jaedolph - an AI chatbot with TTS used for Jaedolph's stream"""

import base64
import configparser
import logging
import os

import requests
from flask import Flask, jsonify, request
from google.genai import Client, errors, types

VOICEBOX_TIMEOUT = 120


def get_ai_response(user_input):
    """Gets the response of the AI Jaedolph persona from Gemini.

    :param user_input: the user's question to ask AI Jaedolph
    :type user_input: string
    :return: the ai's response
    :rtype: string
    """
    app.logger.info("getting ai response from gemini...")
    response = gemini_client.models.generate_content(
        model=config["gemini"]["model"],
        contents=user_input,
        config=types.GenerateContentConfig(
            system_instruction=config["gemini"]["system_prompt"],
            temperature=config["gemini"]["temperature"],
        ),
    )

    app.logger.info("ai response: %s", response.text)
    return response.text


def generate_tts(text):
    """Generates TTS audio using voicebox, then saves the output to disk.

    :param text: text to read in the TTS engine
    :type text: string
    """

    app.logger.info("generating tts with voicebox...")
    payload = {
        "text": text,
        "profile_id": config["voicebox"]["profile_id"],
        "language": "en",
        "model_size": "1.7B",
        "engine": "qwen",
        "max_chunk_chars": 800,
        "crossfade_ms": 50,
        "normalize": True,
    }

    voicebox_uri = f"{config['voicebox']['url']}/generate/stream"
    with requests.post(
        voicebox_uri, json=payload, timeout=VOICEBOX_TIMEOUT, stream=True
    ) as response:
        response.raise_for_status()
        with open(config["voicebox"]["file_output_path"], "wb") as output_wav:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    output_wav.write(chunk)
    app.logger.info("wrote tts output to %s", config["voicebox"]["file_output_path"])


def parse_config():
    """Parses the program's configuration.

    :return: Parsed configuration
    :rtype: ConfigParser
    """
    config_file_location = os.getenv("AI_JAEDOLPH_CONFIG_FILE", default="./ai_jaedolph.ini")
    app.logger.info("parsing config file from %s", config_file_location)
    config_loader = configparser.ConfigParser()
    config_loader.read(config_file_location)

    # load system prompt from file
    with open(config_loader["gemini"]["system_prompt_file"], "r", encoding="utf-8") as file:
        system_prompt = file.read()
    config_loader.set("gemini", "system_prompt", system_prompt)

    return config_loader


# set up flask app
app = Flask(__name__)

# parse config
config = parse_config()

# setup gemini client
gemini_client = Client(api_key=config["gemini"]["api_key"])

# setup logging
gunicorn_logger = logging.getLogger("gunicorn.error")
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)


# pylint: disable=too-many-return-statements
@app.route("/ask", methods=["POST"])
def ask():
    """Route for asking AI Jaedolph questions.

    :return: json response containing the ai response text
    :rtype: Response
    """

    if not request.is_json:
        return jsonify({"error": "Request payload must be JSON"}), 400

    data = request.get_json()

    # Extract the expected fields
    username = data.get("username")
    encoded_question = data.get("question")

    if not username or not encoded_question:
        return jsonify({"error": "missing 'username' or 'question' in payload"}), 400

    try:
        # Decode the base64 question
        question = base64.b64decode(encoded_question).decode("utf-8")
    except Exception as exp:  # pylint: disable=broad-exception-caught
        # Catch base64 decoding errors
        return jsonify({"error": f"invalid base64 string: {str(exp)}"}), 400

    app.logger.info("answering question from %s: %s", username, question)

    try:
        ai_response = get_ai_response(
            f"the twitch user {username} has asked you this question: {question}"
        )
    except errors.APIError as exp:
        msg = f"error getting a response from gemini {exp}"
        app.logger.error(msg)
        return jsonify({"error": msg}), 500

    try:
        tts = f'{username} asked me: "{question}"\n...\n{ai_response}'
        generate_tts(tts)
    except requests.exceptions.RequestException as exp:
        msg = f"error generating TTS from voicebox {exp}"
        app.logger.error(msg)
        return jsonify({"error": msg}), 500
    except Exception as exp:  # pylint: disable=broad-exception-caught
        msg = f"could not generate TTS {exp}"
        app.logger.error(msg)
        return jsonify({"error": msg}), 500

    return jsonify({"response": ai_response})
