"""
Each message you type is treated as a new incident
report and run through the full pipeline: triage -> diagnose -> retrieve
-> propose -> human approval -> execute.
"""

import uuid
from langgraph.types import Command
from graph.workflow import workflow

def handle_incident(user_message: str):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = workflow.invoke({"user_message": user_message}, config=config)

    if "__interrupt__" in result:
        interrupt_info = result["__interrupt__"][0].value
        print("\n" + interrupt_info["proposal"])
        print(f"\n{interrupt_info['question']}")

        answer = input("Your answer (yes/no): ").strip()
        final_result = workflow.invoke(Command(resume=answer), config=config)

        print(f"\n{final_result['action_result']}\n")
    else:
        print(f"\n{result['proposal']}\n")

def main():
    print("IT Incident Agent")
    print("Describe an incident (or type 'quit' to exit).\n")

    while True:
        user_input = input("Incident: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        handle_incident(user_input)


if __name__ == "__main__":
    main()