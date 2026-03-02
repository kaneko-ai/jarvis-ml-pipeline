import pathlib

env_path = pathlib.Path(".env")
content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""

additions = []
if "OPENAI_API_KEY" not in content:
    additions.append("# OpenAI (ChatGPT Plus)")
    additions.append("OPENAI_API_KEY=")
if "DEEPSEEK_API_KEY" not in content:
    additions.append("# DeepSeek (optional)")
    additions.append("DEEPSEEK_API_KEY=")
if "LLM_MODEL" not in content:
    additions.append("# Default LLM model for LiteLLM")
    additions.append("LLM_MODEL=gemini/gemini-2.0-flash")

if additions:
    new_content = content.rstrip() + "\n\n" + "\n".join(additions) + "\n"
    env_path.write_text(new_content, encoding="utf-8")
    print(f"Updated .env: added {len(additions)} lines")
else:
    print(".env already up to date")
