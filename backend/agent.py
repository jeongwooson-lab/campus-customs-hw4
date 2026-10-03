import os
from pathlib import Path
from models import AgentDeps
from tools import get_product, search_products

PROMPT = (Path(__file__).parent / 'prompts' / 'prompt.md').read_text()


def make_agent():
    from pydantic_ai import Agent, RunContext
    model_name = os.getenv('AI_MODEL', 'openai:gpt-5.6').split(':')[-1]
    if os.getenv('PORTKEY_API_KEY'):
        from openai import AsyncOpenAI
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider
        client = AsyncOpenAI(api_key=os.environ['PORTKEY_API_KEY'], base_url=os.getenv('PORTKEY_BASE_URL', 'https://api.portkey.ai/v1'), default_headers={'x-portkey-provider': os.getenv('PORTKEY_PROVIDER', 'openai')})
        model = OpenAIChatModel(model_name, provider=OpenAIProvider(openai_client=client))
    else:
        model = os.getenv('AI_MODEL', 'openai:gpt-5.6')
    agent = Agent(model, deps_type=AgentDeps, instructions=PROMPT, retries=1)

    @agent.tool
    def search_catalogue(ctx: RunContext[AgentDeps], query: str) -> list[dict]:
        """Search real merchandise by garment, team, school, college, or color. Max 8 results."""
        matches = search_products(query, 8)
        ctx.deps.tool_events.append({'tool':'search_catalogue','args':query[:120], 'result':f'{len(matches)} matches'})
        return [p.model_dump() for p in matches]

    @agent.tool
    def check_product(ctx: RunContext[AgentDeps], product_id: str) -> dict:
        """Read exact live price, color, description, and stock by size for one product ID."""
        product = get_product(product_id)
        ctx.deps.tool_events.append({'tool':'check_product','args':product_id[:120], 'result':'found' if product else 'missing'})
        return product.model_dump() if product else {'error':'Product not found'}

    return agent


async def answer(message: str, deps: AgentDeps, facts: list, history: list[dict]):
    if not (os.getenv('OPENAI_API_KEY') or os.getenv('PORTKEY_API_KEY')):
        return local_answer(message, facts), 'no_api_key'
    try:
        agent = make_agent()
        from pydantic_ai.usage import UsageLimits
        fact_text = '\n'.join(f'{p.name} (id {p.product_id}): ${p.price:.2f}; colors {", ".join(p.colors)}; stock ' + ', '.join(f'{s.size}={s.quantity}' for s in p.inventory) for p in facts[:8])
        prior = '\n'.join(f"{m['role']}: {m['content'][:500]}" for m in history[-6:])
        contextual = f'Current product page ID: {deps.product_id or "none"}. Shopper: {deps.user_name or "guest"} ({deps.user_email or "no email"}).'
        result = await agent.run(f'{contextual}\nRecent conversation:\n{prior}\nVerified database facts:\n{fact_text or "No matching catalogue records found."}\nShopper asks: {message}', deps=deps, usage_limits=UsageLimits(request_limit=6, tool_calls_limit=4))
        return str(result.output), 'completed'
    except Exception as exc:
        deps.tool_events.append({'tool':'agent_error','args':'model call', 'result':type(exc).__name__})
        return local_answer(message, facts), 'model_unavailable'


def local_answer(message, facts):
    if not facts:
        return "I couldn't find a matching item in our catalogue. Try a garment type, sport, college, or color."
    p = facts[0]
    lower = message.lower()
    if any(x in lower for x in ['stock','available','size','many','pink','color','price','much','this','it']):
        sizes = ', '.join(f'{s.size}: {s.quantity}' for s in p.inventory)
        colors = ', '.join(p.colors)
        return f'{p.name} is ${p.price:.2f}. Listed colors: {colors}. Current stock by size: {sizes}. ' + ('Pink is not listed for this item.' if 'pink' in lower and 'pink' not in colors.lower() else 'Stock can change, so check again before ordering.')
    return f'I found {len(facts)} matching items. Here are a few you can open for details: ' + ', '.join(f'{p.name} (${p.price:.2f})' for p in facts[:4]) + '.'
