# Setup Guide — First Time

Complete these steps once before you start your first niche.

---

## 1. Accounts to create (all free to start)

| Account | Link | Why you need it |
|---|---|---|
| Claude Code | https://claude.ai/code | Your AI assistant — runs the whole workflow |
| Printify | https://printify.com | Creates + ships your products |
| Etsy | https://etsy.com/sell | Where you sell |
| eRank | https://erank.com | Real keyword search volumes for Etsy |
| Firecrawl | https://www.firecrawl.dev | Scrapes competitor listings |

---

## 2. Install tools on your computer

You need Node.js and Python 3 already installed. Check:

```bash
node --version    # should print v18 or higher
python3 --version # should print 3.9 or higher
```

If you don't have them:
- Node.js: https://nodejs.org (download the LTS version)
- Python: https://www.python.org/downloads/

Then install the Firecrawl CLI:

```bash
npm install -g firecrawl
```

---

## 3. Clone this repo and install dependencies

```bash
git clone https://github.com/YOUR-REPO-URL etsy-pod-launcher
cd etsy-pod-launcher
npm install
```

---

## 4. Get your API keys

### Printify API token
1. Log in to Printify → https://printify.com/app/account/api
2. Click **Generate token**
3. Give it all scopes (shops, products, orders, uploads, catalog)
4. Copy the token — you'll only see it once

### Printify Shop ID
1. In Printify, go to your store
2. Look at the URL: `https://printify.com/app/store/products` — the number in the URL before `/products` is your shop ID
3. Or run this after you have your token:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" https://api.printify.com/v1/shops.json
   ```

### Firecrawl API key
1. Log in to Firecrawl → https://www.firecrawl.dev/app/api-keys
2. Click **Create API Key**
3. Copy the key (starts with `fc-`)

---

## 5. Configure your .env file

```bash
cp .env.example .env
```

Open `.env` and fill in your three values:

```
PRINTIFY_API_TOKEN=your_token_here
PRINTIFY_SHOP_ID=your_shop_id_here
FIRECRAWL_API_KEY=fc-your_key_here
```

---

## 6. Start the Printify bridge server

The bridge is a small local server that lets Claude Code talk to the Printify API safely.

```bash
npm start
```

You should see:
```
printify-bridge listening on http://localhost:3333
```

Leave this running in a terminal tab while you work. Test it:

```bash
curl http://localhost:3333/health
```

---

## 7. Set up Playwright MCP in Claude Code

Playwright lets Claude Code open a browser to scrape eRank keyword data.

Open Claude Code settings (gear icon → MCP Servers) and add:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

Or run this from terminal if Claude Code is installed:
```bash
claude mcp add playwright -- npx @playwright/mcp@latest
```

---

## 8. Open the project in Claude Code

Open this folder in Claude Code. Then just tell it:

> "I want to launch a [product type] on Etsy. Help me research the top 5 competitors."

Claude will walk you through the rest. See [WORKFLOW.md](WORKFLOW.md) for the full step-by-step.

---

## Quick test — make sure everything works

Run this sequence to confirm your setup is correct:

```bash
# 1. Server is healthy
curl http://localhost:3333/health

# 2. Printify connection works (should list your shop)
curl http://localhost:3333/api/shops

# 3. Firecrawl CLI works
firecrawl --version

# 4. Research script works (dry run)
python3 scripts/research-competitors.py --help
```

If any step fails, check your `.env` values and re-read the relevant section above.
