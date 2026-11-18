# ChemAssist AI — AI-Powered Chemistry Experiment Assistant

A beginner-friendly educational chemistry website built with Python and Streamlit.

## Features in this starter version

- Dashboard
- AI chemistry tutor (Gemini API optional; demo mode works without a key)
- Experiment library with safety notes
- Chemical equation balancer for simple neutral molecular equations
- pH indicator virtual simulation
- Chemical explorer with optional RDKit 2D drawings
- Safety centre
- Chemistry quiz with SQLite score history

## 1. Install the tools

Install Python 3.11 or newer and Visual Studio Code:
- Python: https://www.python.org/downloads/
- VS Code: https://code.visualstudio.com/

During Python installation on Windows, tick **Add Python to PATH**.

## 2. Create and open the project

Extract the ZIP file. Open the `chemassist_ai` folder in VS Code.

Open VS Code's terminal: **Terminal → New Terminal**.

## 3. Create a virtual environment

Windows PowerShell:
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:
```cmd
py -m venv .venv
.venv\Scripts\activate.bat
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Install packages

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If RDKit fails to install, install the core packages first:
```bash
pip install streamlit python-dotenv google-genai sympy
```
You can add RDKit later using the official instructions: https://www.rdkit.org/docs/Install.html

## 5. Run the website

```bash
streamlit run app.py
```

A browser tab should open automatically. If it does not, copy the local URL shown in the terminal (usually http://localhost:8501).

## 6. Enable the AI assistant (optional)

1. Create a Gemini API key through Google AI Studio: https://aistudio.google.com/app/apikey
2. Make a copy of `.env.example` and name the copy `.env`.
3. Put your key after `GEMINI_API_KEY=`.
4. Save the file and restart Streamlit.

Example:
```env
GEMINI_API_KEY=your_private_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Never share your API key, post it in screenshots, or commit `.env` to GitHub. API access and quotas depend on Google's current terms and account eligibility. If no key is configured, the assistant uses a clearly labelled demo response.

## 7. Test the project

- Open AI Chemistry Assistant. Without a key, check demo mode. With a key, ask: "Explain pH in simple words."
- Open Equation Balancer and try `H2 + O2 -> H2O`.
- Open Virtual Lab and move the pH slider.
- Open Chemical Explorer and choose Water. If RDKit is installed, a 2D structure should appear.
- Complete the quiz and check the recent results.

## Important educational and safety limits

This is a learning prototype, not a certified laboratory system. Virtual lab output is simulated. Experiment entries are conceptual learning material, not complete practical protocols. Never perform chemical experiments without qualified supervision and institution-approved procedures. Do not use AI output as the sole source for chemical handling decisions.

## Project structure

```text
chemassist_ai/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Next development stages

1. Add more verified experiments and references.
2. Improve equation balancing and add ionic/redox support.
3. Add molecule search and richer RDKit visualisations.
4. Add student accounts and teacher/admin roles.
5. Add deployment and a project report/presentation.
