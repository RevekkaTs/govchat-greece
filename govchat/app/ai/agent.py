import json
import os
from openai import OpenAI
from app.ai.tools import road_safety_tool, fires_tool, energy_tool

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "road_safety_tool",
            "description": "Get road accident statistics from Greek government data. Use for questions about traffic accidents, road safety, vehicle crashes in Greece.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Filter by year (optional)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fires_tool",
            "description": "Get forest fire data from Greek government data. Use for questions about wildfires, forest fires, burned areas in Greece.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Filter by year (optional)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "energy_tool",
            "description": "Search Greek energy data. Use for ANY question about ADMIE, the Greek electricity grid, energy production, energy consumption, renewable energy, electricity prices, or the Greek energy sector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query about Greek energy data"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

TOOL_MAP = {
    "road_safety_tool": road_safety_tool,
    "fires_tool": fires_tool,
    "energy_tool": energy_tool,
}


def _detect_language(text: str) -> str:
    for char in text:
        if 'Ͱ' <= char <= 'Ͽ' or 'ἀ' <= char <= '῿':
            return "Greek"
    return "English"


def run_agent(user_question: str, history: list[dict] | None = None) -> tuple[str, str | None]:
    """Run the agent and return (answer, domain)"""
    try:
        language = _detect_language(user_question)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are GovChat Greece, a helpful assistant that answers questions about Greek government open data. "
                    "IMPORTANT: Always use the available tools to answer questions — never rely on your own training knowledge for road safety, fires, or energy topics. "
                    "IMPORTANT: Use the conversation history to understand follow-up questions and pick the correct tool. "
                    f"IMPORTANT: You MUST reply in {language} only. Do not use any other language."
                )
            }
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_question})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="required"
        )

        message = response.choices[0].message
        domain = None

        if message.tool_calls:
            messages.append(message)
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                if domain is None:
                    domain = tool_name.replace("_tool", "")
                tool_fn = TOOL_MAP[tool_name]
                tool_result = tool_fn(**tool_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            return final_response.choices[0].message.content or "", domain

        return message.content or "", domain
    except Exception as e:
        return f"Sorry, I encountered an error processing your question: {str(e)}", None
