import os
import pyaudio
import wave
import threading
import time
from dotenv import load_dotenv
from openai import OpenAI
import pvcobra
import numpy as np
import tempfile
from datetime import datetime

load_dotenv()

# Constants
CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5  # Record in 5-second segments

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")
SILENCE_DURATION = float(os.getenv("SILENCE_DURATION", "0.4"))

# Global variables
is_listening = True
is_recording = False
frames = []
current_transcription = ""

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Cobra
cobra = pvcobra.create(access_key=PICOVOICE_ACCESS_KEY)

def transcribe_audio(audio_file):
    start_time = time.time()
    with open(audio_file, "rb") as file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=file,
            response_format="text"
        )
    end_time = time.time()
    duration = (end_time - start_time) * 1000  # Convert to milliseconds
    return transcription, duration

def next_process():
    print("Next process")

def process_audio():
    global is_listening, is_recording, frames, current_transcription

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("Listening...")
    
    silence_start = None
    voice_start = None
    segment_start = None

    try:
        while is_listening:
            data = stream.read(CHUNK, exception_on_overflow=False)
            pcm = np.frombuffer(data, dtype=np.int16)
            voice_probability = cobra.process(pcm)

            if voice_probability > 0.5:
                if not is_recording:
                    is_recording = True
                    voice_start = time.time()
                    segment_start = time.time()
                    print("\nVoice detected, recording...")
                    current_transcription = ""
                silence_start = None
                frames.append(data)
            elif is_recording:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= SILENCE_DURATION:
                    is_recording = False
                    print(f"\nSilence detected. Transcribing...")
                    # Transcribe the recorded segment
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                        wf = wave.open(temp_audio.name, 'wb')
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(p.get_sample_size(FORMAT))
                        wf.setframerate(RATE)
                        wf.writeframes(b''.join(frames))
                        wf.close()
                    
                    transcription, duration = transcribe_audio(temp_audio.name)
                    current_transcription += transcription
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    print(f"[{timestamp}] Transcription (took {duration:.2f}ms): {current_transcription}")
                    next_process()
                    
                    os.unlink(temp_audio.name)
                    frames.clear()
                    current_transcription = ""
                    print("\nListening...")
                else:
                    frames.append(data)
            
            # Transcribe every RECORD_SECONDS if continuously recording
            if is_recording and time.time() - segment_start >= RECORD_SECONDS:
                #print("\nTranscribing segment...")
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                    wf = wave.open(temp_audio.name, 'wb')
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(p.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))
                    wf.close()
                
                transcription, duration = transcribe_audio(temp_audio.name)
                current_transcription += transcription
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                #print(f"[{timestamp}] Current transcription (took {duration:.2f}ms): {current_transcription}")
                
                os.unlink(temp_audio.name)
                frames.clear()
                segment_start = time.time()

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

# Start the main processing loop
process_audio()

# Clean up
cobra.delete()

print("Script completed")