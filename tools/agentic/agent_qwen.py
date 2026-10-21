#!/usr/bin/env python3
"""Qwen Code agent wrapper for the CVDP agentic workflow.

Counterpart of the official claude-code-agent wrapper: reads /code/prompt.json, prepends the same benchmark
workspace rules, and runs Qwen Code headless in /code against an OpenAI-compatible endpoint. The event stream
(stream-json) goes to stdout so token usage and turns end up in the agent log.
Environment: QWEN_MODEL, OPENAI_BASE_URL, OPENAI_API_KEY; optional CVDP_EXTRA_INSTRUCTIONS_B64 (text placed before the task).
"""
import json, os, subprocess, sys

RULES = """Benchmark workspace rules:
- Work inside /code and use the task prompt plus repository files to infer the required deliverables.
- Modify only project files needed for the task. The benchmark does not provide additional expected solution paths beyond the task and repository content.
- Do not modify benchmark infrastructure or generated artifacts, including prompt.json, Docker compose files, run scripts, hidden/reference solution files, run directories, logs, caches, or simulator build outputs.
- Do not alter benchmark harness infrastructure or generated output to force a passing score. If the task asks for RTL, verification code, documentation, assertions, or testbench changes, make those requested project changes directly.
"""


def main():
    print("Starting Qwen Code agent...")
    task = json.load(open("/code/prompt.json")).get("prompt", "")
    if not task:
        print("No task found in prompt.json. Exiting."); sys.exit(1)
    extra = ""
    if os.environ.get("CVDP_EXTRA_INSTRUCTIONS_B64"):  # optional trial instructions, recorded in the run's protocol.json
        import base64
        extra = base64.b64decode(os.environ["CVDP_EXTRA_INSTRUCTIONS_B64"]).decode() .strip() + "\n\n"
        print(f"Extra instructions: {len(extra)} characters")
    task = f"{RULES}\n{extra}Task:\n{task}"
    env = os.environ.copy()
    env["HOME"] = "/tmp/qwen-home"; os.makedirs(env["HOME"], exist_ok=True)
    # Agent settings for benchmark runs:
    # - managed auto-memory off: Qwen Code otherwise makes an extra model call after each task to extract
    #   "durable memories"; the benchmark must not accumulate experience and the call only adds overhead.
    # - QWEN_CONTEXT_WINDOW (optional): tell Qwen Code the model's real context limit so its built-in
    #   conversation compaction can trigger (it otherwise assumes a much larger window and never compacts).
    settings = {"memory": {"enableManagedAutoMemory": False, "enableManagedAutoDream": False, "enableAutoSkill": False}}
    if env.get("QWEN_CONTEXT_WINDOW"):
        settings["model"] = {"generationConfig": {"contextWindowSize": int(env["QWEN_CONTEXT_WINDOW"])}}
    # QWEN_REQUEST_TIMEOUT_MS (optional): time limit for one model request. Without it a single long
    # answer (several minutes of reasoning on a slow model) is cut off after about 10 minutes and retried
    # from the start, which can repeat without end.
    if env.get("QWEN_REQUEST_TIMEOUT_MS"):
        settings.setdefault("model", {}).setdefault("generationConfig", {})["timeout"] = int(env["QWEN_REQUEST_TIMEOUT_MS"])
    # QWEN_TEMPERATURE (optional): sampling temperature sent with every request. Without it the request
    # carries no temperature and the model's own default applies (1.0 for the Qwen models used here).
    if env.get("QWEN_TEMPERATURE"):
        settings.setdefault("model", {}).setdefault("generationConfig", {}).setdefault("samplingParams", {})["temperature"] = float(env["QWEN_TEMPERATURE"])
    # QWEN_MAX_TOKENS (optional): upper limit of the output (reasoning included) of one model request.
    if env.get("QWEN_MAX_TOKENS"):
        settings.setdefault("model", {}).setdefault("generationConfig", {}).setdefault("samplingParams", {})["max_tokens"] = int(env["QWEN_MAX_TOKENS"])
    # QWEN_PRESENCE_PENALTY / QWEN_FREQUENCY_PENALTY / QWEN_REPEAT_PENALTY (optional): penalties on repeated tokens, sent with every request.
    for var, key in (("QWEN_PRESENCE_PENALTY", "presence_penalty"), ("QWEN_FREQUENCY_PENALTY", "frequency_penalty"), ("QWEN_REPEAT_PENALTY", "repeat_penalty")):
        if env.get(var):
            settings.setdefault("model", {}).setdefault("generationConfig", {}).setdefault("samplingParams", {})[key] = float(env[var])
    # QWEN_REASONING_EFFORT (optional): thinking level sent with every request (the model lists: false, low, medium, xhigh).
    if env.get("QWEN_REASONING_EFFORT"):
        settings.setdefault("model", {}).setdefault("generationConfig", {}).setdefault("samplingParams", {})["reasoning_effort"] = env["QWEN_REASONING_EFFORT"]
    # Without a version marker Qwen Code treats the file as an old-format file and rewrites it, dropping "model".
    settings["$version"] = 4
    os.makedirs(os.path.join(env["HOME"], ".qwen"), exist_ok=True)
    with open(os.path.join(env["HOME"], ".qwen", "settings.json"), "w") as f:
        json.dump(settings, f)
    print("Qwen Code settings:", json.dumps(settings))
    # --include-partial-messages: the answer (reasoning included) is written to the log piece by piece while it is
    # being produced, so a supervisor can follow it live.
    cmd = ["qwen", "--yolo", "--output-format", "stream-json", "--include-partial-messages", "-m", env["QWEN_MODEL"],
           "--openai-base-url", env["OPENAI_BASE_URL"], "--openai-api-key", env.get("OPENAI_API_KEY", "ollama")]
    if env.get("CVDP_QWEN_OPENAI_LOG"):  # debugging aid: dump raw API requests/responses
        cmd += ["--openai-logging", "--openai-logging-dir", env["CVDP_QWEN_OPENAI_LOG"]]
    print("Command:", " ".join(cmd[:6]), "..."); print(f"Task length: {len(task)} characters"); sys.stdout.flush()
    sys.exit(subprocess.run(cmd, input=task, text=True, env=env, cwd="/code").returncode)


if __name__ == "__main__":
    main()
