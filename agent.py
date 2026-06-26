from dotenv import load_dotenv; load_dotenv()
import anthropic
import json
from pathlib import Path
from resolve import load_people, resolve_people

client = anthropic.Anthropic() # new instance of our model
MODEL = "claude-sonnet-4-6" # the specific Anthropic model we're using
MAX_STEPS = 6 # MAX_STEPS can be anything -- we don't want our loop to run forever; 
              # but in a larger corporate context, you'd want to base this off of tokens/budget 
              # since 6 small calls and 6 large calls can mean two different things.

# This is a simple set of instructions for what our model should do
SYSTEM = (
    "You are a company-research agent. Answer questions using ONLY the "
    "provided tools and documents.\n"
    "HARD RULES:\n"
    "1. Always use the tools to find information before answering. "
    "Never answer from memory.\n"
    "2. Cite the source file in brackets after every factual claim, "
    "e.g. [email_001.txt]. Every fact needs a source.\n"
    "3. If the documents do not contain the answer, say so plainly. "
    "Do not guess or invent information."
)
         

# TOOLS = the "menu" handed to the model. A list of tool descriptions (not code).
# The model reads this to know what tools exist and how to call them.
#
# Each tool dict has three parts:
#   name         - the tool's identifier; the model sends this back to call it,
#                  and execute_tool() matches on it.
#   description  - plain-English "what it does / when to use it." This is how the
#                  model DECIDES whether to call the tool. Write it well.
#   input_schema - the required shape of the arguments (JSON Schema). Forces the
#                  model to send valid inputs (here: an object with a "query" string).
#
# TOOLS only DESCRIBES. The real work lives in execute_tool() below.
#   TOOLS        -> passed as tools=TOOLS, the model reads it
#   execute_tool -> your code that actually runs when a tool is called
TOOLS = [
    {
        "name": "search_docs",
        "description": "Search company documents. Returns matching snippets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for"},
            },
            "required": ["query"],
        },
    },

    {
        "name": "resolve_people",
        "description": "Resolve and merge people records into canonical entities "
                       "(collapses name/company variants by email). Use to identify "
                       "who a person is across documents.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

from pathlib import Path

# --- Ingestion: read every file in sample_docs/ into memory, ONCE at startup ---
DOCS_DIR = Path("sample_docs")

def load_docs():
    docs = []
    for path in sorted(DOCS_DIR.iterdir()):
        if path.is_file():
            docs.append({"name": path.name, "text": path.read_text()})
    return docs

DOCS = load_docs()   # loaded once when the program starts, not per-query
                     # DOCS stores dicts, not words. 



def execute_tool(name, tool_input):
    if name == "search_docs":
        query = tool_input["query"] # just the search term. tool_input = {"query": "Acme"} -> tool_input[query] = "Acme"
        results = []
        for doc in DOCS: 
            if query.lower() in doc["text"].lower():
                results.append(f"[{doc['name']}] {doc['text']}") # putting snippet in results--including filename so we can cite it later
        return results
    
    if name == "resolve_people":
        return resolve_people(load_people())
    
    raise ValueError(f"Unknown tool: {name}")


def run_agent(question):
    messages = [{"role": "user", "content": question}] # messages is the only form of memory for the model--it's wiped clean through every
                                                       # iteration of the loop. every create() call is stateless, so it reads through
                                                       # the entire transcript + the tool data from messages and moves forward. 
                                                       # if you handed the output straight to the user instead of calling create() again
                                                       # the stuff would be in an array--which a user wouldn't know what to make of. 

    for _ in range(MAX_STEPS): # calls create() MAX_STEPS times to read the data and turn it into English. every time you call create()
                               # the model either decides if it has an answer, or it will ask for more data by calling another tool 
        # TODO 1: call the model with MODEL, max_tokens, SYSTEM, TOOLS, messages
        resp = client.messages.create(model = MODEL, max_tokens = 1024,
                                      system = SYSTEM, tools = TOOLS, messages = messages)

        # if resp.stop_reason is NOT "tool_use", the model is done.
        #         return the text. (text lives in resp.content blocks where .type == "text")
        if resp.stop_reason != 'tool_use':
            return "".join(b.text for b in resp.content if b.type == "text")
        

        # otherwise, the model wants a tool.
        messages.append({"role":"assistant","content":resp.content}) #records what the model said

        results = []
        for b in resp.content:
            if b.type == "tool_use": #skips any text blocks--only acts on tool requests
                output = execute_tool(b.name, b.input) #returns a list of snippets
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(output)}) 
                # json.dumps(output) converts the python object into a json-formatted string (List/dict -> string)
                # tool_use_id maps each request to its results to know which request got which result. helps with parllel operations
                # this way the model can know what to do down the road (get more data, give the user what they're asking for)
        
        messages.append({"role": "user", "content": results}) # appends all the results as one user message

    return "Stopped: hit max steps." # loop is done


if __name__ == "__main__":
    print(run_agent(input("Ask: ")))