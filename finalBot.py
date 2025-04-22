import discord
import asyncio
import logging
import os
import time
import json
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)

# Discord bot token (replace this with a NEW token!)
TOKEN = 'Insert Bot Token Here'

# Define intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize Discord client
client = discord.Client(intents=intents)

# Functions
def model_req(payload=None):
    try:
        url = "http://localhost:11434/api/generate"
        api_key = os.getenv('API_KEY', None)
        delta = response = None

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        print(payload)

        start_time = time.time()
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        delta = time.time() - start_time

        if response.status_code == 200:
            response_json = response.json()
            result = ""
            if 'response' in response_json:
                result = response_json['response']
            elif 'choices' in response_json:
                result = response_json['choices'][0]['message']['content']
            else:
                result = response_json
            return round(delta, 3), result
        elif response.status_code == 401:
            return -1, f"!!ERROR!! Authentication issue. Check API_KEY ({url})"
        else:
            return -1, f"!!ERROR!! HTTP {response.status_code}, {response.text}"
    except Exception as e:
        return -1, f"!!ERROR!! {str(e)}"

def create_payload(model, prompt, target="ollama", **kwargs):
    if target == "ollama":
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if kwargs:
            payload["options"] = {key: value for key, value in kwargs.items()}
        return payload
    else:
        print(f'!!ERROR!! Unknown target: {target}')
        return None

# Function to generate response using ollama
async def generate_response(prompt: str) -> str:
    payload = create_payload(
        target="ollama",
        model="llama3.2",
        prompt=prompt,
        temperature=0.7,
        num_ctx=2048,
        num_predict=300
    )
    _, response = model_req(payload=payload)
    return response

# Event: Bot is ready
@client.event
async def on_ready():
    logging.info(f'✅ Logged in as {client.user} (ID: {client.user.id})')
    logging.info('------')

# Event: Message received
@client.event
async def on_message(message):
    print("Received message:", message.content)

    if message.author == client.user:
        return

    content = message.content.replace(f'<@{client.user.id}>', '').strip()

    if content.startswith('!ask'):
        question = content[4:].strip()
        if question:
            await message.channel.send("🧠 Processing your question...")
            prompt = f"Provide a detailed explanation for the following chemistry question:\n{question}"
            response = await generate_response(prompt)
            await message.channel.send(response)
        else:
            await message.channel.send("❗ Please provide a question. Usage: `!ask [your question]`")

    elif content.startswith('!summarize'):
        study_text = content[10:].strip()
        if study_text:
            await message.channel.send("📚 Summarizing your study material...")
            prompt = f"Summarize the following chemistry study material:\n{study_text}"
            response = await generate_response(prompt)
            await message.channel.send(response)
        else:
            await message.channel.send("❗ Please provide text. Usage: `!summarize [your text]`")

    elif content.startswith('!quiz'):
        topic = content[5:].strip()
        if topic:
            await message.channel.send(f"📝 Generating a quiz on: **{topic}**")
            prompt = (
                f"Create a multiple-choice quiz with 3 questions on the topic '{topic}'. "
                "Each question should have 4 options labeled A-D, and indicate the correct answer."
            )
            response = await generate_response(prompt)
            await message.channel.send(response)
        else:
            await message.channel.send("❗ Please specify a topic. Usage: `!quiz [topic]`")

    elif content.startswith('!help'):
        help_text = (
            "🤖 **Chemistry Study Assistant Bot Commands:**\n"
            "`!ask [question]` - Ask a chemistry-related question.\n"
            "`!summarize [text]` - Summarize study material.\n"
            "`!quiz [topic]` - Generate a quiz on a specific topic.\n"
            "`!help` - Show this message."
        )
        await message.channel.send(help_text)

# Run the bot
if __name__ == '__main__':
    client.run(TOKEN)
