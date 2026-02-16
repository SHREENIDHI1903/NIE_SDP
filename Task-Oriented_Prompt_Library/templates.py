# templates.py

PROMPT_LIBRARY = {
    
    # Task 1: The Email Summarizer
    # Gemma:2b is small, so we give it very clear, short instructions.
    "SUMMARIZE_EMAIL": {
        "model": "gemma:2b",
        "temperature": 0.2, 
        "system": (
            "You are a helpful assistant. "
            "Read the email and output exactly 3 bullet points summarizing the key actions. "
            "Do not add any intro or outro text."
        ),
        "user_template": "Email:\n'''{email_text}'''\n\nSummary:"
    },

    # Task 2: The Python Bug Fixer
    "FIX_PYTHON": {
        "model": "gemma:2b",
        "temperature": 0.1, # Low temp for code accuracy
        "system": (
            "You are a Python Expert. "
            "Find the bug in the code below. "
            "Output ONLY the fixed code block. Do not explain."
        ),
        "user_template": "Code:\n```python\n{code_snippet}\n```"
    },

    # Task 3: The Keyword Extractor (Structured Output)
    "EXTRACT_KEYWORDS": {
        "model": "gemma:2b",
        "temperature": 0.0,
        "system": (
            "You are a data extractor. "
            "Identify the 'Product' and the 'Price' from the text. "
            "Output the result in JSON format: {'product': str, 'price': str}."
        ),
        "user_template": "Text: {input_text}"
    }
}