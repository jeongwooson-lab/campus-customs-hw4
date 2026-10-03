# Campus Customs — VS Code handoff

## Read this first

Continue work in this folder: `/Users/letsroll/Desktop/MBA/03_Coursework/AI Class/homework/hw-4/hw4`. The user later authorized publishing the code to a public GitHub repository for submission preparation. The real API key is in `.env`; **do not print it, paste it into chat, logs, screenshots, or commit it**. `.env`, `data/`, the database, and source product images are ignored by Git.

The assignment asks for a Campus Customs merchandise site with a React/Vite/TypeScript front end, FastAPI + PydanticAI backend, SQLite catalogue/inventory/users, accounts, chat search that updates product cards, chat memory, evidence screenshots, an audit trail, and documentation. Problem 6 (supplied later) specifically requires real description, price, and stock tools with clear sold-out answers. The user also requested three cute puppies that follow the desktop mouse.

## Current implementation

- `frontend/src/main.tsx` has Home, Products, About Us, login, registration, item detail pages, category/search/price controls, and a floating chat. `/api/chat` returns `{reply, products}`; matching cards appear in chat and on the Products page, and link to the detail page.
- `frontend/src/PuppyTrail.tsx` and `frontend/src/style.css` add three animated SVG puppies. The overlay ignores pointer events and is hidden on touch devices and for reduced-motion users. Preview: `output/puppy_preview.png`.
- `backend/main.py` serves products/images, account routes, chat/history routes, and `/api/health`. It loads `.env` from the project root. Signed session tokens identify users. New account passwords use 600,000-round PBKDF2; old seed hashes still verify.
- `backend/tools.py` reads the supplied catalogue and size inventory with parameterized SQLite queries, searches products, and creates `chat_messages` if a fresh data pack lacks it.
- `backend/agent.py` builds the PydanticAI agent. `search_catalogue` and `check_product` are its tools. `backend/models.py` defines API and agent types. `backend/prompts/prompt.md` requires database-grounded price and stock answers and clear sold-out statements.
- The chat has a database-grounded fallback when the model call fails. Authenticated chats save/reload from SQLite; guests do not persist history. `output/audit_trail.json` records chat/tool activity and must not be wiped.
- `output/harness.md`, `output/usability.md`, `output/design.md`, `output/app_check.html`, `AI_prompts.md`, and `README.md` cover assignment write-ups. Screenshots are in `output/app_check_images/`.

## Local setup and checks already done

The local data pack is at `/Users/letsroll/Downloads/data`. `hw4/data` is an ignored symlink to it. It contains 102 catalogue items, 612 size inventory rows, user accounts, and product images. The seed login is documented in `README.md`. Dependencies are installed in `.venv` and `frontend/node_modules`. Start the servers in separate terminals:

```bash
cd '/Users/letsroll/Desktop/MBA/03_Coursework/AI Class/homework/hw-4/hw4/backend'
../.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

```bash
cd '/Users/letsroll/Desktop/MBA/03_Coursework/AI Class/homework/hw-4/hw4/frontend'
npm run dev
```

Site: `http://127.0.0.1:5173/`; API health: `http://127.0.0.1:8000/api/health`. Both returned HTTP 200 at handoff. Existing Codex server processes may still occupy ports 5173 and 8000; reuse them or stop them before starting another copy. `npm run build` passed. Browser checks passed for the seed login, real price/stock, hoodie search returning eight clickable cards, navigation from a chat result to its detail page, the product filter, and puppies not blocking links. A fresh-copy database test passed registration, seed/new login, automatic chat table creation, eight chat cards, and saved history. `pydantic_ai.models.test.TestModel` successfully exercised both tool registrations, though with its artificial arguments.

## Critical open issue: PydanticAI / OpenAI SDK path returns 401 through Portkey

**The Portkey key itself is valid.** Earlier advice that it was invalid because it lacked `pk-` was incorrect; do not repeat that assumption. Current `.env` has `PORTKEY_API_KEY` set, `OPENAI_API_KEY` blank, `PORTKEY_PROVIDER` blank, and `AI_MODEL=openai:gpt-5.6`. Keep the key secret.

Evidence from October 3, 2026:

1. `GET https://api.portkey.ai/v1/models` with the current key returned HTTP 200. The same endpoint without a key returned HTTP 401.
2. A minimal `POST https://api.portkey.ai/v1/chat/completions` using Python `httpx` returned HTTP 200 for `gpt-5.6` and a short “Reply OK” request. These raw variants all succeeded: Portkey key header only; Portkey key header plus `x-portkey-provider: openai`; Bearer key plus provider; and even placeholder Bearer plus Portkey key header plus provider.
3. The *same short request* through `openai.AsyncOpenAI` returned HTTP 401, `Portkey Error: Invalid API Key. Error Code: 03`. PydanticAI, which uses that SDK client in `backend/agent.py`, returns the same 401 and falls back to the database answer.
4. An SDK request hook confirmed it goes to `/v1/chat/completions`, sends the right Portkey key in `x-portkey-api-key`, sends `x-portkey-provider: openai`, and sends the expected JSON body. The SDK adds `Accept: application/json`, `User-Agent: AsyncOpenAI/Python 3.24.0`, and `x-stainless-*` headers. The cause of the divergent gateway behavior is not yet isolated. Raw `httpx.AsyncClient` also succeeds, so this is not simply synchronous versus asynchronous HTTP.

### Next debugging steps

1. Compare a successful raw `httpx` request with the SDK request one header at a time, especially `Accept`, `User-Agent`, and `x-stainless-*`. Keep all credential values redacted. Test with a tiny request so it does not incur significant cost.
2. Fix `backend/agent.py` so PydanticAI can use the working Portkey route. One likely route is a custom `httpx.AsyncClient` request hook or transport that normalizes the SDK-only headers before the request is sent; validate the exact cause first. Another option is a Portkey-supported OpenAI-compatible client/provider setup.
3. Test an actual PydanticAI `agent.run(...)` with the saved key, then `/api/chat` end to end. Confirm a real price/stock question uses `check_product`, returns structured product cards, and logs `completed` rather than `model_unavailable`.
4. Update `output/app_check.html` and any write-up that says the screenshots used a fallback if new evidence is captured with the live model. Preserve existing audit records.
5. After any `.env` change, restart Uvicorn. `/api/health` currently reports only whether a key is present; it does **not** prove the model connection works.

Do not ask the user to create another key based solely on the old `pk-` assumption. The current key authenticated successfully and completed raw chat requests.

## Delivery state

Git is initialized with four local commits as of this handoff update. The user authorized a public GitHub repository after initially requesting local-only work. Check `git remote -v` and `git status` for the current publication state. Canvas submission requires posting the public repository URL to the course assignment.
