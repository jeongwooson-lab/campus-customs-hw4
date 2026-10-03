# Usability improvements

1. **Live product search and category chips.** Shoppers can narrow the catalogue by name, sport, college, or garment type without scrolling through every item. This helps them reach a relevant product faster.
2. **Price sorting and visible size stock.** The catalogue can sort by price, and each detail page shows size quantities and sold-out states. This makes comparison easier and avoids a dead end on an unavailable size.
3. **Grounded database lookup.** The chat response includes exact catalogue records, prices, and inventory by size. This helps the business avoid made-up stock claims and gives shoppers cards they can open.
4. **Graceful model fallback with page context.** The assistant still answers from the local database if the model service is unavailable. It also knows the item page the shopper is viewing, so “this item” gets a specific answer instead of a guess.
