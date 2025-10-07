import re
from thefuzz import fuzz

class NLPProcessor:
    """
    Processes text input to identify intents and extract parameters.
    It uses regular expressions for initial pattern matching and `thefuzz` library
    for keyword-based confidence scoring to improve robustness.
    """
    def __init__(self, intent_definitions: list[dict], keyword_threshold: int = 75):
        """
        Initializes the NLPProcessor.

        Args:
            intent_definitions: A list of dictionaries, where each dictionary
                                defines an intent. Expected keys are:
                                - "intent_name": str, the unique name of the intent.
                                - "regex_pattern": str, the regex pattern to match the command structure.
                                - "entity_keys": list[str] (optional), keys for parameters
                                                 extracted by regex capturing groups.
                                - "keywords": list[str] (optional), a list of characteristic phrases or
                                              keywords for this intent. Used for fuzzy matching
                                              to confirm intent if regex is matched. If empty or
                                              not provided, intent relies solely on regex.
            keyword_threshold: int (0-100), the minimum `thefuzz.token_set_ratio` score
                               required for a keyword match to be considered valid.
                               Only applicable if keywords are provided for an intent.
        """
        if not intent_definitions:
            raise ValueError("Intent definitions list cannot be empty.")
        if not (0 <= keyword_threshold <= 100):
            raise ValueError("Keyword threshold must be between 0 and 100.")

        self.intent_definitions = intent_definitions
        self.keyword_threshold = keyword_threshold

        for intent_def in self.intent_definitions:
            # Validate essential keys
            if not all(k in intent_def for k in ["intent_name", "regex_pattern"]):
                raise ValueError(
                    f"Intent definition missing 'intent_name' or 'regex_pattern': {intent_def}"
                )

            # Ensure 'keywords' is a list if present, default to empty list otherwise
            if "keywords" in intent_def and not isinstance(intent_def["keywords"], list):
                raise ValueError(
                    f"Keywords for intent '{intent_def['intent_name']}' must be a list."
                )
            intent_def.setdefault("keywords", [])

            # Pre-compile regex for efficiency
            try:
                intent_def["compiled_regex"] = re.compile(
                    intent_def["regex_pattern"],
                    re.IGNORECASE
                )
            except re.error as e:
                raise ValueError(
                    f"Invalid regex pattern for intent '{intent_def['intent_name']}': {e}"
                )

    def preprocess(self, text: str) -> str:
        """
        Basic preprocessing of the input text.
        Converts to lowercase and strips leading/trailing whitespace.
        """
        if not isinstance(text, str):
            return ""
        return text.lower().strip()

    def process(self, text: str) -> dict | None:
        """
        Processes the input text to identify an intent and extract parameters.

        The process involves:
        1. Preprocessing the text.
        2. Iterating through defined intents:
            a. Matching the text against the intent's regex pattern.
            b. If regex matches and the intent has keywords:
                i. Calculate a confidence score using `thefuzz.token_set_ratio`
                   between the processed text and each keyword phrase.
                ii. If the maximum keyword score is below `self.keyword_threshold`,
                    this match is considered low-confidence, and the processor
                    moves to the next intent definition.
            c. If regex matches and (no keywords are defined OR keyword score is sufficient):
                i. Extract parameters using regex capturing groups and `entity_keys`.
                ii. Return the structured command (intent name and parameters).
        3. If no intent is confidently matched, return None.

        Args:
            text: The input text string from the user.

        Returns:
            A dictionary with "intent" and "params" if a match is found,
            e.g., {"intent": "openApp", "params": {"appName": "Notepad"}}.
            Returns None if no intent is matched or confidence is too low.
        """
        processed_text = self.preprocess(text)
        if not processed_text:
            return None

        for intent_def in self.intent_definitions:
            match = intent_def["compiled_regex"].match(processed_text)

            if match:
                # If intent has keywords, perform fuzzy keyword matching for confidence
                if intent_def["keywords"]:
                    max_keyword_score = 0
                    for keyword_phrase in intent_def["keywords"]:
                        # Compare the whole processed text against each keyword phrase
                        score = fuzz.token_set_ratio(processed_text, keyword_phrase.lower())
                        if score > max_keyword_score:
                            max_keyword_score = score

                    # If keyword confidence is below threshold, discard this regex match
                    if max_keyword_score < self.keyword_threshold:
                        continue # Try next intent definition

                # If we reach here, either no keywords were needed, or keyword check passed
                params = {}
                entity_keys = intent_def.get("entity_keys", [])
                if not isinstance(entity_keys, (list, tuple)): # Should be caught by init, but defensive
                    entity_keys = []

                # Get all non-None captured groups from the regex match
                actual_groups = [g for g in match.groups() if g is not None]

                if entity_keys and actual_groups:
                    for i, key in enumerate(entity_keys):
                        if i < len(actual_groups):
                            params[key] = actual_groups[i].strip()
                        else:
                            # This case means not enough groups were captured for all entity_keys
                            params[key] = None # Or raise an error, or omit the key

                return {"intent": intent_def["intent_name"], "params": params}

        return None # Command not understood or no match met criteria

# Reflects the definitions used in successful testing from the previous subtask.
UPDATED_EXAMPLE_INTENT_DEFINITIONS = [
    {
        "intent_name": "openApp",
        "regex_pattern": r"^(?:jarvis\s)?(?:please\s)?(?:open|launch|start)\s+([\w\s.-]+)",
        "entity_keys": ["appName"],
        "keywords": ["open app", "launch application", "start this app", "open"]
    },
    {
        "intent_name": "getTime",
        "regex_pattern": r"^(?:jarvis\s)?(?:.*\b(time|what time|current time)\b.*)",
        "entity_keys": [],
        "keywords": ["what time is it", "what is the current time", "tell me the time"]
    },
    {
        "intent_name": "searchWeb",
        "regex_pattern": r"^(?:jarvis\s)?(?:search for|search|find|look up)\s+(.+)",
        "entity_keys": ["query"],
        "keywords": ["search the web for", "find on internet", "look up online", "search", "find"]
    },
    {
        "intent_name": "checkWeather",
        "regex_pattern": r"^(?:jarvis\s)?(?:.*\b(weather|forecast)\b.*)",
        "entity_keys": [],
        "keywords": ["how is the weather", "weather forecast today", "is it raining outside", "temperature check", "weather conditions"]
    }
]

if __name__ == '__main__':
    processor = NLPProcessor(UPDATED_EXAMPLE_INTENT_DEFINITIONS, keyword_threshold=75)

    test_phrases = [
        "Jarvis open Notepad.exe",
        "please start my app",
        "jarvis what time is it",
        "What's the current time please?",
        "jarvis search for latest AI news",
        "look up python tutorials online",
        "jarvis weather", # Will be filtered by threshold 75 (score 67)
        "forecast today",
        "show weather conditions", # Will pass (score 100)
        "open something",
        "show me the time", # Will pass (score 81)
        "search the internet for cats",
        "jarvis, what is the temperature today", # No regex match (no "weather" or "forecast")
        "tell me a joke",
        "jarvis open", # Fails regex (needs appName)
        "search for", # Regex matches, query "for", keywords should confirm "search"
        "just some random words",
        "book a flight",
    ]

    print(f"Using Keyword Threshold: {processor.keyword_threshold}\n")

    for phrase in test_phrases:
        result = processor.process(phrase)
        if result:
            print(f"Input: \"{phrase}\" -> Intent: {result['intent']}, Params: {result['params']}")
        else:
            print(f"Input: \"{phrase}\" -> Command not understood")

    print("\n--- Testing different thresholds for 'show weather conditions' ---")
    test_phrase_threshold = "show weather conditions"

    processor_low_thresh = NLPProcessor(UPDATED_EXAMPLE_INTENT_DEFINITIONS, keyword_threshold=50)
    print(f"\nUsing Keyword Threshold: {processor_low_thresh.keyword_threshold}")
    result_low = processor_low_thresh.process(test_phrase_threshold)
    print(f"Input: \"{test_phrase_threshold}\" (low thresh) -> {result_low}")

    processor_high_thresh = NLPProcessor(UPDATED_EXAMPLE_INTENT_DEFINITIONS, keyword_threshold=90)
    print(f"\nUsing Keyword Threshold: {processor_high_thresh.keyword_threshold}")
    result_high = processor_high_thresh.process(test_phrase_threshold)
    print(f"Input: \"{test_phrase_threshold}\" (high thresh) -> {result_high}")

    print("\n--- Testing different thresholds for 'jarvis weather' ---")
    test_phrase_weather = "jarvis weather"
    print(f"\nUsing Keyword Threshold: {processor_low_thresh.keyword_threshold}") #50
    result_low_jw = processor_low_thresh.process(test_phrase_weather)
    print(f"Input: \"{test_phrase_weather}\" (low thresh) -> {result_low_jw}")

    print(f"\nUsing Keyword Threshold: {processor.keyword_threshold}") # Default 75
    result_75_jw = processor.process(test_phrase_weather)
    print(f"Input: \"{test_phrase_weather}\" (75 thresh) -> {result_75_jw}")

    print(f"\nUsing Keyword Threshold: {processor_high_thresh.keyword_threshold}") #90
    result_high_jw = processor_high_thresh.process(test_phrase_weather)
    print(f"Input: \"{test_phrase_weather}\" (high thresh) -> {result_high_jw}")

    try:
        NLPProcessor([], keyword_threshold=101)
    except ValueError as e:
        print(f"\nError with invalid threshold: {e}")
    try:
        NLPProcessor(UPDATED_EXAMPLE_INTENT_DEFINITIONS, keyword_threshold=-1)
    except ValueError as e:
        print(f"Error with invalid threshold: {e}")
    try:
        NLPProcessor([{"intent_name": "t", "regex_pattern": r".", "keywords": "not a list"}])
    except ValueError as e:
        print(f"Error with invalid keywords type: {e}")
