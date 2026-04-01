# learning-assist-be

FastAPI backend for the Agentic Coding IDE MVP.

## Judge0 configuration

Judge0 execution is hardcoded in backend configuration.

The backend submits code using `wait=false` and polls submission status by token.

## LLM configuration (OpenAI-compatible Bedrock endpoint)

Set this secret in `.env`:

```bash
OPENAI_API_KEY=your_bedrock_mantle_token
```

## Local setup (without Docker)

```bash
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Local setup (Docker compose)

```bash
copy .env.example .env
docker compose up --build backend
```

This command starts the API on `http://localhost:8000`.

## Single-container deploy (no compose)

The image now bundles the RDS cert at `/certs/global-bundle.pem`, so TLS verification works without a bind mount.

```bash
docker build -t learning-assist-be .
docker run --rm -p 8000:8000 --env-file .env learning-assist-be
```

## API quick check

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/problems
```
