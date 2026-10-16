import os
import time

from openai import OpenAI

client = OpenAI(base_url="http://localhost:20128/v1", api_key=os.getenv("AURA_LLM_API_KEY", ""))


def test_openai_sdk():
    print("Testing OpenAI SDK with principal-combo...")
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model="principal-combo",
        messages=[{"role": "user", "content": "Teste rápido de conexão. Responda apenas 'OK'."}],
        max_tokens=20,
    )
    t1 = time.perf_counter()
    print(f"Time: {t1 - t0:.2f}s")
    print("Content:", resp.choices[0].message.content)
    print("Model in response:", resp.model)

    print("\nTesting OpenAI SDK Tool Calling...")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "consultar_saldo_milhas",
                "description": "Consulta saldo de milhas",
                "parameters": {
                    "type": "object",
                    "properties": {"customer_id": {"type": "string"}},
                    "required": ["customer_id"],
                },
            },
        }
    ]
    t0 = time.perf_counter()
    resp_tool = client.chat.completions.create(
        model="principal-combo",
        messages=[{"role": "user", "content": "Verifique as milhas de CUST-1234"}],
        tools=tools,
        tool_choice="auto",
    )
    t1 = time.perf_counter()
    print(f"Time: {t1 - t0:.2f}s")
    print("Tool calls:", resp_tool.choices[0].message.tool_calls)
    if resp_tool.choices[0].message.tool_calls:
        tc = resp_tool.choices[0].message.tool_calls[0]
        print(f"Function called: {tc.function.name} with args: {tc.function.arguments}")


if __name__ == "__main__":
    test_openai_sdk()
