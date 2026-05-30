FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir \
    fastapi==0.115.6 \
    uvicorn==0.34.0 \
    pandas==2.2.3 \
    numpy==2.2.1 \
    scikit-learn==1.6.0 \
    joblib==1.4.2 \
    pydantic==2.10.4 \
    neo4j==5.27.0 \
    python-dotenv==1.0.1 \
    langgraph \
    openai==2.14.0 \
    streamlit==1.41.1 \
    requests==2.32.3

RUN pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu

COPY . /app

EXPOSE 8002

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8002}"]
