import json
from pathlib import Path

transcript_path = Path(r"C:\Users\Anurodh\.gemini\antigravity\brain\0ae9d278-2bd6-44c9-b4f5-d295fe4b4adb\.system_generated\logs\transcript.jsonl")

with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)
        idx = d.get("step_index", 0)
        if 775 <= idx <= 805:
            tc = d.get("tool_calls", [])
            print(f"Step {idx}: type={d.get('type')}")
            for t in tc:
                print(f"   tool: {t.get('name')}, args={t.get('args')}")
            if d.get("type") == "GENERIC" and "content" in d:
                c = d["content"]
                print(f"   content preview: {c[:250]}...")
