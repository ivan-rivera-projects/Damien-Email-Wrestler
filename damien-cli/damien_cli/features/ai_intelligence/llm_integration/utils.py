import tiktoken

class TokenCounter:
    """
    A utility class for counting tokens in a text string based on a given model.
    It caches encodings to avoid re-initializing them for the same model.
    """
    def __init__(self):
        self.encodings: dict[str, tiktoken.Encoding] = {}

    def _get_encoding(self, model_name: str) -> tiktoken.Encoding:
        """
        Retrieves or creates and caches the tiktoken encoding for a given model.
        Falls back to "cl100k_base" if the specific model encoding is not found.
        """
        if model_name not in self.encodings:
            try:
                self.encodings[model_name] = tiktoken.encoding_for_model(model_name)
            except KeyError:
                # Fallback for models not directly known by tiktoken,
                # or if the model name is an alias not recognized by tiktoken.
                # cl100k_base is a common encoding used by newer OpenAI models.
                self.encodings[model_name] = tiktoken.get_encoding("cl100k_base")
        return self.encodings[model_name]

    def count(self, text: str, model_name: str = "gpt-3.5-turbo") -> int:
        """
        Counts the number of tokens in the given text for the specified model.

        Args:
            text: The text to count tokens for.
            model_name: The name of the model to use for tokenization.
                        Defaults to "gpt-3.5-turbo".

        Returns:
            The number of tokens in the text.
        """
        if not text:
            return 0
        encoding = self._get_encoding(model_name)
        return len(encoding.encode(text))

# Example Usage (can be removed or kept for simple testing)
if __name__ == '__main__':
    counter = TokenCounter()
    sample_text = "This is a sample sentence for token counting."
    
    # Test with default model
    num_tokens_default = counter.count(sample_text)
    print(f"Tokens for '{sample_text}' (default model gpt-3.5-turbo): {num_tokens_default}")

    # Test with a specific model (e.g., gpt-4)
    num_tokens_gpt4 = counter.count(sample_text, model_name="gpt-4")
    print(f"Tokens for '{sample_text}' (model gpt-4): {num_tokens_gpt4}")

    # Test with a model that might fallback
    num_tokens_fallback = counter.count(sample_text, model_name="some-custom-model")
    print(f"Tokens for '{sample_text}' (model some-custom-model, fallback): {num_tokens_fallback}")

    # Test empty string
    num_tokens_empty = counter.count("")
    print(f"Tokens for empty string: {num_tokens_empty}")