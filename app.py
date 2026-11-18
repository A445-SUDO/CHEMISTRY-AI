import os
import re
import sqlite3
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()
APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "chemassist.db"

st.set_page_config(page_title="ChemAssist AI", page_icon="🧪", layout="wide")

# ---------- Database ----------
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student TEXT,
                score INTEGER,
                total INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

init_db()

# ---------- Styling ----------
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0b1020 0%, #111b32 55%, #17132d 100%); color: #f4f6ff; }
[data-testid="stSidebar"] { background: #10172a; }
.hero { padding: 1.6rem; border-radius: 22px; background: linear-gradient(115deg,#30205f,#155e75); border: 1px solid #64748b55; }
.hero h1 { color: white; font-size: 2.45rem; margin-bottom: .25rem; }
.hero p { color: #e2e8f0; font-size: 1.05rem; }
.card { background: #17233a; border: 1px solid #34445e; border-radius: 16px; padding: 1rem 1.1rem; margin-bottom: .7rem; }
.small-muted { color: #b7c4d8; font-size: .92rem; }
div.stButton > button { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ---------- Content ----------
EXPERIMENTS = [
    {
        "title": "Red Cabbage pH Indicator (simulation)",
        "level": "Beginner",
        "goal": "Understand how indicators change colour in acidic, neutral and basic solutions.",
        "concept": "Red cabbage contains pigments called anthocyanins. Their colour changes with pH.",
        "materials": "In a real supervised classroom demonstration: prepared red-cabbage indicator and teacher-approved household samples.",
        "safety": "Use only teacher-approved, labelled samples. Never taste chemicals or mix household cleaners. This website simulation does not require real substances.",
        "steps": ["Choose a sample in the virtual lab.", "Observe the predicted indicator colour.", "Compare the result with the pH scale.", "Record what you learned."],
        "result": "Acidic samples tend toward pink/red, neutral samples purple, and basic samples blue/green. Actual shades vary."
    },
    {
        "title": "Crystallisation (concept lesson)",
        "level": "Beginner",
        "goal": "Learn how crystals form from a solution.",
        "concept": "Crystallisation is a separation and purification technique in which dissolved particles form an ordered solid structure.",
        "materials": "This entry is a concept lesson only. Any physical demonstration must be selected and supervised by a qualified teacher.",
        "safety": "Do not heat solutions or handle unknown substances without a teacher's approved procedure and protective equipment.",
        "steps": ["Learn what a saturated solution means.", "Explore how cooling or solvent evaporation can encourage crystal formation.", "Describe the crystal growth process."],
        "result": "Particles can arrange into a repeating crystal lattice as conditions change."
    },
    {
        "title": "Density and Floating (simulation)",
        "level": "Beginner",
        "goal": "Explore the relationship between density and floating.",
        "concept": "Density is mass divided by volume. An object is more likely to float when its average density is lower than the surrounding fluid.",
        "materials": "No physical materials needed for this digital simulation.",
        "safety": "Digital activity only. Do not conduct experiments with unknown liquids.",
        "steps": ["Change the object's density in the simulator.", "Compare it with the fluid density.", "Predict whether it floats or sinks."],
        "result": "Floating behaviour depends on the object's average density and buoyancy."
    }
]

QUIZ = [
    ("What does pH describe?", ["The colour of a substance", "How acidic or basic a solution is", "Its mass", "Its boiling point"], 1,
     "pH is a scale used to describe acidity and basicity."),
    ("What is the usual pH of a neutral aqueous solution at room temperature?", ["0", "3", "7", "14"], 2,
     "A neutral aqueous solution is approximately pH 7 at 25 °C."),
    ("What is the formula for density?", ["Volume ÷ mass", "Mass ÷ volume", "Mass × volume", "Mass + volume"], 1,
     "Density = mass / volume."),
    ("Which instrument is commonly used to measure liquid volume in a lab?", ["Graduated cylinder", "Thermometer", "Balance", "Stopwatch"], 0,
     "A graduated cylinder measures liquid volume."),
    ("What should you do if an unknown chemical spills?", ["Touch it", "Smell it closely", "Tell the teacher/lab supervisor", "Pour another chemical on it"], 2,
     "Keep away and alert the responsible supervisor; follow the lab emergency procedure.")
]

# ---------- Chemistry equation balancer ----------
def parse_formula(formula):
    """Parse simple chemical formulas, including nested parentheses and element counts."""
    tokens = re.findall(r"[A-Z][a-z]?|\d+|[()]", formula)
    if "".join(tokens) != formula:
        raise ValueError(f"Cannot understand formula: {formula}")
    stack = [{}]
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "(":
            stack.append({})
            i += 1
        elif tok == ")":
            if len(stack) == 1:
                raise ValueError("Unmatched closing parenthesis.")
            group = stack.pop()
            i += 1
            mult = 1
            if i < len(tokens) and tokens[i].isdigit():
                mult = int(tokens[i]); i += 1
            for el, n in group.items():
                stack[-1][el] = stack[-1].get(el, 0) + n * mult
        elif re.fullmatch(r"[A-Z][a-z]?", tok):
            i += 1
            count = 1
            if i < len(tokens) and tokens[i].isdigit():
                count = int(tokens[i]); i += 1
            stack[-1][tok] = stack[-1].get(tok, 0) + count
        else:
            raise ValueError("Unexpected number in formula.")
    if len(stack) != 1:
        raise ValueError("Unclosed parenthesis.")
    return stack[0]

def balance_equation(equation):
    from sympy import Matrix
    from functools import reduce
    from math import gcd
    from sympy import lcm

    if "->" in equation:
        left, right = equation.split("->", 1)
    elif "→" in equation:
        left, right = equation.split("→", 1)
    else:
        raise ValueError("Use an arrow, for example: H2 + O2 -> H2O")
    reactants = [x.strip() for x in left.split("+") if x.strip()]
    products = [x.strip() for x in right.split("+") if x.strip()]
    if not reactants or not products:
        raise ValueError("Add at least one reactant and one product.")
    formulas = reactants + products
    counts = [parse_formula(f) for f in formulas]
    elements = sorted(set().union(*(d.keys() for d in counts)))
    rows = []
    for el in elements:
        rows.append([d.get(el, 0) * (1 if j < len(reactants) else -1)
                     for j, d in enumerate(counts)])
    nullspace = Matrix(rows).nullspace()
    if not nullspace:
        raise ValueError("Could not find a balance for this equation.")
    vec = nullspace[0]
    denominator = 1
    for value in vec:
        denominator = lcm(denominator, value.q)
    coeffs = [int(value * denominator) for value in vec]
    common = reduce(gcd, [abs(c) for c in coeffs if c])
    coeffs = [c // common for c in coeffs]
    if any(c <= 0 for c in coeffs):
        raise ValueError("This equation needs a different formulation.")
    def fmt(items, nums):
        return " + ".join((("" if n == 1 else str(n)) + item) for item, n in zip(items, nums))
    return fmt(reactants, coeffs[:len(reactants)]) + " → " + fmt(products, coeffs[len(reactants):])

# ---------- AI helper ----------
def ask_gemini(question, history=None):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return ("Demo mode is active because GEMINI_API_KEY is not configured.\n\n"
                "I can still show a sample response: pH is a scale that describes how acidic "
                "or basic an aqueous solution is. A value below 7 is acidic, around 7 is neutral, "
                "and above 7 is basic at 25 °C.\n\nAdd your Gemini API key to the .env file to enable live AI answers.")
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = (
            "You are ChemAssist, a careful educational chemistry tutor for students. "
            "Explain concepts clearly and at beginner level. Do not provide instructions for "
            "dangerous synthesis, explosives, poisons, weapons, or unsupervised hazardous experiments. "
            "For practical experiments, prioritize teacher supervision, safety data, and approved protocols. "
            "If uncertain, say so. User question: " + question
        )
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt
        )
        return response.text or "The AI returned an empty response. Please try again."
    except Exception as exc:
        return f"AI connection error: {exc}\n\nCheck your API key, internet connection and selected model. The rest of the website still works."

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🧪 ChemAssist AI")
    st.caption("Your digital chemistry learning lab")
    page = st.radio("NAVIGATION", [
        "🏠 Dashboard", "🤖 AI Chemistry Assistant", "🧫 Experiment Library",
        "⚖️ Equation Balancer", "🧪 Virtual Lab", "🧬 Chemical Explorer",
        "🦺 Safety Centre", "📝 Quiz Centre"
    ])
    st.divider()
    st.caption("Educational project • Version 1.0")
    st.caption("Simulations are educational models, not laboratory instructions.")

# ---------- Dashboard ----------
if page == "🏠 Dashboard":
    st.markdown("""
    <div class="hero">
      <h1>Welcome to ChemAssist AI 🧪</h1>
      <p>Explore chemistry, understand experiments and learn safely with your AI study assistant.</p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    c1, c2, c3 = st.columns(3)
    c1.metric("Learning modules", "7")
    c2.metric("Sample experiments", len(EXPERIMENTS))
    c3.metric("Practice questions", len(QUIZ))
    st.subheader("Explore your laboratory")
    cards = [
        ("🤖 AI Chemistry Assistant", "Ask chemistry questions in simple language."),
        ("🧫 Experiment Library", "Read objectives, concepts and safety notes."),
        ("⚖️ Equation Balancer", "Balance supported chemical equations."),
        ("🧪 Virtual Lab", "Explore safe, simplified simulations."),
        ("🧬 Chemical Explorer", "View basic molecular information."),
        ("🦺 Safety Centre", "Review important laboratory safety habits.")
    ]
    cols = st.columns(3)
    for i, (title, desc) in enumerate(cards):
        with cols[i % 3]:
            st.markdown(f'<div class="card"><h3>{title}</h3><p class="small-muted">{desc}</p></div>', unsafe_allow_html=True)
    st.info("Begin with the Experiment Library or try balancing H2 + O2 -> H2O.")

# ---------- AI Assistant ----------
elif page == "🤖 AI Chemistry Assistant":
    st.title("🤖 AI Chemistry Assistant")
    st.write("Ask a chemistry question and get a beginner-friendly explanation.")
    if "chat" not in st.session_state:
        st.session_state.chat = []
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Example: Explain covalent bonding in simple words...")
    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = ask_gemini(prompt)
            st.markdown(answer)
        st.session_state.chat.append({"role": "assistant", "content": answer})
    st.caption("AI answers can be wrong. Verify important chemistry facts with textbooks or your teacher.")

# ---------- Experiment Library ----------
elif page == "🧫 Experiment Library":
    st.title("🧫 Experiment Library")
    st.write("Explore the science behind each activity. These entries are educational; follow only teacher-approved practical procedures.")
    for exp in EXPERIMENTS:
        with st.expander(f"{exp['title']} • {exp['level']}"):
            st.markdown(f"**Objective:** {exp['goal']}")
            st.markdown(f"**Scientific concept:** {exp['concept']}")
            st.markdown(f"**Materials:** {exp['materials']}")
            st.markdown("**Learning steps:**")
            for step in exp["steps"]:
                st.write("• " + step)
            st.markdown(f"**Expected learning:** {exp['result']}")
            st.warning("Safety: " + exp["safety"])

# ---------- Equation Balancer ----------
elif page == "⚖️ Equation Balancer":
    st.title("⚖️ Chemical Equation Balancer")
    st.write("Enter a simple chemical equation. Use -> or → between reactants and products.")
    equation = st.text_input("Chemical equation", "H2 + O2 -> H2O")
    if st.button("Balance equation", type="primary"):
        try:
            result = balance_equation(equation.replace(" ", ""))
            st.success("Balanced equation")
            st.markdown(f"## `{result}`")
            st.caption("The program finds coefficients that conserve each element. This first version supports ordinary neutral molecular formulas, not every ionic/redox notation.")
        except Exception as exc:
            st.error(str(exc))
    st.info("Try: Fe + O2 -> Fe2O3   |   Al + O2 -> Al2O3   |   C3H8 + O2 -> CO2 + H2O")

# ---------- Virtual Lab ----------
elif page == "🧪 Virtual Lab":
    st.title("🧪 Virtual Lab: pH Indicator")
    st.write("A simplified digital model of how red-cabbage indicator colour can vary with pH. No real chemicals are used.")
    ph = st.slider("Adjust the simulated pH", 0.0, 14.0, 7.0, 0.5)
    if ph < 4:
        colour, label, explanation = "#ef6b91", "Acidic", "The model shows a pink/red shade."
    elif ph < 6.5:
        colour, label, explanation = "#b56bd8", "Weakly acidic", "The model shows a purple-pink shade."
    elif ph <= 7.5:
        colour, label, explanation = "#7856b5", "Approximately neutral", "The model shows a purple shade."
    elif ph < 11:
        colour, label, explanation = "#398bd0", "Basic", "The model shows a blue shade."
    else:
        colour, label, explanation = "#35a77c", "Strongly basic", "The model shows a blue-green shade."
    st.markdown(f"""
    <div style="background:{colour};padding:2rem;border-radius:18px;color:white;text-align:center">
      <div style="font-size:1rem">SIMULATED INDICATOR COLOUR</div>
      <div style="font-size:2.5rem;font-weight:700">{label}</div>
      <div>pH = {ph:g}</div>
    </div>
    """, unsafe_allow_html=True)
    st.write(explanation)
    st.caption("Real indicator colours depend on concentration, preparation and conditions. This is an illustrative model, not a measurement.")

# ---------- Chemical Explorer ----------
elif page == "🧬 Chemical Explorer":
    st.title("🧬 Chemical Explorer")
    st.write("Explore a few familiar molecules. Values shown are educational reference information.")
    molecules = {
        "Water": ("H₂O", "Two hydrogen atoms and one oxygen atom.", "SMILES: O"),
        "Carbon dioxide": ("CO₂", "One carbon atom and two oxygen atoms.", "SMILES: O=C=O"),
        "Methane": ("CH₄", "One carbon atom bonded to four hydrogen atoms.", "SMILES: C"),
        "Ethanol": ("C₂H₆O", "An alcohol molecule with two carbon atoms.", "SMILES: CCO"),
        "Glucose": ("C₆H₁₂O₆", "A simple sugar used by living organisms.", "SMILES: C(C1C(C(C(C(O1)O)O)O)O)O")
    }
    selected = st.selectbox("Choose a molecule", list(molecules.keys()))
    formula, description, smiles = molecules[selected]
    st.markdown(f'<div class="card"><h2>{selected} · {formula}</h2><p>{description}</p><p>{smiles}</p></div>', unsafe_allow_html=True)
    try:
        from rdkit import Chem
        from rdkit.Chem import Draw, Descriptors
        smi = smiles.replace("SMILES: ", "")
        mol = Chem.MolFromSmiles(smi)
        if mol:
            st.image(Draw.MolToImage(mol, size=(450, 300)), caption=f"2D structure of {selected}")
            st.write(f"Calculated molecular weight: **{Descriptors.MolWt(mol):.2f} g/mol**")
        else:
            st.info("RDKit could not draw this structure in the current environment.")
    except ImportError:
        st.info("Optional: install RDKit to display 2D molecule structures. See README.md.")
    except Exception as exc:
        st.info(f"Molecule drawing is unavailable: {exc}")

# ---------- Safety Centre ----------
elif page == "🦺 Safety Centre":
    st.title("🦺 Laboratory Safety Centre")
    st.write("Safety comes before every experiment.")
    safety_items = [
        ("Wear appropriate PPE", "Use teacher-approved goggles, lab coat and gloves when required."),
        ("Never taste chemicals", "Never taste laboratory substances. Avoid directly smelling chemicals."),
        ("Read labels", "Check the identity, hazard symbols and instructions before handling any substance."),
        ("Never mix unknown substances", "Do not combine chemicals or household cleaners."),
        ("Know emergency equipment", "Learn the locations of eyewash stations, safety showers, exits and spill kits."),
        ("Report incidents", "Tell the teacher or lab supervisor immediately about spills, breakages or exposure.")
    ]
    for title, detail in safety_items:
        st.markdown(f'<div class="card"><h4>✅ {title}</h4><p class="small-muted">{detail}</p></div>', unsafe_allow_html=True)
    st.error("This website is an educational aid, not a substitute for a teacher, safety data sheet, institutional rules or emergency procedures.")

# ---------- Quiz ----------
elif page == "📝 Quiz Centre":
    st.title("📝 Chemistry Knowledge Quiz")
    name = st.text_input("Student name (optional)", "Student")
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    with st.form("chem_quiz"):
        answers = []
        for i, (question, options, correct, explanation) in enumerate(QUIZ):
            choice = st.radio(f"{i+1}. {question}", options, index=None, key=f"quiz_{i}")
            answers.append(choice)
        submitted = st.form_submit_button("Submit quiz", type="primary")
    if submitted:
        score = sum(1 for i, answer in enumerate(answers) if answer == QUIZ[i][1][QUIZ[i][2]])
        with sqlite3.connect(DB_PATH) as con:
            con.execute("INSERT INTO quiz_results(student, score, total) VALUES (?, ?, ?)",
                        (name.strip() or "Student", score, len(QUIZ)))
        st.session_state.quiz_submitted = True
        st.session_state.quiz_score = score
    if st.session_state.quiz_submitted:
        score = st.session_state.quiz_score
        st.success(f"You scored {score} out of {len(QUIZ)}!")
        for i, (question, options, correct, explanation) in enumerate(QUIZ):
            st.write(f"**{i+1}. {question}**")
            st.write(f"Correct answer: {options[correct]}")
            st.caption(explanation)
        if st.button("Try again"):
            st.session_state.quiz_submitted = False
            st.rerun()
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute("SELECT student, score, total, created_at FROM quiz_results ORDER BY id DESC LIMIT 10").fetchall()
    if rows:
        st.subheader("Recent quiz results")
        st.dataframe([{"Student": r[0], "Score": f"{r[1]}/{r[2]}", "Date": r[3]} for r in rows], use_container_width=True)
