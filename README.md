# MIRA v0 Prototype 🧬

## AI-Powered Knowledge Assistant for DeSci & Molecule

MIRA (Molecule Information & Research Assistant) is an experimental prototype that demonstrates how modern AI can intelligently provide accurate information about decentralized science (DeSci) and Molecule's ecosystem.

## 🎯 What is MIRA?

MIRA is a smart chatbot that can answer questions about **anything related to Molecule and the DeSci ecosystem**. This includes, but is not limited to:

- **DeSci (Decentralized Science)** - The movement to make scientific research more open and accessible
- **Molecule Platform** - All features, products, and services offered by Molecule
- **IP-NFTs** - Tokenizing intellectual property and research assets
- **Research Funding** - Grants, investments, and new funding mechanisms
- **DAOs & Governance** - BioDAOs, VitaDAO, and decentralized organizations
- **DeSci Tools** - Various tools and protocols in the ecosystem
- **Community & Events** - DeSci conferences, initiatives, and collaborations
- **And much more!** - Any topic connected to Molecule's mission and the broader DeSci movement

### Key Features

- **🤖 Smart Decision Making**: MIRA decides on its own whether it has enough information to answer your question
- **📚 Local Knowledge Base**: Contains curated information about Molecule and DeSci
- **🌐 Web Search Fallback**: Automatically searches the web when local knowledge isn't enough
- **👍👎 Feedback System**: Help improve MIRA by rating responses
- **🔍 Source Transparency**: Always shows where information comes from

## 🏗️ How It Works

MIRA uses a three-step intelligent process called "Agentic RAG" (Retrieval Augmented Generation):

### 1. **Search Local Knowledge**
When you ask a question, MIRA first searches its local knowledge base for relevant information using advanced semantic search that understands meaning, not just keywords.

### 2. **Evaluate & Decide**
MIRA then evaluates the information it found:
- **Sufficient Context?** → Use local knowledge to answer
- **Insufficient but Relevant?** → Search the web for current information
- **Off-topic?** → Politely decline with an explanation

### 3. **Generate Response**
Based on its decision, MIRA either:
- Provides an answer from trusted local sources
- Searches the web for up-to-date information (focusing on trusted domains)
- Explains that the question is outside its expertise

## 🛠️ Technology Stack

MIRA combines several technologies:

### **Chainlit** (User Interface)
- Responsive chat interface
- Real-time streaming responses
- Interactive feedback buttons

### **LanceDB** (Knowledge Storage)
- **Vector Search**: Finds information by meaning and context
- **Hybrid Search**: Combines semantic understanding with keyword matching
- **Fast & Efficient**: Delivers relevant results quickly

### **OpenAI GPT-4o** (AI Brain)
- Understands natural language questions
- Evaluates context quality
- Generates human-like responses
- Web search capabilities for current information

### **Langfuse** (Monitoring & Analytics)
- Tracks system performance
- Collects user feedback
- Helps improve responses over time
- Ensures quality and reliability

## 📊 The Workflow

Here's how MIRA processes your questions:

```
┌─────────────────────┐
│   User Question     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Search Local       │
│  Knowledge Base     │
│  (LanceDB)          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Evaluate Context   │
│  Is it sufficient?  │
└──────────┬──────────┘
           │
    ┌──────┴──────┬─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│   Yes   │ │   No,   │ │   No &  │
│         │ │   but   │ │  Off-   │
│  Local  │ │Relevant │ │  topic  │
│ Answer  │ │         │ │         │
└─────────┘ │   Web   │ └─────────┘
            │ Search  │
            │ (GPT-4o)│
            └─────────┘
                │
    ┌───────────┴─────────────┐
    │                         │
    ▼                         ▼
┌─────────────────────┐ ┌─────────────────────┐
│  Generate Answer    │ │ "Sorry, I can't     │
│  with Sources       │ │  help with that"    │
└──────────┬──────────┘ └──────────┬──────────┘
           │                       │
           └───────────┬───────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │   Display Answer    │
            │   👍    👎          │
            └─────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ Langfuse Monitoring │
            │ (Track & Improve)   │
            └─────────────────────┘
```

### The Decision Process Explained:

1. **You ask a question** → MIRA receives your query
2. **Searches local knowledge** → Uses LanceDB's semantic search to find relevant information
3. **Makes a smart decision**:
   - ✅ **Sufficient info?** → Answers from local knowledge
   - 🌐 **Not enough but relevant?** → Searches the web for current info
   - ❌ **Off-topic?** → Politely declines
4. **Generates response** → Creates a helpful answer with sources
5. **You rate the answer** → Helps MIRA improve over time

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone [repository-url]
   cd molecule-chainlit
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file with:
   ```
   OPENAI_API_KEY=your_openai_api_key
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key
   ```

5. **Run the application**
   ```bash
   chainlit run app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:8000`

## ⚠️ Important Notes

### This is a Prototype
- MIRA v0 is an **experimental prototype**, not a production-ready application
- Used for learning about robust AI systems and gathering user feedback
- Responses should be verified for critical decisions

### Data Sources
- Local knowledge base contains curated information about Molecule and DeSci
- Web search results are filtered to prioritize trusted domains like:
  - molecule.to
  - molecule.xyz
  - bio.xyz
  - vitadao.com
  - ...