# Groq API Setup

TinyOwl now supports Groq API models alongside local Ollama models!

## Get Your Free Groq API Key

1. Go to https://console.groq.com/
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key

## Set Environment Variable

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export GROQ_API_KEY="your-api-key-here"
```

Then reload:
```bash
source ~/.bashrc
```

## Available Models

Once configured, you'll have access to:
- `groq:llama-3.1-70b-versatile` - Best reasoning, slower
- `groq:llama-3.1-8b-instant` - Fast responses
- `groq:mixtral-8x7b-32768` - Long context window

## Free Tier Limits

- 14,400 requests per day
- Very fast inference (~100 tokens/second)
- No credit card required

## Usage

Your TinyOwl will automatically detect the API key and show Groq models in the model switcher (`/model`).