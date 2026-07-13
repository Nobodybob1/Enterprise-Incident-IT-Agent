import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load API key
load_dotenv()

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Model to use
MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "You are an IT incident assistant. For now you have no tools and no "
    "runbook knowledge - you're just a plain assistant. In later stages "
    "you'll gain the ability to search runbooks and check system status."
)

def chat():
    print("IT Incident Agent - Stage 1 (plain chat, no tools yet)")
    print ("Type 'quit' to exit.\n")

    # We keep the full message history so the model has conversational
    # context. Each entry is a dict with a role ("user" or "assistant")
    # and content (the text)
    messages = []

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        )

        # response.content is a list of content blocks. For a plain text reply (no tools involved yet),
        # there will be a single block with type "text"
        reply_text = "".join(block.text for block in response.content if block.type == "text")

        print(f"Agent: {reply_text}\n")

        # Add the assistant's reply to history so the next turn has context
        messages.append({"role": "assistant", "content": reply_text})

if __name__ == "__main__":
    chat()