# Gemini LLM Integration

This document describes the Gemini LLM manager integration for the Telegram analyzer project.

## Overview

The `GeminiLLMManager` class provides the same functionality as the OpenAI `LLMManager` but uses Google's Generative AI (Gemini) models instead.

## Setup

1. **Install Dependencies**
   ```bash
   # The google-generativeai dependency has been added to pyproject.toml
   pip install google-generativeai>=0.8.0
   ```

2. **Environment Variables**
   Add your Gemini API key to your `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Usage

### Basic Usage

```python
from src.llm.gemini_sdk import GeminiLLMManager

# Initialize the manager
gemini_manager = GeminiLLMManager()

# Analyze sentiment
sentiment, polarity = await gemini_manager.analyze_sentiment("I love this product!")
print(f"Sentiment: {sentiment}, Polarity: {polarity}")

# Generate response
response = await gemini_manager.generate_response("Hello, how are you?")
print(f"Response: {response}")
```

### Integration with Existing Code

To use Gemini instead of OpenAI in your existing code, simply replace the import and initialization:

```python
# Instead of:
# from src.llm.openai_sdk import LLMManager
# self.llm_manager = LLMManager()

# Use:
from src.llm.gemini_sdk import GeminiLLMManager
self.llm_manager = GeminiLLMManager()
```

## API Methods

### `analyze_sentiment(text: str) -> Tuple[str, float]`

Analyzes the sentiment of the given text and returns:
- `sentiment`: "positive", "negative", or "neutral"
- `polarity`: A float between -1.0 and 1.0 representing sentiment strength

### `generate_response(text: str) -> str`

Generates a contextual response to the given text.

## Error Handling

The manager includes comprehensive error handling:
- Returns neutral sentiment (0.0 polarity) if the model fails to initialize
- Handles JSON parsing errors gracefully
- Logs all errors for debugging

## Configuration

The manager uses the `GEMINI_API_KEY` environment variable for authentication. If the key is not found, the manager will log a warning and return default values.

## Model

Currently uses the `gemini-pro` model. You can modify the `Model` enum in `gemini_sdk.py` to use different Gemini models if needed. 