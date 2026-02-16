# engine.py
from openai import OpenAI
from templates import PROMPT_LIBRARY
import sys

class GemmaEngine:
    def __init__(self):
        # Connect to local Ollama instance
        try:
            self.client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama" # Required but unused
            )
        except Exception as e:
            print(f"❌ Error connecting to Ollama: {e}")
            sys.exit(1)

    def execute_task(self, task_id, **kwargs):
        """
        Loads the prompt, injects data, and gets response from Gemma.
        """
        # 1. Load Configuration
        config = PROMPT_LIBRARY.get(task_id)
        if not config:
            return f"❌ Error: Task '{task_id}' not found."

        # 2. Inject Variables (The "Prompt Engineering" part)
        try:
            prompt = config['user_template'].format(**kwargs)
        except KeyError as e:
            return f"❌ Error: Missing input data for variable {e}"

        print(f"⚙️  Gemma:2b is thinking about {task_id}...")

        # 3. Call the Model
        response = self.client.chat.completions.create(
            model=config['model'],
            messages=[
                {"role": "system", "content": config['system']},
                {"role": "user", "content": prompt}
            ],
            temperature=config['temperature'],
        )

        return response.choices[0].message.content