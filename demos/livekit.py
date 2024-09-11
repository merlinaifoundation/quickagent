import os
import asyncio
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, openai, silero
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def entrypoint(ctx: JobContext):
    # Create an initial chat context with a system prompt
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are Merlin the Wizard. "
            "Your interface with users will be voice. "
            "Keep your responses short and concise, avoiding unpronounceable punctuation."
        ),
    )

    # Connect to the LiveKit room, subscribing only to audio
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Create the VoiceAssistant
    assistant = VoiceAssistant(
        vad=silero.VAD.load(min_silence_duration=float(os.getenv('SILENCE_DURATION', 0.5))),
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o"),
        tts=openai.TTS(voice="onyx"),
        chat_ctx=initial_ctx,
    )

    # Start the voice assistant
    assistant.start(ctx.room)

    print("Agent is ready. Type your messages and press Enter to simulate speech input.")
    print("Type 'quit' to exit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break

        # Process the user input as if it was speech
        response = await assistant.process_speech(user_input)
        
        # Print the agent's response
        print(f"Agent: {response}")

    print("Exiting the agent.")

if __name__ == "__main__":
    # Initialize the worker with the entrypoint
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))



'''
https://agents-playground.livekit.io/
'''