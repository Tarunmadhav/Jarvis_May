import sys
import pyttsx3
import json # Added import for json

try:
    from jarvis_nlp.nlp_processor import NLPProcessor
except ImportError:
    sys.path.append('jarvis_nlp')
    try:
        from nlp_processor import NLPProcessor
    except ImportError as e:
        print(f"Failed to import NLPProcessor even after path adjustment: {e}")
        sys.exit(1)

try:
    from jarvis_skills.skills import SKILL_REGISTRY
except ImportError as e:
    print(f"Warning: Could not import SKILL_REGISTRY from jarvis_skills.skills ({e}). Skills will not work.")
    SKILL_REGISTRY = {}

# Removed hardcoded APP_INTENT_DEFINITIONS

def load_intent_definitions(filepath: str = "intent_definitions.json") -> list:
    """
    Loads intent definitions from a JSON file.
    Handles FileNotFoundError and json.JSONDecodeError.
    Returns an empty list if loading fails.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            intent_definitions = json.load(f)
        if not isinstance(intent_definitions, list):
            print(f"Error: Intent definitions file '{filepath}' does not contain a valid JSON list.")
            return []
        return intent_definitions
    except FileNotFoundError:
        print(f"Error: Intent definitions file '{filepath}' not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from '{filepath}': {e}")
        return []
    except Exception as e: # Catch any other unexpected errors during loading
        print(f"An unexpected error occurred while loading intent definitions from '{filepath}': {e}")
        return []

tts_engine = None

def speak(text_to_speak: str):
    if tts_engine:
        print(f"Jarvis (speaking): {text_to_speak}")
        tts_engine.say(text_to_speak)
        tts_engine.runAndWait()
    else:
        print(f"Jarvis (TTS not ready): {text_to_speak}")

def main():
    global tts_engine
    print("Initializing Jarvis...")
    try:
        tts_engine = pyttsx3.init()
    except Exception as e:
        print(f"Error initializing TTS engine: {e}. Jarvis will be silent.")

    speak("Jarvis initializing.")

    app_intent_definitions = load_intent_definitions()
    if not app_intent_definitions:
        error_msg = "Failed to load intent definitions. Jarvis cannot understand commands."
        print(error_msg)
        if tts_engine: speak(error_msg)
        return # Exit if definitions failed to load

    try:
        nlp_processor = NLPProcessor(app_intent_definitions, keyword_threshold=75)
        speak("Natural Language Processor initialized. Ready for commands.")
    except Exception as e:
        error_msg = f"Critical Error initializing NLPProcessor: {e}. Jarvis cannot operate."
        print(error_msg)
        if tts_engine: speak(error_msg)
        return

    while True:
        try:
            user_input = input("You: ")
        except EOFError:
            print("\nJarvis: Exiting...")
            if tts_engine: speak("Exiting now.")
            break
        except KeyboardInterrupt:
            print("\nJarvis: Exiting...")
            if tts_engine: speak("Exiting now.")
            break

        if user_input.lower() in ["quit", "exit"]:
            goodbye_msg = "Goodbye!"
            print(f"Jarvis: {goodbye_msg}")
            if tts_engine: speak(goodbye_msg)
            break

        if not user_input:
            continue

        try:
            result = nlp_processor.process(user_input)
        except Exception as e:
            error_msg = f"An error occurred during NLP processing: {e}"
            print(f"Jarvis: {error_msg}")
            if tts_engine: speak(error_msg)
            result = None

        response_message = None
        if result:
            intent = result['intent']
            params = result['params']

            if intent in SKILL_REGISTRY:
                skill_function = SKILL_REGISTRY[intent]
                try:
                    response_message = skill_function(params)
                except Exception as e:
                    error_msg = f"Error executing skill '{intent}': {e}"
                    print(f"Jarvis: {error_msg}")
                    if tts_engine: speak(error_msg)
                    response_message = "I had trouble performing that action."
            else:
                response_message = f"I understood your intent is '{intent}' with parameters {params}, but I don't have a specific skill for that yet."
        else:
            response_message = "Sorry, I didn't understand that."

        if response_message is None:
            response_message = "I encountered an unexpected issue."

        print(f"Jarvis: {response_message}")
        if tts_engine: speak(response_message)

if __name__ == '__main__':
    main()
