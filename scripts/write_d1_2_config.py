import pathlib
import yaml

config_path = pathlib.Path("config.yaml")
config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

config["llm"] = {
    "default_provider": "gemini",
    "default_model": "gemini/gemini-2.0-flash",
    "fallback_model": "openai/gpt-4.1",
    "models": {
        "gemini": "gemini/gemini-2.0-flash",
        "openai": "openai/gpt-5-mini",
        "deepseek": "deepseek/deepseek-reasoner",
    },
    "cache_enabled": True,
    "max_retries": 3,
    "temperature": 0.3,
}

config.setdefault("storage", {}).update({
    "logs_dir": "logs",
    "exports_dir": "exports",
    "pdf_archive_dir": "pdf-archive",
    "local_fallback": "logs",
})

out = yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False)
config_path.write_text(out, encoding="utf-8")
print(f"Updated: {config_path} ({config_path.stat().st_size} bytes)")
