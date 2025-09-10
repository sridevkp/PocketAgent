class LLM:
    def generate_response(): pass

class OpenaiLLM(LLM):
    def __init__(self, model="gpt-5"):
        super().__init__()
        self.model = model

        try:
            from openai import OpenAI
            self.client = OpenAI()
        except Exception:
            raise ImportError("Openai SDK not found. Install the official Openai client per Openai docs.")
        

    def generate_response(self, system_instruction, content):
        response = self.client.responses.create(
            model="gpt-5",
            instructions=system_instruction,
            input=[
                    {
                        "role": "developer",
                        "content": system_instruction,
                    }
                ]+ content,
        )

        return response.output_text[0].content[0].text


class GenaiLLM(LLM):
    def __init__(self, api_key, model="gemini-2.5-flash"):
        super().__init__()
        self.model = model

        if not api_key:
            raise ValueError("Mistral API key not provided.")
        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
        except Exception:
            raise ImportError("Genai SDK not found. Install the official Genai client per Google Genai docs.")
        

    def generate_response(self, system_instruction, content):
        from google.genai.types import Content, GenerateContentConfig, Part

        contents = [
            Content(
                role=entry["role"],
                parts=[Part(text=entry["content"])]
            )
            for entry in content
        ]

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=GenerateContentConfig(system_instruction=system_instruction)
        )

        return response.candidates[0].content.parts[0].text
    
class MistralLLM(LLM):
    def __init__(self, api_key: str , model: str = "magistral-medium-latest"):
        self.model = model

        if not api_key:
            raise ValueError("Mistral API key not provided.")
        try:
            from mistralai import Mistral
            self.client = Mistral(api_key=api_key)
        except Exception:
            raise ImportError("Mistral SDK not found. Install the official Mistral client per Mistral docs ")

    def generate_response(self, system_instruction: str, content) -> str:
        try:
            chat_response = self.client.chat.complete(
                    model = self.model,
                    messages = [
                        {
                            "role": "system",
                            "content": system_instruction,
                        }
                    ]+ content,
                    response_format = {
                        "type": "json_object",
                    }
                )
            
            return chat_response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Mistral response generation failed: {e}")

class CoherelLLM(LLM):
    def __init__(self, api_key: str , model: str = "command-a-03-2025"):
        self.model = model

        if not api_key:
            raise ValueError("Cohere API key not provided.")
        try:
            import cohere
            self.client = cohere.ClientV2()
        except Exception:
            raise ImportError("cohere SDK not found. Install the official Cohere client per Cohere docs ")

    def generate_response(self, system_instruction: str, content) -> str:
        try:
            chat_response = self.client.chat(
                model=self.model,
                messages=[
                        {
                            "role": "system",
                            "content": system_instruction,
                        }
                    ]+ content,
                response_format = {
                        "type": "json_object"
                    }
            )
            
            return chat_response.message.content[0].text
        except Exception as e:
            raise RuntimeError(f"Cohere response generation failed: {e}")
