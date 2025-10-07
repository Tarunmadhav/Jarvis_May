import datetime
import webbrowser
import urllib.parse
import openai
import os # For API key management in production

# --- IMPORTANT SECURITY NOTE ---
# The API key is hardcoded here FOR SUBTASK TESTING ONLY in an isolated environment.
# In a real application, NEVER hardcode API keys. Use environment variables
# or a secure configuration management system.
# Example for real use: OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free"

def get_current_time(params: dict) -> str:
    """
    Retrieves the current time and formats it into a user-friendly string.
    Params is unused but included for consistent skill signature.
    """
    now = datetime.datetime.now()
    formatted_time = now.strftime("%I:%M %p")
    return f"The current time is {formatted_time}."

def open_application(params: dict) -> str:
    """
    Opens specific web services (YouTube, Spotify) or returns a placeholder
    message for other application names.
    """
    app_name_original = params.get('appName')
    if not app_name_original:
        return "No application name specified for opening."

    app_name_lower = app_name_original.lower()
    url_to_open = None
    message = f"Attempting to open {app_name_original}..."

    if app_name_lower == "youtube":
        url_to_open = "https://www.youtube.com"
        message = "Opening YouTube..."
    elif app_name_lower == "spotify":
        url_to_open = "https://open.spotify.com"
        message = "Opening Spotify..."

    if url_to_open:
        try:
            webbrowser.open_new_tab(url_to_open)
            return message
        except Exception as e:
            print(f"Error opening web browser for {app_name_original}: {e}")
            return f"Sorry, I encountered an error trying to open {app_name_original}."
    else:
        return message

def search_web(params: dict) -> str:
    """
    Performs a web search using the default browser.
    """
    query = params.get('query')
    if not query:
        return "You didn't specify what to search for."
    try:
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        webbrowser.open_new_tab(search_url)
        return f"Searching the web for '{query}'..."
    except Exception as e:
        print(f"Error opening web browser for search: {e}")
        return f"Sorry, I encountered an error trying to search for '{query}'."

def check_weather_skill(params: dict) -> str:
    """
    Placeholder skill for checking the weather.
    """
    return "Fetching the latest weather forecast for you."

def play_media(params: dict) -> str:
    """
    Opens a web browser to search for the specified media title on a
    streaming service (YouTube by default or Spotify if specified).
    """
    media_title = params.get('mediaTitle')
    media_service_input = params.get('mediaService')
    if not media_title:
        return "You need to specify what song or video you want to play."
    encoded_media_title = urllib.parse.quote_plus(media_title)
    service_name_for_message = "YouTube (default)"
    search_url = f"https://www.youtube.com/results?search_query={encoded_media_title}"
    if media_service_input:
        service_lower = media_service_input.lower()
        if "youtube" in service_lower:
            service_name_for_message = "YouTube"
        elif "spotify" in service_lower:
            service_name_for_message = "Spotify"
            search_url = f"https://open.spotify.com/search/{encoded_media_title}"
    try:
        webbrowser.open_new_tab(search_url)
        return f"Searching for '{media_title}' on {service_name_for_message}..."
    except Exception as e:
        print(f"Error opening web browser for media: {e}")
        return f"Sorry, I encountered an error trying to play '{media_title}' on {service_name_for_message}."

def query_text_file(params: dict) -> str:
    """
    Reads a text file (now including .md, .py, .json, .csv) and uses an LLM
    via OpenRouter to answer a question about it or summarize it.
    """
    file_path = params.get('filePath')
    query_text = params.get('queryText') # Optional

    if not file_path:
        return "You need to specify the path to the file."

    # Updated list of allowed extensions
    ALLOWED_EXTENSIONS = (".txt", ".md", ".py", ".json", ".csv")
    if not file_path.lower().endswith(ALLOWED_EXTENSIONS):
        return f"Sorry, I can only analyze files with extensions: {', '.join(ALLOWED_EXTENSIONS)}." # Updated message

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except FileNotFoundError:
        return f"Sorry, I couldn't find the file: {file_path}"
    except UnicodeDecodeError:
        return f"Sorry, I had trouble reading the file '{file_path}'. It might not be a plain text file or has an unsupported encoding."
    except IOError as e:
        return f"Sorry, I encountered an error reading the file '{file_path}': {e}"

    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY_HERE":
        return "API key for OpenRouter is not configured. I cannot analyze the file."

    try:
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

        if query_text:
            prompt = f"Based on the following document content retrieved from the file '{file_path}':\n\n---\n{file_content}\n---\n\nPlease answer this question: {query_text}"
        else:
            prompt = f"Please summarize the key points of the following document retrieved from the file '{file_path}':\n\n---\n{file_content}\n---"

        MAX_PROMPT_CHARS = 15000
        if len(prompt) > MAX_PROMPT_CHARS:
             return f"The content of '{file_path}' (plus your query, if any) is too long for me to process (over {MAX_PROMPT_CHARS} characters). Please try with a smaller file or a more specific query."

        completion = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes documents and code. If analyzing code, provide explanations or summaries as if to a fellow programmer. If analyzing data like JSON or CSV, describe its structure or summarize its content."}, # Enhanced system prompt
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=700 # Increased max_tokens
        )
        llm_response = completion.choices[0].message.content
        return llm_response if llm_response else f"I received an empty response from the AI for your query about '{file_path}'." # Context in empty response

    except openai.AuthenticationError:
        return "Sorry, there's an issue with the AI service authentication. Please check the API key."
    except openai.RateLimitError:
        return "Sorry, I've made too many requests to the AI service recently. Please try again later."
    except openai.APIConnectionError:
        return "Sorry, I couldn't connect to the AI service. Please check your internet connection."
    except openai.APIStatusError as e:
        print(f"OpenRouter API Status Error for '{file_path}': {e.status_code} - {e.response}") # Context
        return f"Sorry, the AI service reported an error ({e.status_code}) while processing '{file_path}'." # Context
    except openai.APIError as e:
        print(f"OpenRouter API Error for '{file_path}': {e}") # Context
        return f"Sorry, I encountered an error with the AI service while processing '{file_path}': {str(e)}" # Context
    except Exception as e:
        print(f"An unexpected error occurred while querying the LLM for '{file_path}': {e}") # Context
        return f"Sorry, an unexpected error occurred while trying to analyze '{file_path}'."

SKILL_REGISTRY = {
    "getTime": get_current_time,
    "openApp": open_application,
    "searchWeb": search_web,
    "checkWeather": check_weather_skill,
    "playMedia": play_media,
    "queryFile": query_text_file,
}
