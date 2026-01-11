---
# ⚖️ Legality AI - Contract Risk Detector

**Legality AI** is an intelligent contract analysis tool designed to identify legal risks in contracts automatically. It uses a custom-trained Sentence Transformer model to detect risky clauses for the category of "Termination for Convenience", "Uncapped Liability" and "Non-Compete" and uses Large Language Models (LLMs) to suggest safer, more balanced rewrites.

---

## 🚀 Features

* **📄 Automated PDF Analysis:** Upload any contract PDF; the system extracts text and chunks it for analysis.
* **⚠️ Risk Detection:** Uses vector similarity search to compare contract clauses against a "Gold Standard" database of known legal risks.
* **🤖 AI Suggestions:** Automatically generates safe, balanced rewrites for risky clauses using **Mistral-7B** (via OpenRouter).
* **🛡️ Safety Guardrails:** automatically flags high-risk clauses (like Liability Caps) as "Review Only" to prevent dangerous AI hallucinations.
* **📊 Observability:** Full tracing of AI logic and latency using **Langfuse**. **(In further updates)**

---

## 🛠️ Tech Stack

### **Backend**

* **Framework:** FastAPI (Python)
* **ML Model:** `sentence-transformers` (Custom Model: `bhavibhatt/legal_model` (on huggingface))
* **LLM Engine:** OpenRouter API (`mistralai/mistral-7b-instruct`)
* **Vector Search:** Scikit-Learn (Cosine Similarity)
* **PDF Processing:** `pdfplumber` & `langchain-text-splitters`
* **Observability:** Langfuse

### **Frontend**

* **Framework:** React (Vite)
* **Styling:** Tailwind CSS / Shadcn UI
* **Language:** TypeScript

### **Deployment**

* **Backend:** Railway
* **Frontend:** Vercel

---

## 🏗️ Architecture

1. **Ingestion:** User uploads a PDF → Backend extracts text → Splits text into chunks.
2. **Embedding:** Chunks are converted into vectors using the custom Hugging Face model.
3. **Risk Search:** Vectors are compared against the `synthetic_gold_standard.json` dataset. High similarity scores trigger a "Risk Detected" flag.
4. **Policy Check:** The system checks if the clause is "Rewrite Allowed" or "Review Only" (e.g., Liability clauses are never rewritten).
5. **Generative Rewrite:** If allowed, the LLM generates a safer version of the clause.

---

## 💻 Local Installation

Follow these steps to run the project locally.

### **1. Clone the Repository**

```bash
git clone https://github.com/your-username/legality-ai.git
cd legality-ai

```

### **2. Backend Setup**

Navigate to the backend folder and install dependencies.

```bash
cd backend

# Create a virtual environment (Recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

```

**Configure Environment Variables:**
Create a `.env` file inside the `backend/` folder:

```env
# AI & Model Keys
OPENROUTER_API_KEY=your_openrouter_key_here
HF_TOKEN=your_huggingface_token_here

# Langfuse (Observability) - Optional
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com

```

**Run the Server:**

```bash
uvicorn main:app --reload
# Backend will run at: http://127.0.0.1:8000

```

### **3. Frontend Setup**

Open a new terminal and navigate to the root (or frontend folder if separate).

```bash
cd frontend  # or just stay in root if package.json is there
npm install
npm run dev
# Frontend will run at: http://localhost:5173

```

---

## 🌍 Deployment

### **Backend (Railway)**

The backend is deployed on Railway to handle the heavy ML libraries (`torch`, `transformers`).

* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
* **Root Directory:** `/backend`

### **Frontend (Vercel)**

The frontend is deployed on Vercel for fast global CDN delivery.

* **Framework Preset:** Vite
* **Build Command:** `npm run build`
* **Output Directory:** `dist`

---

## 🔌 API Endpoints

### `POST /analyze-contract`

Uploads a PDF and returns a list of detected risks.

### `GET /health`

Checks if the ML model is loaded and external APIs are connected.

---

## 🤝 Contributers

1. Bhavyang
2. Sneha
3. Vedant

---

