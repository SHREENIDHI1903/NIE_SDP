### **Phase 1: Setup (Terminal)**

1. **Install the Python Library:**
Open your terminal/command prompt and run:
```bash
pip install openai colorama

```


2. **Pull the Model:**
Download the specific model we are using (approx. 1.5GB):
```bash
ollama pull gemma:2b

```
### **Phase 2: The Modular Code**

We will create three separate files in the same folder.

#### **File 1: `templates.py` (The Configuration)**

*Create this file. This contains your "Prompt Engineering" logic. Notice we hardcode `gemma:2b` here.*

---

#### **File 2: `engine.py` (The Connector)**

*Create this file. This script talks to your local Ollama server.*

---

#### **File 3: `main.py` (The User Interface)**

*Create this file. This is where you run the tasks.*

---

### **Phase 3: Run It**

1. Make sure Ollama is running in the background.
2. Run the script:
```bash
python main.py

```

---
