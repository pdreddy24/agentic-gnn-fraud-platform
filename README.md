# Agentic GNN Fraud Detection Platform

An end-to-end AI-powered fraud detection platform that combines **Graph Neural Networks**, **traditional machine learning**, **Neo4j graph intelligence**, **agentic AI workflows**, and **LLM-based explanations** to detect suspicious financial transactions.

This project demonstrates how graph-based AI can be used to identify fraud patterns that are often hidden in relationships between users, devices, cards, IP addresses, merchants, and transactions.

---

## 🚀 Project Overview

Traditional fraud detection systems often analyze transactions individually. However, many real-world fraud patterns are not visible in a single transaction. Fraudsters often reuse devices, IP addresses, cards, merchants, and accounts, creating hidden relationship patterns.

This project solves that problem by combining:

- **Graph Neural Networks** for relationship-based fraud detection
- **Neo4j** for graph intelligence and relationship analysis
- **Traditional ML models** for transaction-level fraud scoring
- **LangGraph-style agent workflow** for modular fraud triage
- **LLM explanations** for analyst-friendly decision summaries
- **FastAPI backend** for APIs and batch processing
- **React frontend** for CSV upload and results visualization

The platform allows users to upload transaction CSV files and classify each transaction as:

- ✅ `APPROVE`
- ⚠️ `REVIEW`
- 🚫 `BLOCK`

---

## 🧠 Problem Statement

Fraud is not always visible from a single transaction row.

For example, this transaction may look normal:

```text
User: U1021
Amount: $145
Country: US
Channel: Web
Merchant: M552
Timestamp: 10:42 AM
```

But the same transaction becomes suspicious when graph relationships are analyzed:

```text
The same device is used by multiple users.
The same IP address is linked to several cards.
The merchant has a high historical fraud rate.
The card is connected to multiple accounts.
```

Traditional tabular models may miss these relationship-based fraud patterns. This project uses graph intelligence and GNN-based scoring to identify suspicious connections across entities.

---

## 🎯 Project Goal

The goal of this project is to build a production-style fraud detection platform that can:

1. Accept transaction data through CSV upload
2. Validate and normalize incoming transactions
3. Generate machine-learning-ready features
4. Analyze entity relationships using Neo4j
5. Score graph-based fraud risk using a GNN-style model
6. Score transaction-level fraud risk using a traditional ML model
7. Combine risk signals into a final decision
8. Classify transactions as `APPROVE`, `REVIEW`, or `BLOCK`
9. Generate human-readable explanations
10. Store prediction history and audit logs

---

## 🏗️ System Architecture

```text
User
 ↓
React Frontend
 ↓
CSV Upload
 ↓
FastAPI Backend
 ↓
Agentic Fraud Detection Workflow
 ↓
Data Quality Agent
 ↓
Feature Engineering Agent
 ↓
Neo4j Graph Agent
 ↓
GNN Graph Scoring Agent
 ↓
ML Scoring Agent
 ↓
Policy Decision Agent
 ↓
Audit Agent
 ↓
LLM Explanation Agent
 ↓
Dashboard Results
```

---

## ⚙️ How It Works

### 1. CSV Upload

The user uploads a transaction CSV file through the frontend.

Expected CSV columns:

```csv
transaction_id,user_id,device_id,card_id,ip_address,merchant_id,amount,timestamp,channel,country
```

---

### 2. Data Quality Agent

The Data Quality Agent validates each transaction before scoring.

It checks for:

- Missing transaction IDs
- Missing user IDs
- Invalid amounts
- Invalid timestamps
- Missing device, card, IP, or merchant data
- Incorrect CSV structure

This prevents bad input data from entering the fraud scoring pipeline.

---

### 3. Feature Engineering Agent

The Feature Agent converts raw transaction data into useful ML features.

Example features:

```text
amount
log_amount
hour_of_day
is_night_transaction
user_transaction_count
device_transaction_count
card_transaction_count
ip_transaction_count
merchant_transaction_count
channel_encoded
country_encoded
```

These features help the ML model detect suspicious transaction-level behavior.

---

### 4. Neo4j Graph Agent

The Neo4j Graph Agent analyzes relationships between entities.

Graph entities include:

```text
User
Transaction
Device
Card
IP Address
Merchant
```

Example relationships:

```text
User → made → Transaction
Transaction → used → Device
Transaction → used → Card
Transaction → came_from → IP Address
Transaction → paid_to → Merchant
```

The graph layer helps detect suspicious patterns such as:

- One device used by many users
- One card linked to multiple users
- One IP address connected to many cards
- A merchant with high fraud history
- Transactions connected to risky entities

---

### 5. GNN Graph Scoring Agent

The GNN-style scoring layer evaluates relationship-based fraud risk.

Instead of looking only at one transaction, the graph model analyzes connected entities.

Example:

```text
Transaction T1 looks normal.
But T1 uses Device D55.
Device D55 is shared by 12 different users.
Several connected users have suspicious transaction history.
Therefore, T1 receives a higher graph risk score.
```

This helps detect fraud rings and shared fraud infrastructure.

---

### 6. ML Scoring Agent

The ML Scoring Agent uses a traditional machine learning model to detect transaction-level risk.

It looks at features such as:

- Amount
- Time of transaction
- Channel
- Country
- Merchant activity
- User activity
- Device activity
- Card activity

This layer is useful for detecting suspicious behavior from the transaction itself.

---

### 7. Policy Decision Agent

The Policy Agent combines multiple risk signals:

```text
GNN graph score
Traditional ML score
Neo4j graph risk score
```

Then it produces a final decision:

```text
Low risk      → APPROVE
Medium risk   → REVIEW
High risk     → BLOCK
```

This makes the system more robust because it does not depend on a single model.

---

### 8. Audit Agent

The Audit Agent records fraud scoring decisions for traceability.

Audit information can include:

```text
Transaction ID
Risk score
Final decision
Reason codes
Agents executed
Timestamp
```

This makes the system easier to debug, review, and explain.

---

### 9. LLM Explanation Agent

The LLM does not make the fraud decision.

Instead, it explains the decision in simple language.

Example explanation:

```text
This transaction was marked REVIEW because the device has been used by multiple users, the IP address is connected to several recent transactions, and the merchant has elevated fraud risk.
```

This makes the platform more useful for fraud analysts and non-technical users.

---

## 🧩 Core Features

- User authentication
- CSV transaction upload
- Batch fraud prediction
- Data validation
- Feature engineering
- Neo4j graph relationship analysis
- GNN-based fraud scoring
- Traditional ML fraud scoring
- Final `APPROVE`, `REVIEW`, or `BLOCK` decision
- Prediction history
- Batch comparison
- Audit logging
- LLM-generated explanations
- React frontend
- FastAPI backend
- Streamlit dashboard option
- Docker support

---

## 🛠️ Tech Stack

### Frontend

- React
- JavaScript
- CSS

### Backend

- Python
- FastAPI
- Uvicorn

### Machine Learning

- Scikit-learn
- Random Forest-style tabular model
- Feature engineering pipeline

### Graph Intelligence

- Neo4j
- Graph-based entity relationship modeling
- GNN-style fraud scoring

### Agent Workflow

- LangGraph-style multi-agent orchestration

### LLM Layer

- OpenAI API
- Human-readable fraud explanations

### Database

- SQLite for application data
- Neo4j for graph relationships

### DevOps

- Docker
- Docker Compose

---

## 📁 Project Structure

```text
agentic-gnn-fraud-platform/
│
├── app/                    # Main FastAPI application and agent workflow
├── backend/                # Backend-related files
├── frontend/               # React frontend
├── dashboard/              # Streamlit dashboard
├── ml/                     # ML training and model logic
├── artifacts/              # Saved models and generated artifacts
├── scripts/                # Utility scripts
├── data/                   # Sample or processed data
├── Dockerfile              # Backend Docker setup
├── Dockerfile.dashboard    # Dashboard Docker setup
├── docker-compose.yml      # Docker Compose setup
├── docker-compose.full.yml # Full Docker setup
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## 🔄 Fraud Detection Workflow

```text
CSV File
 ↓
Frontend Upload
 ↓
FastAPI API Endpoint
 ↓
Transaction Parser
 ↓
Data Quality Agent
 ↓
Feature Engineering Agent
 ↓
Neo4j Graph Lookup
 ↓
GNN Graph Score
 ↓
ML Fraud Score
 ↓
Policy Decision
 ↓
Audit Logging
 ↓
LLM Explanation
 ↓
Database Storage
 ↓
Frontend Results
```

---

## 📊 Example Input CSV

```csv
transaction_id,user_id,device_id,card_id,ip_address,merchant_id,amount,timestamp,channel,country
T1001,U101,D501,C9001,192.168.1.10,M300,120.50,2026-05-30 10:45:00,web,US
T1002,U102,D501,C9002,192.168.1.10,M301,980.00,2026-05-30 02:15:00,mobile,US
T1003,U103,D777,C9003,10.0.0.21,M999,1500.00,2026-05-30 03:30:00,web,IN
```

---

## 📤 Example Output

```json
{
  "transaction_id": "T1002",
  "ml_score": 0.64,
  "gnn_graph_score": 0.78,
  "neo4j_graph_risk": 0.72,
  "final_risk": 0.73,
  "decision": "REVIEW",
  "reason_codes": [
    "DEVICE_SHARED_BY_MULTIPLE_USERS",
    "HIGH_GRAPH_RISK",
    "UNUSUAL_TRANSACTION_TIME"
  ],
  "explanation": "This transaction was marked REVIEW because the device and IP address are shared across multiple users, and the transaction occurred during a higher-risk time window."
}
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/pdreddy24/agentic-gnn-fraud-platform.git
cd agentic-gnn-fraud-platform
```

---

### 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate it:

```bash
# Windows
venv\Scripts\activate
```

```bash
# macOS / Linux
source venv/bin/activate
```

---

### 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

---

### 5. Start Neo4j

If using Docker:

```bash
docker compose up -d neo4j
```

Or start Neo4j manually using Neo4j Desktop.

---

### 6. Run the FastAPI Backend

```bash
uvicorn app.main:app --reload
```

Backend will run at:

```text
http://localhost:8000
```

FastAPI Swagger docs:

```text
http://localhost:8000/docs
```

---

### 7. Run the React Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at:

```text
http://localhost:3000
```

---

### 8. Optional: Run Streamlit Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

Dashboard will run at:

```text
http://localhost:8501
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/signup` | Create a new user account |
| `POST` | `/auth/login` | Login and get authentication token |
| `GET` | `/auth/me` | Get current logged-in user |
| `POST` | `/uploads/predict-file` | Upload CSV and run fraud prediction |
| `GET` | `/uploads/history` | View upload history |
| `GET` | `/uploads/{batch_id}/predictions` | View predictions for a specific batch |
| `GET` | `/uploads/compare/{current_batch_id}/{previous_batch_id}` | Compare two uploaded batches |

---

## 🧠 Why This Approach Works

This system works because it combines different types of fraud intelligence.

### Traditional ML

Traditional ML detects transaction-level patterns such as:

- High amount
- Unusual transaction time
- Risky channel
- Suspicious country
- Abnormal user behavior

### Neo4j Graph Intelligence

Neo4j detects explainable relationship risks such as:

- Shared devices
- Shared cards
- Shared IP addresses
- Risky merchants
- Connected suspicious users

### Graph Neural Network

The GNN-style scoring layer learns from connected entities and can detect suspicious fraud rings that may not be visible from individual rows.

### Agentic Workflow

The agent-based design makes the system modular, explainable, and easier to extend.

Each agent has a clear role:

```text
DataQualityAgent      → validates input
FeatureAgent          → creates ML features
Neo4jGraphAgent       → analyzes graph relationships
GNNGraphAgent         → scores graph risk
MLScoringAgent        → scores transaction risk
PolicyAgent           → makes final decision
AuditAgent            → records decision trace
ExplanationAgent      → explains result
```

---

## 🧪 Example Use Case

A fraud analyst uploads a CSV containing recent transactions.

The system detects that one transaction has:

```text
High amount
Night-time activity
Shared device
Shared IP address
Risky merchant history
High graph risk score
```

The final output is:

```text
Decision: REVIEW
```

The explanation says:

```text
This transaction was marked REVIEW because it occurred during a high-risk time window, used a device shared by multiple users, and was connected to a merchant with elevated fraud risk.
```

This helps the analyst quickly understand why the transaction needs review.

---

## 📈 Business Relevance

This type of system can be useful for:

- Banking
- Fintech
- Payment processing
- E-commerce
- Insurance
- Crypto exchanges
- Digital lending
- Online marketplaces

Business value:

- Detect suspicious transactions
- Identify fraud rings
- Reduce manual review workload
- Help analysts prioritize risky activity
- Improve fraud explainability
- Support audit and compliance workflows

---

## 📚 What I Learned

This project helped me understand that real-world AI systems require more than just model training.

Key learnings:

- Designing a full-stack AI application
- Building APIs with FastAPI
- Creating a frontend workflow with React
- Modeling fraud data as a graph
- Using Neo4j for relationship analysis
- Combining GNN scoring with traditional ML scoring
- Building modular agent workflows
- Adding auditability and explainability
- Using LLMs for explanations instead of decision-making

The biggest takeaway:

```text
Fraud detection is not only a prediction problem.
It is also a graph problem, a system design problem, and an explainability problem.
```

---

## 🔮 Future Improvements

Future improvements include:

- Real-time transaction scoring
- Analyst feedback loop
- Model retraining from feedback
- Precision, recall, F1-score, and ROC-AUC dashboard
- Interactive Neo4j graph visualization
- Model drift monitoring
- Data drift monitoring
- Role-based access control
- Cloud deployment
- CI/CD pipeline
- More advanced GNN architectures
- Better fraud reason-code generation

---

## 📸 Suggested Screenshots

Add screenshots in this order:

1. Architecture diagram
2. Frontend login page
3. CSV upload screen
4. Prediction results table
5. Risk score output
6. LLM explanation output
7. Upload history page
8. Batch comparison page
9. Neo4j graph visualization
10. FastAPI Swagger docs

---

## 🧾 Case Study Summary

This project demonstrates how modern fraud detection can combine graph intelligence, machine learning, and explainable AI.

By combining GNN-based graph scoring, Neo4j relationship analysis, traditional ML models, FastAPI APIs, React frontend, and LLM explanations, this platform shows how AI systems can be designed to be both powerful and understandable.

The final result is a full-stack fraud detection platform that can process transaction data, identify suspicious patterns, generate risk scores, classify transactions, and explain decisions in human-readable language.

---

## 🏷️ Keywords

```text
Fraud Detection
Graph Neural Networks
Neo4j
Machine Learning
FastAPI
React
LangGraph
LLM
Explainable AI
Python
Scikit-learn
Graph Intelligence
Financial AI
Risk Scoring
```

---
<img width="2210" height="1208" alt="Screenshot 2026-05-29 180442" src="https://github.com/user-attachments/assets/e5dc8a1e-589a-402d-a864-461d231e298e" />


## 👨‍💻 Author

Built by Deekshitha Reddy Palvai
Demo: https://agentic-gnn-fraud-platform.vercel.app/ 
LinkedIn: https://www.linkedin.com/in/deeksh596/

---




