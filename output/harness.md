# Campus Customs system harness

## Database fields

The provided SQLite file lives in `data/campus_customs.db`. The app opens it through `DATA_DIR`; the data pack stays outside Git.

| Table | Field | Why it matters |
|---|---|---|
| `catalogue` | `product_id` | Stable ID for API URLs, chat matches, and inventory joins. |
| `catalogue` | `name` | Main product label and search text. |
| `catalogue` | `garment_type` | Category filters and search matching. |
| `catalogue` | `description` | Detail-page copy and grounded chat context. |
| `catalogue` | `colors` | JSON list of listed colors; prevents guessing a color. |
| `catalogue` | `search_tags` | JSON keywords for sports, colleges, and other searches. |
| `catalogue` | `image_file_path` | Local image path used by product cards. |
| `catalogue` | `price` | The price returned by the API and assistant. |
| `inventory` | `id` | Unique stock row. |
| `inventory` | `product_id` | Connects a size row to a catalogue item. |
| `inventory` | `size` | Size the shopper can ask about. |
| `inventory` | `quantity` | Live quantity; zero means sold out. |
| `users` | `id` | Account ID and owner of saved chat messages. |
| `users` | `name` | Display name, including the seed user. |
| `users` | `email` | Case-insensitive login ID and agent context. |
| `users` | `password_hash` | PBKDF2-SHA256 hash; plaintext is never stored. |
| `users` | `created_at` | Account creation timestamp. |
| `users` | `first_name` | Greeting and account form field. |
| `users` | `last_name` | Account form field. |
| `chat_messages` | `id` | Orders the conversation. |
| `chat_messages` | `user_id` | Limits history to the logged-in shopper. |
| `chat_messages` | `role` | Distinguishes shopper and assistant messages. |
| `chat_messages` | `content` | Saved message text. |
| `chat_messages` | `products_json` | Saves the exact cards returned with an assistant reply. |
| `chat_messages` | `created_at` | Time of the message. |

## Models and API contract

`Stock` contains size and quantity. `Product` packages an item, its colors/tags, image URL, exact price, size rows, and total stock. `UserPublic` leaves out the password hash. `AuthInput` and `RegisterInput` validate login/registration data, while `AuthResponse` carries the session token and public user. `ChatInput` limits messages to 2,000 characters and optionally carries the current product ID. `ChatResponse` has `reply` and `products`, so the front end can display search-result cards from the same API call. `ChatMessage` rebuilds stored conversations. `AgentDeps` supplies name, email, product ID, and an in-memory tool event list to PydanticAI.

## Auth and memory

Registration uses a random salt and PBKDF2-SHA256; login verifies with a constant-time comparison. The seed account uses the same stored hash format. The API returns a seven-day HMAC-signed token; only the local browser stores it. Authenticated messages are inserted into `chat_messages` and the last 40 are returned by `/api/history`. The agent receives the shopper's name and email as dependencies and up to six recent messages as context. Guests can chat without saved history. The front end sends the current product ID so “this one” means the item being viewed. The server validates that ID against the catalogue before using it.

## Tools and abilities

`search_catalogue` searches names, garment types, colors, descriptions, and tags, with a cap of eight cards. `check_product` reads an exact record with price and size stock. Product and inventory facts are queried from SQLite for each chat turn. The API returns structured products whether the model calls a tool or uses the already fetched facts, and the front end renders those as clickable cards. If a model key is absent or its request fails, a deterministic answer uses the same database facts and records the stop reason in the audit trail.

## Safety and specs

The prompt forbids invented price, availability, discounts, shipping claims, and orders. It treats chat and catalogue text as data rather than instructions and does not expose credentials, hashes, or other customers' messages. API input uses Pydantic validation; SQL statements use bound parameters. Search results are capped at eight in the chat path; the catalogue endpoint is capped at 102. The agent has one retry. The default model is `gpt-5.6`, configured by `AI_MODEL`; Portkey can use `PORTKEY_API_KEY` and `PORTKEY_PROVIDER` instead of a direct OpenAI key. The audit file is a JSON array that only grows by appending new records, preserving earlier entries across runs. Each record includes time, tool name, short arguments/result, and stop reason.

Run `cd backend && ../.venv/bin/uvicorn main:app --reload` and `cd frontend && npm run dev` in separate terminals after placing the data pack. The app lives at `http://127.0.0.1:5173` and the API at port 8000.
