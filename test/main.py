# main.py
from desktopassitant import cmd
from emailassistant import email
from musicandnewsAI import ink
from virassitant import vir
from voice_translator import voice


import speech_recognition as sr

def start_listening():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening... Say something:")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        recognized_text = recognizer.recognize_google(audio)
        print("You said:", recognized_text)
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand what you said.")
    except sr.RequestError as e:
        print("Error with the voice recognition service; {0}".format(e))

if __name__ == "__main__":
    while True:
        command = input("Say 'jarvis' to start voice recognition or any other word to terminate: ")
        
        if command.lower() == "jarvis":
            start_listening()
            cmd()
            email()
            ink()
            vir()
            voice()
    
            instance = vir()
            instance.method()
        else:
            print("Terminating...")
            break
