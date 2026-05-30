# Agentic GNN Fraud Detection Platform

A full-stack **Transactional Fraud Detection** platform that uses **Graph Neural Networks**, **Neo4j**, **Machine Learning**, and **LLM explanations** to detect suspicious financial transactions.

The system analyzes relationships between users, devices, cards, IP addresses, merchants, and transactions to classify each transaction as:

- ✅ `APPROVE`
- ⚠️ `REVIEW`
- 🚫 `BLOCK`

---

## 🚀 Overview

Fraud is not always visible in a single transaction.  
A transaction may look normal by amount or country, but it can become suspicious when connected to shared devices, repeated IP addresses, risky merchants, or multiple accounts.

This project combines graph intelligence and machine learning to identify hidden fraud patterns.

---

## 🧠 How It Works

```text
CSV Upload
 ↓
FastAPI Backend
 ↓
Data Validation
 ↓
Feature Engineering
 ↓
Neo4j Graph Analysis
 ↓
GNN Fraud Scoring
 ↓
ML Fraud Scoring
 ↓
Policy Decision
 ↓
LLM Explanation
 ↓
Final Result
```

---

## ✨ Features

- CSV transaction upload
- Fraud risk prediction
- Neo4j graph relationship analysis
- GNN-based fraud scoring
- Traditional ML scoring
- Final decision: `APPROVE`, `REVIEW`, or `BLOCK`
- LLM-based explanation
- Upload history
- Batch comparison
- React frontend
- FastAPI backend
- Docker support

---

## 🛠️ Tech Stack

- **Frontend:** React
- **Backend:** FastAPI, Python
- **Database:** SQLite, Neo4j
- **Machine Learning:** Scikit-learn
- **Graph AI:** Graph Neural Networks / GraphSAGE-style model
- **Agent Workflow:** LangGraph-style agents
- **LLM:** OpenAI API
- **DevOps:** Docker, Docker Compose

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




