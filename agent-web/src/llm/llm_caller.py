"""Bridge script: Node.js -> Python LiteLLM."""
import sys, json, os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from jarvis_core.llm.litellm_client import completion

def sanitize_text(text):
    """Remove surrogate characters and other non-encodable chars."""
    if not isinstance(text, str):
        return str(text)
    # Encode to utf-8 with surrogates replaced, then decode back
    return text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")

def main():
    raw_input = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    input_data = json.loads(raw_input)
    message = sanitize_text(input_data.get("message", ""))
    model = input_data.get("model", "gemini/gemini-2.0-flash")
    try:
        result = completion(message, model=model)
        clean_result = sanitize_text(result) if isinstance(result, str) else str(result)
        output = json.dumps({"success": True, "content": clean_result, "model": model}, ensure_ascii=False)
        sys.stdout.buffer.write(output.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")
        sys.stdout.buffer.flush()
    except Exception as e:
        error_msg = sanitize_text(str(e))
        output = json.dumps({"success": False, "error": error_msg, "model": model}, ensure_ascii=False)
        sys.stdout.buffer.write(output.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")
        sys.stdout.buffer.flush()

if __name__ == "__main__":
    main()
