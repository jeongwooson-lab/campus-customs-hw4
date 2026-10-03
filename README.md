# Campus Customs

A Yale-inspired merchandise demo built with React, Vite, TypeScript, FastAPI, SQLite, and PydanticAI. Shoppers can browse 102 supplied products, inspect live size stock, create accounts, and chat about merchandise. Chat searches return structured product cards that open the same detail pages as catalogue cards.

## Setup

1. Download the course data pack and place `campus_customs.db` and `products/` inside `hw4/data/`. The database and images are deliberately excluded from Git.
2. Make a virtual environment: `python3 -m venv .venv`, then install `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`. Set `DATA_DIR` to the absolute path of your data folder. Enter either a direct OpenAI key in `OPENAI_API_KEY`, or a Portkey key in `PORTKEY_API_KEY` and its provider slug in `PORTKEY_PROVIDER`. Never commit `.env`.
4. From `backend/`, run `../.venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000`.
5. From `frontend/`, run `npm install` and `npm run dev`. Open `http://127.0.0.1:5173`.

The default model is `gpt-5.6` through either the direct OpenAI endpoint or the Portkey OpenAI-compatible gateway. Set `AI_MODEL` if your authorized provider uses a different model name. If a model call is unavailable, chat uses a database-grounded local answer so product search and stock checks still work. `/api/health` reports whether the data pack and an AI key are configured; it does not validate credentials.

The data pack includes a seed account: `test@campuscustoms.yale.edu` / `password`. This is for local testing only. The new-account form requires an eight-character password.

## API and project files

- `/api/products` and `/api/products/{product_id}` return catalogue data with live inventory.
- `/api/register`, `/api/login`, and `/api/me` handle accounts and signed sessions.
- `/api/chat` returns `{reply, products}`; `/api/history` loads the logged-in shopper's messages.
- `backend/agent.py`, `models.py`, `tools.py`, and `prompts/prompt.md` contain the agent system.
- `output/harness.md` explains the schema and design; `output/app_check.html` holds browser evidence.

The original Yale Bulldog Blue storefront informed the broad product groupings and campus feel. Home and About copy here is original. This is a course demo, not an official Yale store or checkout.

## Assignment notes

Problem 6 was supplied separately after the initial file and is covered by the product and stock tools. The student chose to keep this project local, so it has not been published to GitHub or submitted to Canvas.
