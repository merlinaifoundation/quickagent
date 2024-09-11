import pyaudio
import wave
import numpy as np
import pveagle
import os
import json
from dotenv import load_dotenv
import warnings

# Suprimir advertencias de ALSA
warnings.filterwarnings("ignore", category=RuntimeWarning, module="sounddevice")

# Cargar variables de entorno
load_dotenv()

# Configuración de audio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 512  # Cambiado a 512 para coincidir con el requerimiento de Eagle
RECORD_SECONDS = 5

# Inicializar PyAudio
audio = pyaudio.PyAudio()

# Función para grabar audio
def record_audio():
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    
    print("Presiona Enter para comenzar a grabar...")
    input()
    print("Grabando...")
    
    frames = []
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    
    print("Grabación finalizada.")
    
    stream.stop_stream()
    stream.close()
    
    return b''.join(frames)

# Función para enrollar un hablante
def enroll_speaker(access_key, speaker_name):
    try:
        eagle_profiler = pveagle.create_profiler(access_key)
        
        percentage = 0.0
        while percentage < 100.0:
            audio_data = record_audio()
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            percentage, feedback = eagle_profiler.enroll(audio_array)
            print(f"Progreso de enrollment: {percentage:.2f}% - {feedback.name}")
        
        speaker_profile = eagle_profiler.export()
        eagle_profiler.delete()
        
        profile_data = {
            "name": speaker_name,
            "profile": speaker_profile.to_bytes().hex()
        }
        
        with open(f"{speaker_name}_profile.json", "w") as f:
            json.dump(profile_data, f)
        
        print(f"Perfil de {speaker_name} guardado.")
    except Exception as e:
        print(f"Error durante el enrollment: {str(e)}")

# Función para reconocer hablantes
def recognize_speaker(access_key, profile_paths):
    try:
        profiles = []
        for path in profile_paths:
            with open(path, "r") as f:
                profile_data = json.load(f)
                profile_bytes = bytes.fromhex(profile_data["profile"])
                profile = pveagle.EagleProfile.from_bytes(profile_bytes)
                profiles.append(profile)
        
        eagle = pveagle.create_recognizer(access_key, profiles)
        
        print("Presiona Enter para comenzar el reconocimiento (presiona Ctrl+C para detener)...")
        input()
        
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)
        
        print("Escuchando...")
        while True:
            audio_data = stream.read(CHUNK)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            scores = eagle.process(audio_array)
            
            max_score = max(scores)
            if max_score > 0.7:  # Umbral de confianza
                speaker_index = scores.index(max_score)
                speaker_name = os.path.basename(profile_paths[speaker_index]).replace("_profile.json", "")
                print(f"Hablante detectado: {speaker_name} (confianza: {max_score:.2f})")
    
    except KeyboardInterrupt:
        print("Reconocimiento detenido.")
    except Exception as e:
        print(f"Error durante el reconocimiento: {str(e)}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        if 'eagle' in locals():
            eagle.delete()

# Función principal
def main():
    access_key = os.getenv("PICOVOICE_ACCESS_KEY")
    if not access_key:
        print("Por favor, configura la variable de entorno PICOVOICE_ACCESS_KEY")
        return
    
    while True:
        print("\n1. Enrollar nuevo hablante")
        print("2. Realizar reconocimiento")
        print("3. Salir")
        choice = input("Elige una opción: ")
        
        if choice == "1":
            speaker_name = input("Ingresa el nombre del hablante: ")
            enroll_speaker(access_key, speaker_name)
        elif choice == "2":
            profile_paths = [f for f in os.listdir() if f.endswith("_profile.json")]
            if not profile_paths:
                print("No hay perfiles de hablantes. Por favor, enrolla al menos un hablante primero.")
            else:
                recognize_speaker(access_key, profile_paths)
        elif choice == "3":
            break
        else:
            print("Opción no válida. Intenta de nuevo.")
    
    audio.terminate()

if __name__ == "__main__":
    main()