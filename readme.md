# Pocket LLM Agent

Pocket Agent is a lightweight framework that turns any raw LLM (OpenAI, Gemini, Mistral, Cohere, etc.) into a tool-using reasoning agent.

Instead of just generating free-form text, Pocket Agent enforces a structured JSON protocol where the LLM can:

Plan: Describe the next step in natural language ({"type": "plan", ...})

Act: Call registered tools with structured inputs ({"type": "action", "function": "get_weather", "input": {...}})

Observe: Receive results back from tools ({"type": "observation", ...})

Respond: Produce user-facing output ({"type": "output", "output": "It is 32°C in Kolkata."})

This lets the LLM not only reason but also interact with your environment (APIs, databases, files, custom functions) safely and consistently.

## Features

- Unified LLM interface for multiple providers

- Plug-and-play backends:

  - OpenAI

  - Google Gemini

  - Mistral AI

  - Cohere AI

- Structured JSON messaging protocol for history & reasoning
- Lightweight, no heavy frameworks

- Extendable: add new tools or model providers easily