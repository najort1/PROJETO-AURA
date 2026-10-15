import os
import json
import time
import urllib.request
import urllib.error
import sys

BASE_URL = "http://localhost:20128/v1"
API_KEY = os.getenv("AURA_LLM_API_KEY", "")
MODEL = "principal-combo"

def make_request(method, url, data=None):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Aura-Investigation/1.0"
    }
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    
    start_time = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            elapsed = time.perf_counter() - start_time
            body_bytes = resp.read()
            body_str = body_bytes.decode("utf-8", errors="replace")
            try:
                body_json = json.loads(body_str)
            except Exception:
                body_json = None
            
            headers_dict = dict(resp.headers)
            return {
                "success": True,
                "status_code": resp.status,
                "elapsed_sec": round(elapsed, 4),
                "headers": headers_dict,
                "body_raw": body_str,
                "body_json": body_json,
                "error": None
            }
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - start_time
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = None
        return {
            "success": False,
            "status_code": e.code,
            "elapsed_sec": round(elapsed, 4),
            "headers": dict(e.headers),
            "body_raw": err_body,
            "body_json": err_json,
            "error": f"HTTPError: {e.code} {e.reason}"
        }
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        return {
            "success": False,
            "status_code": None,
            "elapsed_sec": round(elapsed, 4),
            "headers": {},
            "body_raw": None,
            "body_json": None,
            "error": f"Exception: {type(e).__name__}: {str(e)}"
        }

def run_tests():
    print("=" * 80)
    print("TESTE 1: GET /v1/models")
    print("=" * 80)
    res_models = make_request("GET", f"{BASE_URL}/models")
    print(f"Status: {res_models['status_code']}")
    print(f"Elapsed: {res_models['elapsed_sec']}s")
    print("Headers:", json.dumps(res_models['headers'], indent=2))
    if res_models['body_json']:
        print("Body JSON:", json.dumps(res_models['body_json'], indent=2))
    else:
        print("Body Raw:", res_models['body_raw'])
    if res_models['error']:
        print("Error:", res_models['error'])

    print("\n" + "=" * 80)
    print("TESTE 2: POST /v1/chat/completions (Mensagem Simples)")
    print("=" * 80)
    chat_payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Olá, quem é você?"}
        ],
        "temperature": 0.7,
        "max_tokens": 256
    }
    res_chat = make_request("POST", f"{BASE_URL}/chat/completions", chat_payload)
    print(f"Status: {res_chat['status_code']}")
    print(f"Elapsed: {res_chat['elapsed_sec']}s")
    print("Headers:", json.dumps(res_chat['headers'], indent=2))
    if res_chat['body_json']:
        print("Body JSON:", json.dumps(res_chat['body_json'], indent=2))
        try:
            choice = res_chat['body_json']['choices'][0]
            print("\n>>> Mensagem retornada:")
            print(choice.get('message', {}).get('content'))
        except Exception:
            pass
    else:
        print("Body Raw:", res_chat['body_raw'])
    if res_chat['error']:
        print("Error:", res_chat['error'])

    print("\n" + "=" * 80)
    print("TESTE 3: POST /v1/chat/completions (Com Tools / Function Calling)")
    print("=" * 80)
    tools_payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Por favor, consulte o saldo de milhas do cliente CUST-9999 e me informe."
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "consultar_saldo_milhas",
                    "description": "Consulta o saldo atual de milhas qualificáveis e categoria do cliente no programa Azul Fidelidade.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "ID do cliente no formato CUST-XXXX"
                            }
                        },
                        "required": ["customer_id"]
                    }
                }
            }
        ],
        "tool_choice": "auto",
        "temperature": 0.2,
        "max_tokens": 256
    }
    res_tools = make_request("POST", f"{BASE_URL}/chat/completions", tools_payload)
    print(f"Status: {res_tools['status_code']}")
    print(f"Elapsed: {res_tools['elapsed_sec']}s")
    print("Headers:", json.dumps(res_tools['headers'], indent=2))
    if res_tools['body_json']:
        print("Body JSON:", json.dumps(res_tools['body_json'], indent=2))
        try:
            msg = res_tools['body_json']['choices'][0]['message']
            tool_calls = msg.get('tool_calls')
            print("\n>>> Análise de suporte a Function Calling:")
            if tool_calls:
                print(">>> SUCESSO: O modelo retornou tool_calls nativo!")
                print("tool_calls:", json.dumps(tool_calls, indent=2))
            else:
                print(">>> AVISO: O modelo respondeu sem tool_calls.")
                print("Content:", msg.get('content'))
        except Exception as e:
            print("Erro ao analisar resposta:", e)
    else:
        print("Body Raw:", res_tools['body_raw'])
    if res_tools['error']:
        print("Error:", res_tools['error'])

if __name__ == "__main__":
    run_tests()
