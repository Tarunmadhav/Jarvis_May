import unittest
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jarvis_nlp.nlp_processor import NLPProcessor

def load_test_intent_definitions(filepath: str = "intent_definitions.json") -> list:
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        definitions_path = os.path.join(base_dir, filepath)
        with open(definitions_path, 'r', encoding='utf-8') as f:
            intent_definitions = json.load(f)
        if not isinstance(intent_definitions, list):
            raise ValueError(f"Test Error: Intent definitions file '{definitions_path}' does not contain a valid JSON list.")
        return intent_definitions
    except FileNotFoundError:
        raise FileNotFoundError(f"Test Error: Intent definitions file '{definitions_path}' not found.")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Test Error: Error decoding JSON from '{definitions_path}': {e.msg}", e.doc, e.pos)
    except Exception as e:
        raise Exception(f"Test Error: An unexpected error occurred while loading intent definitions from '{definitions_path}': {e}")

class TestNLPProcessor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.intent_definitions = load_test_intent_definitions()
        if not cls.intent_definitions:
            raise unittest.SkipTest("Intent definitions could not be loaded; skipping NLPProcessor tests.")

    def setUp(self):
        self.default_threshold = 75
        self.processor = NLPProcessor(self.__class__.intent_definitions, keyword_threshold=self.default_threshold)
        self.lenient_processor = NLPProcessor(self.__class__.intent_definitions, keyword_threshold=60)

    def test_preprocess(self):
        self.assertEqual(self.processor.preprocess("  TeSt PhRaSe  "), "test phrase")
        self.assertEqual(self.processor.preprocess(123), "")

    def test_open_app_intent(self):
        passing_phrases = {
            "jarvis open Notepad.exe": {"appName": "notepad.exe"},
            "please start my app launcher": {"appName": "my app launcher"},
            "open VS Code": {"appName": "vs code"},
        }
        for phrase, expected_params in passing_phrases.items():
            with self.subTest(phrase=phrase, type="passing"):
                result = self.processor.process(phrase)
                self.assertIsNotNone(result, f"Phrase '{phrase}' failed.")
                if result:
                    self.assertEqual(result["intent"], "openApp")
                    self.assertEqual(result["params"], expected_params)

    def test_get_time_intent(self):
        passing_phrases = [
            "jarvis what time is it",
            "What's the current time please?",
            "show me the time"
        ]
        for phrase in passing_phrases:
            with self.subTest(phrase=phrase, type="passing"):
                result = self.processor.process(phrase)
                self.assertIsNotNone(result, f"Phrase '{phrase}' failed.")
                if result:
                    self.assertEqual(result["intent"], "getTime")
                    self.assertEqual(result["params"], {})

    def test_search_web_intent(self):
        passing_phrases = {
            "jarvis search for latest AI news": {"query": "latest ai news"},
            "look up python tutorials online": {"query": "python tutorials online"},
            "jarvis search for cats": {"query": "cats"}
        }
        for phrase, expected_params in passing_phrases.items():
            with self.subTest(phrase=phrase, type="passing"):
                result = self.processor.process(phrase)
                self.assertIsNotNone(result, f"Phrase '{phrase}' failed.")
                if result:
                    self.assertEqual(result["intent"], "searchWeb")
                    self.assertEqual(result["params"], expected_params)

    def test_check_weather_intent(self):
        passing_phrases = {
            "forecast today": {},
            "show weather conditions": {}
        }
        for phrase, expected_params in passing_phrases.items():
            with self.subTest(phrase=phrase, type="passing"):
                result = self.processor.process(phrase)
                self.assertIsNotNone(result, f"Phrase '{phrase}' failed.")
                if result:
                    self.assertEqual(result["intent"], "checkWeather")
                    self.assertEqual(result["params"], expected_params)
        self.assertIsNone(self.processor.process("jarvis weather"))

    def test_play_media_intent(self):
        phrases_with_service = {
            "jarvis play Hotel California on youtube": {"mediaTitle": "hotel california", "mediaService": "youtube"},
            "please stream my workout mix on spotify": {"mediaTitle": "my workout mix", "mediaService": "spotify"},
            "Play The Four Seasons on Apple Music": {"mediaTitle": "the four seasons", "mediaService": "apple music"},
        }
        for phrase, expected_params in phrases_with_service.items():
            with self.subTest(msg="Play Media with Service", phrase=phrase):
                result = self.processor.process(phrase)
                self.assertIsNotNone(result, f"Expected intent for '{phrase}', got None")
                if result:
                    self.assertEqual(result["intent"], "playMedia")
                    self.assertEqual(result["params"], expected_params)

        phrases_without_service = {
            "jarvis play a good song": {"mediaTitle": "a good song"},
            "stream classical music": {"mediaTitle": "classical music"},
            "PLEASE PLAY LOUD MUSIC": {"mediaTitle": "loud music"}
        }
        for phrase, expected_params in phrases_without_service.items():
            with self.subTest(msg="Play Media without Service", phrase=phrase):
                result = self.processor.process(phrase)
                self.assertIsNotNone(result, f"Expected intent for '{phrase}', got None")
                if result:
                    self.assertEqual(result["intent"], "playMedia")
                    self.assertEqual(result["params"], expected_params)
                    self.assertNotIn("mediaService", result["params"])

        phrase_weak_keyword_regex_mismatch = "jarvis list my songs on spotify"
        result_weak_keyword = self.processor.process(phrase_weak_keyword_regex_mismatch)
        self.assertIsNone(result_weak_keyword)

        passing_phrase_strong_keyword = "play my track on my device"
        result_strong_keyword = self.processor.process(passing_phrase_strong_keyword)
        self.assertIsNotNone(result_strong_keyword)
        if result_strong_keyword:
             self.assertEqual(result_strong_keyword["params"]["mediaTitle"], "my track")
             self.assertEqual(result_strong_keyword["params"]["mediaService"], "my device")

        failing_phrase_weak_keywords = "show my track on my device"
        result_fail_keywords = self.processor.process(failing_phrase_weak_keywords)
        self.assertIsNone(result_fail_keywords)

    def test_query_file_intent(self):
        phrases_with_query = {
            "jarvis what does file report.txt say about sales figures": {"filePath": "report.txt", "queryText": "sales figures"},
            "Tell me what the file notes/meeting_notes.txt is about project alpha": {"filePath": "notes/meeting_notes.txt", "queryText": "project alpha"},
            "jarvis what does file data_v2.csv concerning response times": {"filePath": "data_v2.csv", "queryText": "response times"}
        }
        for phrase, expected_params in phrases_with_query.items():
            with self.subTest(msg="Query File with specific question", phrase=phrase):
                result = self.processor.process(phrase)
                self.assertIsNotNone(result, f"Expected intent for '{phrase}', got None. Current params: {result.get('params') if result else 'None'}")
                if result:
                    self.assertEqual(result["intent"], "queryFile")
                    self.assertEqual(result["params"], expected_params)

        phrases_general_analysis = {
            "jarvis summarize file overview.md": {"filePath": "overview.md"},
            "analyze the file data/log_output.txt": {"filePath": "data/log_output.txt"},
            "PLEASE EXPLAIN THE FILE main_logic.py": {"filePath": "main_logic.py"}
        }
        for phrase, expected_params in phrases_general_analysis.items():
            with self.subTest(msg="Query File for general analysis", phrase=phrase):
                result = self.processor.process(phrase)
                self.assertIsNotNone(result, f"Expected intent for '{phrase}', got None.")
                if result:
                    self.assertEqual(result["intent"], "queryFile")
                    self.assertEqual(result["params"], expected_params)
                    self.assertNotIn("queryText", result["params"])

        phrase_non_match = "jarvis check this document status.txt"
        result_non_match = self.processor.process(phrase_non_match)
        self.assertIsNone(result_non_match)

        phrase_bad_verb = "jarvis show the file report.txt about sales"
        self.assertIsNone(self.processor.process(phrase_bad_verb))

    def test_keyword_filtering_logic(self):
        processor_strict = NLPProcessor(self.__class__.intent_definitions, keyword_threshold=90)
        self.assertIsNone(processor_strict.process("jarvis weather"))
        result_lenient = self.lenient_processor.process("jarvis weather")
        self.assertIsNotNone(result_lenient)
        if result_lenient:
             self.assertEqual(result_lenient["intent"], "checkWeather")

    def test_unknown_command_after_keyword_filtering(self): # Restored method
        phrases = [
            "tell me a joke", "jarvis how are you", "jarvis open", "search",
            "what is the temperature today", "book a flight", "", "   "
        ]
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                result = self.processor.process(phrase)
                self.assertIsNone(result, f"Expected None for '{phrase}', got {result}")

        result_search_for = self.processor.process("search for")
        self.assertIsNotNone(result_search_for, "'search for' should be recognized")
        if result_search_for:
            self.assertEqual(result_search_for["intent"], "searchWeb")
            self.assertEqual(result_search_for["params"], {"query": "for"})

    def test_initialization_errors(self):
        with self.assertRaisesRegex(ValueError, "Intent definitions list cannot be empty"):
            NLPProcessor([])
        with self.assertRaisesRegex(ValueError, "Keyword threshold must be between 0 and 100"):
            NLPProcessor(self.__class__.intent_definitions, keyword_threshold=-1)
        with self.assertRaisesRegex(ValueError, "Keyword threshold must be between 0 and 100"):
            NLPProcessor(self.__class__.intent_definitions, keyword_threshold=101)
        with self.assertRaisesRegex(ValueError, "missing 'intent_name' or 'regex_pattern'"):
            NLPProcessor([{ "name": "test" }])
        with self.assertRaisesRegex(ValueError, "Invalid regex pattern for intent"):
            NLPProcessor([{ "intent_name": "test_invalid_regex", "regex_pattern": "[" }])
        with self.assertRaisesRegex(ValueError, "Keywords for intent .* must be a list"):
             NLPProcessor([{
                "intent_name": "test_kw_type",
                "regex_pattern": r".",
                "keywords": "not-a-list"
            }])

if __name__ == '__main__':
    unittest.main(verbosity=2)
