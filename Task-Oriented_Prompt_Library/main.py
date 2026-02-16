# main.py
from engine import GemmaEngine
from colorama import Fore, Style, init

# Initialize colors
init(autoreset=True)

def run_app():
    # Start the engine
    ai = GemmaEngine()

    # --- Scenario 1: Summarizing a Work Email ---
    email_content = """
    From: Boss
    Subject: Urgent
    Hey Team, we need to finalize the Q3 report by Friday 5 PM. 
    Also, please update the client database with the new leads.
    I'll be out of office tomorrow, so email Sarah if you get stuck.
    """
    
    print(Fore.CYAN + "\n--- Task 1: Summarize Email ---")
    result = ai.execute_task("SUMMARIZE_EMAIL", email_text=email_content)
    print(Fore.GREEN + result)


    # --- Scenario 2: Fixing Broken Code ---
    # A classic error: dividing by zero
    bad_code = """
    def calc_ratio(a, b):
        return a / 0
    """

    print(Fore.CYAN + "\n--- Task 2: Fix Python Code ---")
    result = ai.execute_task("FIX_PYTHON", code_snippet=bad_code)
    print(Fore.YELLOW + result)


    # --- Scenario 3: Extracting Data ---
    customer_msg = "I want to buy the SuperWidget 3000. I saw it listed for $499."

    print(Fore.CYAN + "\n--- Task 3: JSON Extraction ---")
    result = ai.execute_task("EXTRACT_KEYWORDS", input_text=customer_msg)
    print(Fore.MAGENTA + result)

if __name__ == "__main__":
    run_app()