import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
from tools.mock_tools import check_service_status

# Load API key
load_dotenv()

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Model to use
MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "You are an IT incident assistant. You have access to a tool that "
    "checks the status of enterprise services. Use it when the user asks "
    "about a specific service's health or status"
)

# Tool schema
TOOLS = [
    {
        "name": "check_service_status",
        "description": "Check the current status, CPU usage, and last restart time of an enterprise service.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "The name of the service to check, e.g. 'nginx', 'database', 'auth-service'.",
                }
            },
            "required": ["service_name"]
        },
    }
]

# Map tool names to the actual Python functions that implement them
AVAILABLE_TOOLS = {
    "check_service_status": check_service_status,
}

def run_tool(tool_name, tool_input):
    "Execute the requested tool and return its result"
    func = AVAILABLE_TOOLS[tool_name]
    return func(**tool_input)

def chat():
    print("IT Incident Agent - Stage 3")
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

        while True:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Add Claude's response
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "tool_use":
                # Find the tool_use block(s) and run them
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"[Agent is calling tool: {block.name}({block.input})]")
                        result = run_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                
                # Send the tool result(s) back to Claude so Claude can continue
                messages.append({"role": "user", "content": tool_results})
                continue

            else:
                # Claude gave a normal text answer - print it and break the inner loop
                reply_text = "".join(
                    block.text for block in response.content if block.type == "text"
                )
                print(f"Agent: {reply_text}\n")
                break

        
if __name__ == "__main__":
    chat()