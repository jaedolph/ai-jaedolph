# AI Jaedolph

AI chatbot with TTS used for [Jaedolph's stream](www.twitch.tv/jaedolph).

Relies on the following components:
- Google Gemini - for the AI response generation
- [Voicebox](https://github.com/jamiepine/voicebox) - for TTS

## Config
Example config file is found [here](ai_jaedolph.ini.example)

The system prompt used for AI Jaedolph is included [here](ai_jaedolph_system_prompt.txt) and can be modified.

## Run with podman

Create config files in your home directory.

Fix rootless permissions on output directory:
```
podman unshare chown -R 1001:0 ~/tts_output/
```

Run the container:
```
podman run \
    -d \
    --name ai-jaedolph \
    -v ~/ai_jaedolph.ini:/usr/src/app/ai_jaedolph.ini:Z \
    -v ~/ai_jaedolph_system_prompt.txt:/usr/src/app/ai_jaedolph_system_prompt.txt:Z \
    -v ~/tts_output:/tts_output:z \
    -p 127.0.0.1:8001:8001 \
    docker.io/jaedolph/ai-jaedolph:latest
```

## Development

Run tox tests:
```
tox
```

Run the server with gunicorn
```
python3 -m venv venv
./venv/bin/activate
pip install -e .
export GUNICORN_CMD_ARGS="\
    --bind 0.0.0.0:8001 \
    --workers 1 \
    --threads 1 \
    --timeout 180 \
    --access-logfile -\
    --error-logfile -"
gunicorn ai_jaedolph:app
```

Test with curl request:
```
QUESTION_B64=$(echo -n "What is your favourite build order in starcraft?" | base64 -w0)
curl localhost:8001/ask
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"username": "testuser", "question": "'${QUESTION_B64}'"}'
```

Test audio:
```
xdg-open tts_output.wav
```
