# Jarvis NLP Module Design

This document outlines the design for the Natural Language Processing (NLP) module for the Jarvis assistant.

## 1. Overview

The NLP module is responsible for taking raw text input (assumed to be transcribed from voice) and converting it into a structured command that the Jarvis application can understand and act upon.

The initial design focuses on a set of simple commands and aims for a lightweight, cross-platform solution, now incorporating `thefuzz` for improved robustness.

## 2. Core Requirements & Functionality

*   **Input:** A text string (e.g., "Jarvis, open Notepad").
*   **Output:** A dictionary representing the structured command, e.g.:
    ```json
    { "intent": "INTENT_NAME", "params": { "parameterName": "parameterValue" } }
    ```
    If the command is not understood or confidence is too low, it will return `None` or `{ "intent": "unknown", "params": {} }`.
*   **Initial Intents:**
    1.  `openApp`: Opens a specified application.
    2.  `getTime`: Gets the current time.
    3.  `searchWeb`: Searches for a query on the web.
    4.  `checkWeather`: Checks the weather (basic version).

## 3. Chosen Libraries/Tools

*   **Python `re` (Regular Expressions) Module:**
    *   **Usage:** Primary tool for initial, broad matching of command patterns and extracting basic entities (like application names or search queries).
    *   **Reasoning:** Built-in, lightweight, fast, and excellent for structured pattern matching.
*   **`thefuzz` Library (with `rapidfuzz`):**
    *   **Usage:** Used after a regex match to perform intent keyword confirmation. It calculates a similarity score (e.g., using `token_set_ratio`) between the input phrase and predefined keywords for the matched intent. This helps filter out ambiguous matches and improves robustness against variations in user phrasing.
    *   **Reasoning:** Provides fuzzy string matching capabilities, is relatively lightweight, and significantly improves user experience by making command recognition more flexible and less prone to errors from minor phrasing deviations.

## 4. Core NLP Module Architecture

The module will be centered around an `NLPProcessor` class.

### 4.1. Components

*   **`NLPProcessor` Class:**
    *   Manages the overall processing flow.
    *   Initialized with a list of `IntentDefinition` objects/dictionaries and a `keyword_threshold`.
    *   `keyword_threshold` (int, 0-100): Minimum confidence score required from `thefuzz` keyword matching to confirm an intent.
    *   Contains methods for `preprocess`ing text and `process`ing it to find intents.
*   **`IntentDefinition` Structure:**
    *   Each intent will be defined by:
        *   `intent_name` (string): e.g., "openApp".
        *   `regex_pattern` (string): A raw string regular expression to identify the command structure and potentially capture entities.
        *   `entity_keys` (list of strings, optional): Keys for the parameters extracted by regex capturing groups.
        *   `keywords` (list of strings): A list of characteristic phrases or keywords for this intent. Used with `thefuzz` to calculate a confidence score for the matched intent. If empty, the intent relies solely on the regex match.

### 4.2. Data Flow

1.  **Input:** Raw text command.
2.  **Preprocessing:** Convert to lowercase, strip whitespace.
3.  **Intent Matching Loop:**
    *   Iterate through each `IntentDefinition`.
    *   Attempt to match the `regex_pattern` against the preprocessed text.
    *   If a regex match occurs:
        *   If the intent definition includes `keywords`:
            *   Calculate a confidence score by comparing the input text to the intent's `keywords` using `thefuzz.token_set_ratio`.
            *   If the highest score obtained is below the `NLPProcessor`'s `keyword_threshold`, the match is considered low-confidence, and the system proceeds to the next `IntentDefinition`.
        *   If the regex match is accepted (either no keywords to check or keyword score is sufficient):
            *   Extract entities using regex capturing groups if `entity_keys` are provided.
            *   Format and return the structured command dictionary.
4.  **No Match:** If no intent is confidently matched after checking all definitions, return an indication that the command was not understood.

### 4.3. Conceptual Python Structure

```python
import re
from thefuzz import fuzz # Import fuzz

class NLPProcessor:
    def __init__(self, intent_definitions: list[dict], keyword_threshold: int = 75): # Added keyword_threshold
        self.intent_definitions = intent_definitions
        self.keyword_threshold = keyword_threshold # Store threshold
        for intent_def in self.intent_definitions:
            intent_def["compiled_regex"] = re.compile(
                intent_def["regex_pattern"],
                re.IGNORECASE
            )
            intent_def.setdefault("keywords", []) # Ensure keywords list exists

    def preprocess(self, text: str) -> str:
        return text.lower().strip()

    def process(self, text: str) -> dict | None:
        processed_text = self.preprocess(text)
        if not processed_text:
            return None

        for intent_def in self.intent_definitions:
            match = intent_def["compiled_regex"].match(processed_text)
            if match:
                # Keyword confidence check
                if intent_def["keywords"]:
                    max_score = 0
                    for kw in intent_def["keywords"]:
                        score = fuzz.token_set_ratio(processed_text, kw) # Example scoring
                        if score > max_score:
                            max_score = score
                    if max_score < self.keyword_threshold:
                        continue # Low confidence, try next intent

                # Parameter extraction
                params = {}
                if "entity_keys" in intent_def and match.groups():
                    actual_groups = [g for g in match.groups() if g is not None]
                    for i, key in enumerate(intent_def["entity_keys"]):
                        if i < len(actual_groups):
                            params[key] = actual_groups[i].strip()

                return {"intent": intent_def["intent_name"], "params": params}

        return None

# Example Intent Definitions (in README.md):
# intent_definitions = [
#     {
#         "intent_name": "openApp",
#         "regex_pattern": r"^(?:jarvis\s)?(?:please\s)?(?:open|launch|start)\s+([\w\s.-]+)", # Regex updated
#         "entity_keys": ["appName"],
#         "keywords": ["open app", "launch application", "start this app", "open"] # Example keywords
#     },
#     {
#         "intent_name": "getTime",
#         "regex_pattern": r"^(?:jarvis\s)?(?:.*\b(time|what time|current time)\b.*)",
#         "entity_keys": [],
#         "keywords": ["what time is it", "what is the current time", "tell me the time"]
#     },
#     {
#         "intent_name": "searchWeb",
#         "regex_pattern": r"^(?:jarvis\s)?(?:search for|search|find|look up)\s+(.+)", # Regex updated
#         "entity_keys": ["query"],
#         "keywords": ["search the web for", "find on internet", "look up online", "search", "find"]
#     },
#     {
#         "intent_name": "checkWeather",
#         "regex_pattern": r"^(?:jarvis\s)?(?:.*\b(weather|forecast)\b.*)",
#         "entity_keys": [],
#         "keywords": ["how is the weather", "weather forecast today", "is it raining outside", "temperature check", "weather conditions"]
#     }
# ]
```

## 5. Wake Word & Application State

*   **Wake Word ("Jarvis"):** The NLP module assumes that it is activated *after* a dedicated wake word engine detects "Jarvis". The regex patterns include "jarvis" to align with this, assuming the wake word might be part of the transcribed string passed to this module.
*   **Application State:** The broader Jarvis application will manage transitioning between listening for the wake word, actively processing commands (using this NLP module), and then returning to wake word listening mode.

## 6. Future Enhancements

*   Loading intent definitions from a configuration file (JSON/YAML).
*   More sophisticated intent disambiguation if commands become complex (e.g., if multiple regexes match, pick the one with highest keyword score).
*   More advanced use of `thefuzz` for entity normalization against known lists (e.g., correcting misspelled application names).
*   Context management for follow-up commands.
*   Integration with more advanced NLP libraries (NLTK, spaCy) if complexity significantly increases beyond regex and basic fuzzy matching."# Jarvis_May" 
