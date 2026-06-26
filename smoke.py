from dotenv import load_dotenv; load_dotenv()
import anthropic
client = anthropic.Anthropic()
r = client.messages.create(model="claude-sonnet-4-6", max_tokens=256,
    messages=[{"role":"user","content":"Say hi in five words."}])
print(r.content[0].text)