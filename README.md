# company-context-agent

An AI agent that turns scattered company documents — emails, meeting notes, contact records — into cited, answerable context. It orchestrates tool calls on Claude to search documents, resolve entities across sources, and synthesize answers grounded in the source files.

## The problem

Company knowledge is spread across emails, notes, and spreadsheets, and the same entity shows up under different names everywhere — "Acme Pay," "Acme Payments, Inc.," and "acmepay.com" are one company; "Sarah Chen" and "S. Chen" are one person. Answering a simple question like *"who is this contact and what's our relationship with their company?"* means reading across all of it and reconciling the variants by hand. This agent does that reconciliation and answers the question with sources attached.

## How it works

The core is an agent loop, not a single model call. The model is given a set of tools, decides which to call, and the loop feeds results back until it has enough to answer:

1. **Agent loop** (`agent.py`) — sends the question plus available tools to Claude. When the model requests a tool, the loop executes it, returns the result, and re-calls the model. Repeats until the model produces a final answer. A step cap guards against runaway loops.
2. **Document search** (`search_docs`) — ingests every file in `sample_docs/` once at startup and returns matching snippets for a query, tagged with their source filename.
3. **Entity resolution** (`resolve.py`) — merges people records that share a stable key (email) into a single canonical entity, collapsing name and company variants. This runs as deterministic code rather than relying on the model to re-guess matches each query, so resolution is consistent and inspectable.
4. **Grounded synthesis** — the system prompt requires the model to use tools before answering, cite the source file after every factual claim, and say so plainly when the documents don't contain an answer rather than guessing.

## Stack

- Python
- Anthropic Claude API (`claude-sonnet-4-6`) for tool use / orchestration
- `python-dotenv` for secrets

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install anthropic python-dotenv
```

Create a `.env` file with an Anthropic API key (from console.anthropic.com):

```
ANTHROPIC_API_KEY=sk-ant-...
```

Run:

```bash
python agent.py
```

## Example

```
Ask: Who is S. Chen and what company are they with?

S. Chen is Sarah Chen (sarah.chen@acmepay.com), the Integration Lead and
Billing Contact for Acme Payments, Inc. — also referred to as Acme Pay.
The two names share an email address, confirming they are the same person.
[contacts.csv, email_002.txt]
```

The agent called `resolve_people` to merge the two contact records, cross-referenced the documents, and grounded each claim in a named source.

## Scope

This is a working prototype built against a small set of sample documents to demonstrate the architecture. The entity-resolution layer currently keys on email; 
the document search is keyword-based. Natural extensions are a relationship graph over resolved entities, semantic (embedding-based) retrieval for matching by meaning 
rather than exact terms, and additional source adapters beyond local files.
