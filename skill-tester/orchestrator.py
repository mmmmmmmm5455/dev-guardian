#!/usr/bin/env python3
"""
skill-tester Orchestrator — chains Agent 1 (Discovery) → Agent 2 (Execution) → Agent 3 (Repair)

Usage:
  python orchestrator.py --skills code-audit,caveman       # test specific skills
  python orchestrator.py --all                              # test all active skills
  python orchestrator.py --skills code-audit --run          # generate combined run prompt
  python orchestrator.py --skills code-audit --step 2       # generate prompt for a specific step
  python orchestrator.py --validate agent1_output.json      # validate an agent output file

Flow:
  Step 1: Generate Agent 1 input → user runs Agent 1 → saves discovery_*.json
  Step 2: Read Agent 1 output → generate Agent 2 input → user runs Agent 2 → saves execution_*.json
  Step 3: Read Agent 2 output → generate Agent 3 input → user runs Agent 3 → saves repair_*.json
"""

import json
import os
import sys
import uuid
import argparse
from datetime import datetime
from pathlib import Path


SKILL_TESTER_DIR = Path(__file__).parent.resolve()
SKILLS_DIR = Path.home() / ".claude" / "skills"
PROMPTS_DIR = SKILL_TESTER_DIR / "prompts"
SCHEMAS_DIR = SKILL_TESTER_DIR / "schemas"
OUTPUT_DIR = SKILL_TESTER_DIR / "test_output"


def gen_id():
    return f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def load_prompt(agent_name):
    """Load agent prompt template."""
    prompt_map = {
        "agent1": PROMPTS_DIR / "agent1_discovery.md",
        "agent2": PROMPTS_DIR / "agent2_execution.md",
        "agent3": PROMPTS_DIR / "agent3_repair.md",
    }
    path = prompt_map.get(agent_name)
    if not path or not path.exists():
        print(f"ERROR: Prompt file not found: {path}")
        return None
    return path.read_text(encoding="utf-8")


def validate_json_file(filepath, schema_name=None):
    """Basic validation that a JSON file is well-formed and has expected fields."""
    path = Path(filepath)
    if not path.exists():
        return False, f"File not found: {filepath}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Read error: {e}"

    # Schema-specific validation
    if "agent1_output" in str(filepath) or "discovery_" in str(filepath):
        required = ["discovery_id", "scanned_paths", "total_found", "skills"]
        missing = [f for f in required if f not in data]
        if missing:
            return False, f"Missing required fields: {missing}"
        return True, f"Valid Agent 1 output — {data.get('total_found', 0)} skills found"

    if "agent2_output" in str(filepath) or "execution_" in str(filepath):
        if "results" not in data:
            return False, "Missing 'results' array"
        return True, f"Valid Agent 2 output — {len(data.get('results', []))} results"

    if "agent3_output" in str(filepath) or "repair_" in str(filepath):
        required = ["repair_id", "repairs_applied", "unfixable_issues", "total_fixed", "total_unfixable"]
        missing = [f for f in required if f not in data]
        if missing:
            return False, f"Missing required fields: {missing}"
        return True, f"Valid Agent 3 output — {data.get('total_fixed', 0)} fixed, {data.get('total_unfixable', 0)} unfixable"

    return True, "Valid JSON"


def validate_outputs_consistency(agent2_output_path, agent3_output_path=None):
    """Cross-validate that agent outputs are consistent."""
    issues = []

    a2 = json.loads(Path(agent2_output_path).read_text(encoding="utf-8"))
    total_results = len(a2.get("results", []))
    failed = [r for r in a2.get("results", [])
              if r.get("function_test", {}).get("pass") == False
              or r.get("trigger_test", {}).get("pass") == False
              or r.get("structure_pass") == False]

    if agent3_output_path:
        a3 = json.loads(Path(agent3_output_path).read_text(encoding="utf-8"))
        fixed = a3.get("total_fixed", 0)
        unfixable = a3.get("total_unfixable", 0)
        total_issues = len(failed)
        if fixed + unfixable != total_issues:
            issues.append(
                f"Agent 3 total ({fixed}+{unfixable}={fixed + unfixable}) "
                f"!= Agent 2 issues ({total_issues})"
            )

    return issues


def step1_generate(skills, scan_paths=None):
    """Generate Agent 1 (Discovery) input."""
    if scan_paths is None:
        scan_paths = [str(SKILLS_DIR)]

    agent1_input = {
        "scan_paths": scan_paths,
        "filter": "all",
        "specific_skills": skills if skills else None,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    input_path = OUTPUT_DIR / f"agent1_input_{gen_id()}.json"
    input_path.write_text(json.dumps(agent1_input, indent=2, ensure_ascii=False), encoding="utf-8")

    return input_path, agent1_input


def step2_generate(agent1_output_path, token_measurement=True):
    """Generate Agent 2 (Execution) input from Agent 1 output."""
    agent2_input = {
        "execution_id": gen_id(),
        "discovery_output_path": str(Path(agent1_output_path).resolve()),
        "design_test_cases": True,
        "token_measurement_enabled": token_measurement,
    }

    input_path = OUTPUT_DIR / f"agent2_input_{agent2_input['execution_id']}.json"
    input_path.write_text(json.dumps(agent2_input, indent=2, ensure_ascii=False), encoding="utf-8")

    return input_path, agent2_input


def step3_generate(agent2_output_path, auto_fix=True, max_attempts=3):
    """Generate Agent 3 (Repair) input from Agent 2 output."""
    agent3_input = {
        "repair_id": gen_id(),
        "execution_output_path": str(Path(agent2_output_path).resolve()),
        "auto_fix_enabled": auto_fix,
        "max_auto_fix_attempts": max_attempts,
    }

    input_path = OUTPUT_DIR / f"agent3_input_{agent3_input['repair_id']}.json"
    input_path.write_text(json.dumps(agent3_input, indent=2, ensure_ascii=False), encoding="utf-8")

    return input_path, agent3_input


def print_agent_prompt(step, input_path, prompt_template):
    """Print the prompt the user should give to the Agent tool."""
    input_json = Path(input_path).read_text(encoding="utf-8")

    agent_configs = {
        1: {"name": "Skill Discovery & Structure Agent", "subagent_type": "general-purpose", "desc": "Scan skills, validate structure, output discovery JSON"},
        2: {"name": "Skill Execution & Quality Agent", "subagent_type": "general-purpose", "desc": "Test skills, score quality, output execution JSON"},
        3: {"name": "Skill Repair & Evolution Agent", "subagent_type": "general-purpose", "desc": "Diagnose failures, auto-fix, output repair JSON"},
    }

    cfg = agent_configs[step]

    print(f"""
{'='*70}
STEP {step}: {cfg['name']}
{'='*70}

Input file: {input_path}
Input content:
{input_json}

---

Copy the prompt below and send it to the Agent tool:

Agent(
  description: "{cfg['desc']}",
  subagent_type: "{cfg['subagent_type']}",
  prompt: \"\"\"
{_indent(prompt_template.strip(), "    ")}

---

IMPORTANT: Use Read tool to read the input JSON from this path:
  {input_path}

Then follow your process steps. Write output JSON to:
  {OUTPUT_DIR.as_posix()}/<type>_<id>.json

Use caveman style. Every finding must have evidence.
\"\"\")
""")
    # Print output path expectation
    output_patterns = {
        1: f"discovery_*.json in {OUTPUT_DIR}",
        2: f"execution_*.json in {OUTPUT_DIR}",
        3: f"repair_*.json in {OUTPUT_DIR}",
    }
    print(f"Expected output: {output_patterns[step]}")


def _indent(text, prefix):
    return prefix + text.replace("\n", "\n" + prefix)


def cmd_generate(args):
    """Generate input files and print prompts for all steps."""
    skills = None
    if args.skills:
        skills = [s.strip() for s in args.skills.split(",")]

    # Step 1
    input1_path, _ = step1_generate(skills)
    print(f"\n[Step 1 ready] Input: {input1_path}")
    if args.step == 1 or args.step is None:
        prompt1 = load_prompt("agent1")
        if prompt1:
            print_agent_prompt(1, input1_path, prompt1)

    # Step 2 placeholder (needs Agent 1 output path)
    if args.step == 2 or args.step is None:
        print(f"\n[Step 2] Requires Agent 1 output file.")
        print(f"  After Agent 1 completes, run:")
        print(f"  python orchestrator.py --continue-from-step 2 --agent1-output <path/to/discovery_*.json>")

    # Step 3 placeholder
    if args.step == 3 or args.step is None:
        print(f"\n[Step 3] Requires Agent 2 output file.")
        print(f"  After Agent 2 completes, run:")
        print(f"  python orchestrator.py --continue-from-step 3 --agent2-output <path/to/execution_*.json>")


def cmd_continue(args):
    """Continue pipeline from a specific step."""
    if args.continue_from_step == 2:
        if not args.agent1_output:
            print("ERROR: --agent1-output required for step 2")
            sys.exit(1)
        valid, msg = validate_json_file(args.agent1_output)
        if not valid:
            print(f"ERROR: Agent 1 output validation failed: {msg}")
            sys.exit(1)
        print(f"[OK] {msg}")

        input2_path, _ = step2_generate(args.agent1_output)
        print(f"\n[Step 2 ready] Input: {input2_path}")
        prompt2 = load_prompt("agent2")
        if prompt2:
            print_agent_prompt(2, input2_path, prompt2)
        print(f"\n[Step 3] After Agent 2 completes, run:")
        print(f"  python orchestrator.py --continue-from-step 3 --agent2-output <path/to/execution_*.json>")

    elif args.continue_from_step == 3:
        if not args.agent2_output:
            print("ERROR: --agent2-output required for step 3")
            sys.exit(1)
        valid, msg = validate_json_file(args.agent2_output)
        if not valid:
            print(f"ERROR: Agent 2 output validation failed: {msg}")
            sys.exit(1)
        print(f"[OK] {msg}")

        input3_path, _ = step3_generate(args.agent2_output)
        print(f"\n[Step 3 ready] Input: {input3_path}")
        prompt3 = load_prompt("agent3")
        if prompt3:
            print_agent_prompt(3, input3_path, prompt3)


def cmd_validate(args):
    """Validate agent output JSON files."""
    all_ok = True
    for filepath in args.files:
        valid, msg = validate_json_file(filepath)
        status = "OK" if valid else "FAIL"
        print(f"[{status}] {filepath}: {msg}")
        if not valid:
            all_ok = False

    # Cross-validation if both agent2 and agent3 outputs provided
    if args.cross_check and len(args.files) >= 2:
        issues = validate_outputs_consistency(args.files[0], args.files[1])
        for issue in issues:
            print(f"[CROSS-CHECK ISSUE] {issue}")
            all_ok = False

    if not all_ok:
        sys.exit(1)


def cmd_full(args):
    """Generate a combined self-contained prompt for running all 3 agents."""
    skills = None
    if args.skills:
        skills = [s.strip() for s in args.skills.split(",")]

    input1_path, input1_data = step1_generate(skills)

    print(f"""=== FULL PIPELINE INPUT ===
All input files written to: {OUTPUT_DIR}

Run the 3 agents in order. Each agent reads the previous agent's output.

--- AGENT 1 INPUT ({input1_path}) ---
{json.dumps(input1_data, indent=2, ensure_ascii=False)}

--- INSTRUCTIONS ---
1. Spawn Agent with subagent_type="general-purpose"
2. Give it the prompt from: {PROMPTS_DIR / 'agent1_discovery.md'}
3. Tell it to read input from: {input1_path}
4. Tell it to write output to: {OUTPUT_DIR / 'discovery_<id>.json'}

After Agent 1 completes, note the output path and continue with Agent 2.
""")


def cmd_run(args):
    """Print a single combined prompt that drives all 3 agents sequentially."""
    skills = None
    if args.skills:
        skills = [s.strip() for s in args.skills.split(",")]

    input1_path, input1_data = step1_generate(skills)
    input1_abs = Path(input1_path).resolve()

    prompt1 = load_prompt("agent1")
    prompt2 = load_prompt("agent2")
    prompt3 = load_prompt("agent3")

    if not all([prompt1, prompt2, prompt3]):
        print("ERROR: Missing agent prompt files")
        sys.exit(1)

    combined = f"""You are the skill-tester orchestrator. Run the 3-agent pipeline sequentially. Use caveman style throughout.

## Pipeline Overview
Agent 1 (Discovery) → Agent 2 (Execution) → Agent 3 (Repair)
Data passes via JSON files in {OUTPUT_DIR.as_posix()}

---

## PHASE 1: AGENT 1 — Skill Discovery & Structure

Read the input JSON from {input1_abs.as_posix()}, then follow your process:

{prompt1}

WRITE OUTPUT to {OUTPUT_DIR.as_posix()}/discovery_<id>.json

After writing Agent 1 output, proceed to Phase 2.

---

## PHASE 2: AGENT 2 — Skill Execution & Quality

Read the Agent 1 output JSON you just wrote, then follow your process:

{prompt2}

WRITE OUTPUT to {OUTPUT_DIR.as_posix()}/execution_<id>.json

After writing Agent 2 output, proceed to Phase 3.

---

## PHASE 3: AGENT 3 — Skill Repair & Evolution

Read the Agent 2 output JSON you just wrote, then follow your process:

{prompt3}

WRITE OUTPUT to {OUTPUT_DIR.as_posix()}/repair_<id>.json

---

## Final Summary
After all 3 phases complete, print a one-line summary:
"Pipeline complete: X skills discovered, Y tested, Z issues fixed, W unfixable"
"""
    run_prompt_path = OUTPUT_DIR / "combined_pipeline_prompt.md"
    run_prompt_path.write_text(combined, encoding="utf-8")
    print(f"Combined pipeline prompt written to: {run_prompt_path}")
    print(f"Length: {len(combined)} chars")
    print(f"\nPaste this prompt into a Claude Code session to run all 3 agents.")
    print(f"Or use: cat {run_prompt_path} | pbcopy  (macOS)")
    print(f"       type {run_prompt_path} | clip   (Windows)")


def main():
    parser = argparse.ArgumentParser(description="skill-tester 3-Agent Pipeline Orchestrator")
    sub = parser.add_subparsers(dest="command", help="Commands")

    # generate
    gen = sub.add_parser("generate", help="Generate input files and print agent prompts")
    gen.add_argument("--skills", help="Comma-separated skill names (omit for all)")
    gen.add_argument("--step", type=int, choices=[1, 2, 3], help="Generate only this step")

    # continue
    cont = sub.add_parser("continue", help="Continue pipeline from a step")
    cont.add_argument("--continue-from-step", type=int, required=True, choices=[2, 3])
    cont.add_argument("--agent1-output", help="Path to Agent 1 output JSON (for step 2)")
    cont.add_argument("--agent2-output", help="Path to Agent 2 output JSON (for step 3)")

    # validate
    val = sub.add_parser("validate", help="Validate agent output JSON files")
    val.add_argument("files", nargs="+", help="JSON files to validate")
    val.add_argument("--cross-check", action="store_true", help="Cross-validate agent outputs")

    # full
    full = sub.add_parser("full", help="Generate full pipeline input files")
    full.add_argument("--skills", help="Comma-separated skill names")

    # run
    run = sub.add_parser("run", help="Generate combined run prompt for single-session execution")
    run.add_argument("--skills", help="Comma-separated skill names")

    # Legacy flags at top level
    parser.add_argument("--all", action="store_true", help="Test all active skills")
    parser.add_argument("--validate", dest="validate_file", help="Validate a single output file")

    args = parser.parse_args()

    # Legacy interface
    if args.validate_file:
        return cmd_validate(argparse.Namespace(files=[args.validate_file], cross_check=False))

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "continue":
        cmd_continue(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "full":
        cmd_full(args)
    elif args.command == "run":
        cmd_run(args)
    else:
        # Default: generate with --all
        if args.all or not args.command:
            args.skills = None
            cmd_generate(args)
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
