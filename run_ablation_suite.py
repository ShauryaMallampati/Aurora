#!/usr/bin/env python3
"""Run the AURORA ablation study suite."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path
from typing import Any, Dict, List, Sequence

import matplotlib.pyplot as plt
import pandas as pd

from aurora_pipeline import (
    RESULTS_ROOT,
    STUDY_CONFIG_PATH,
    aggregate_runs,
    build_experiment_config,
    build_hyperparameter_table,
    build_mechanism_table,
    create_bar_plot,
    create_cadence_plot,
    create_training_curve_plot,
    json_default,
    load_study_definition,
    markdown_table,
    now_iso,
    train_single_run,
    write_estrat_spec,
    write_fallback_analysis,
    write_json,
    write_text,
)


RUN_LOG_PATH = RESULTS_ROOT / "suite_run_log.json"
FINAL_AUDIT_PATH = RESULTS_ROOT / "FINAL_AUDIT.md"
REPO_AUDIT_PATH = RESULTS_ROOT / "REPO_AUDIT.md"
PAPER_SNIPPETS_PATH = RESULTS_ROOT / "PAPER_SNIPPETS.md"


def create_placeholder_plot(output_prefix: Path, title: str, message: str) -> None:
    plt.figure(figsize=(8, 5))
    plt.axis("off")
    plt.text(0.5, 0.55, title, ha="center", va="center", fontsize=14, fontweight="bold")
    plt.text(0.5, 0.42, message, ha="center", va="center", fontsize=11, wrap=True)
    plt.tight_layout()
    plt.savefig(output_prefix.with_suffix(".png"))
    plt.savefig(output_prefix.with_suffix(".pdf"))
    plt.close()


def append_run_log(entry: Dict[str, Any]) -> None:
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    if RUN_LOG_PATH.exists():
        payload = json.loads(RUN_LOG_PATH.read_text(encoding="utf-8"))
    else:
        payload = []
    payload.append(entry)
    RUN_LOG_PATH.write_text(json.dumps(payload, indent=2, default=json_default), encoding="utf-8")


def seed_run_dir(root: Path, family: str, variant: str, seed: int, single_variant_family: bool = False) -> Path:
    if single_variant_family:
        return root / family / f"seed_{seed}"
    return root / family / variant / f"seed_{seed}"


def maybe_run_config(config, force: bool) -> Dict[str, Any]:
    if config.manifest_path.exists() and not force:
        try:
            manifest = json.loads(config.manifest_path.read_text(encoding="utf-8"))
            if manifest.get("status") == "completed" and config.eval_json_path.exists():
                return {"status": "reused", "config": config, "manifest": manifest}
        except Exception:
            pass
    return train_single_run(config)


def run_family(
    study: Dict[str, Any],
    family_name: str,
    variants: Sequence[str],
    force: bool = False,
    single_variant_family: bool = False,
    guidance_intervals: Dict[str, int] | None = None,
) -> Dict[str, Any]:
    family_root = RESULTS_ROOT / family_name
    family_root.mkdir(parents=True, exist_ok=True)

    completed_runs: List[Path] = []
    failed_runs: List[Dict[str, Any]] = []
    run_records: List[Dict[str, Any]] = []

    seeds = study["defaults"]["seeds"]
    for variant in variants:
        for seed in seeds:
            run_dir = seed_run_dir(
                RESULTS_ROOT,
                family_name,
                variant,
                seed,
                single_variant_family=single_variant_family,
            )
            run_name = f"{variant}_seed_{seed}"
            config = build_experiment_config(
                study=study,
                family=family_name,
                variant_key=variant,
                seed=seed,
                output_dir=run_dir,
                run_name=run_name,
                guidance_interval=guidance_intervals.get(variant) if guidance_intervals else None,
            )
            try:
                maybe_run_config(config, force=force)
                completed_runs.append(run_dir)
                run_records.append({"variant": variant, "seed": seed, "status": "completed", "run_dir": str(run_dir)})
            except Exception as error:
                failed_runs.append(
                    {
                        "variant": variant,
                        "seed": seed,
                        "error": str(error),
                        "run_dir": str(run_dir),
                    }
                )

    if single_variant_family:
        aggregate_runs(completed_runs, family_root, family_name)
    else:
        for variant in variants:
            variant_runs = [path for path in completed_runs if path.parent.name == variant]
            if variant_runs:
                aggregate_runs(variant_runs, family_root / variant, variant)

    return {
        "family_name": family_name,
        "completed_runs": run_records,
        "failed_runs": failed_runs,
    }


def run_cadence_family(study: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
    family_name = "cadence_ablation"
    family_root = RESULTS_ROOT / family_name
    family_root.mkdir(parents=True, exist_ok=True)

    base_variant = study["families"]["cadence_ablation"]["base_variant"]
    base_k = int(study["defaults"]["guidance_interval"])
    cadence_variants = {
        "dense": max(1, round(base_k / 2)),
        "baseline": base_k,
        "sparse": max(1, base_k * 2),
    }

    completed_runs: List[Path] = []
    failed_runs: List[Dict[str, Any]] = []
    run_records: List[Dict[str, Any]] = []

    for cadence_name, cadence_value in cadence_variants.items():
        for seed in study["defaults"]["seeds"]:
            run_dir = seed_run_dir(RESULTS_ROOT, family_name, cadence_name, seed)
            config = build_experiment_config(
                study=study,
                family=family_name,
                variant_key=base_variant,
                seed=seed,
                output_dir=run_dir,
                run_name=f"{cadence_name}_seed_{seed}",
                guidance_interval=cadence_value,
                overrides={"model_label": f"aurora_{cadence_name}_cadence"},
            )
            try:
                maybe_run_config(config, force=force)
                completed_runs.append(run_dir)
                run_records.append(
                    {
                        "variant": cadence_name,
                        "seed": seed,
                        "guidance_interval": cadence_value,
                        "status": "completed",
                        "run_dir": str(run_dir),
                    }
                )
            except Exception as error:
                failed_runs.append(
                    {
                        "variant": cadence_name,
                        "seed": seed,
                        "guidance_interval": cadence_value,
                        "error": str(error),
                        "run_dir": str(run_dir),
                    }
                )

    for cadence_name in cadence_variants:
        variant_runs = [path for path in completed_runs if path.parent.name == cadence_name]
        if variant_runs:
            aggregate_runs(variant_runs, family_root / cadence_name, cadence_name)

    return {
        "family_name": family_name,
        "completed_runs": run_records,
        "failed_runs": failed_runs,
    }


def write_heuristic_interpretation(study: Dict[str, Any]) -> None:
    heuristic_summary_path = RESULTS_ROOT / "heuristic_strategist" / "aggregate_summary.json"
    hybrid_summary_path = RESULTS_ROOT / "core_variants" / "qwen2_5_3b" / "aggregate_summary.json"
    output_path = RESULTS_ROOT / "heuristic_strategist" / "INTERPRETATION.md"
    if not heuristic_summary_path.exists() or not hybrid_summary_path.exists():
        write_text(
            output_path,
            "# Interpretation\n\nHeuristic vs hybrid comparison is unavailable because one or both aggregate summaries are missing.\n",
        )
        return

    heuristic = json.loads(heuristic_summary_path.read_text(encoding="utf-8"))
    hybrid = json.loads(hybrid_summary_path.read_text(encoding="utf-8"))
    heuristic_mean = heuristic.get("mean_final_return")
    hybrid_mean = hybrid.get("mean_final_return")

    if heuristic_mean is None or hybrid_mean is None:
        relation = "could not be determined"
    else:
        delta = heuristic_mean - hybrid_mean
        threshold = max(1.0, abs(hybrid_mean) * 0.05)
        if abs(delta) <= threshold:
            relation = "heuristic ~= hybrid"
        elif delta < 0:
            relation = "heuristic < hybrid"
        else:
            relation = "heuristic > hybrid"

    body = f"""# Interpretation

- Heuristic mean final return: {heuristic_mean}
- Hybrid mean final return: {hybrid_mean}
- Automatic relation: {relation}
"""
    write_text(output_path, body)


def write_cadence_interpretation() -> None:
    output_path = RESULTS_ROOT / "cadence_ablation" / "INTERPRETATION.md"
    table_path = RESULTS_ROOT / "cadence_ablation" / "aggregate_results.csv"
    if not table_path.exists():
        write_text(output_path, "# Interpretation\n\nCadence comparison is unavailable because aggregate results are missing.\n")
        return

    frame = pd.read_csv(table_path)
    if frame.empty:
        write_text(output_path, "# Interpretation\n\nCadence comparison is unavailable because aggregate results are empty.\n")
        return

    best_row = frame.sort_values("overall_mean", ascending=False).iloc[0]
    text = f"""# Interpretation

- Best measured cadence: {best_row['variant']}
- Mean return: {best_row['overall_mean']:.4f}
- Observation: {'denser guidance helped' if best_row['variant'] == 'dense' else 'sparser guidance helped' if best_row['variant'] == 'sparse' else 'baseline cadence remained best'}
"""
    write_text(output_path, text)


def write_mechanism_takeaway(frame: pd.DataFrame) -> None:
    output_path = RESULTS_ROOT / "mechanism_ablation" / "TAKEAWAY.txt"
    if frame.empty:
        write_text(output_path, "Mechanism ablation results are unavailable.\n")
        return

    best = frame.sort_values("overall_mean", ascending=False).iloc[0]
    ppo = frame[frame["variant"] == "ppo_only"]
    ppo_mean = float(ppo.iloc[0]["overall_mean"]) if not ppo.empty else math.nan
    delta = float(best["overall_mean"]) - ppo_mean if not math.isnan(ppo_mean) else math.nan
    write_text(
        output_path,
        f"Best mechanism variant: {best['variant']} with overall mean {best['overall_mean']:.4f}. "
        f"Delta vs PPO-only: {delta:.4f}.\n",
    )


def create_mechanism_outputs() -> pd.DataFrame:
    mechanism_root = RESULTS_ROOT / "mechanism_ablation"
    mechanism_root.mkdir(parents=True, exist_ok=True)
    frame = build_mechanism_table(mechanism_root)
    if frame.empty:
        empty = pd.DataFrame(columns=["variant", "easy_mean", "easy_std", "hard_mean", "hard_std", "overall_mean", "overall_std"])
        empty.to_csv(mechanism_root / "ablation_table.csv", index=False)
        empty.to_csv(RESULTS_ROOT / "ablation_table.csv", index=False)
        write_text(mechanism_root / "ablation_table.md", markdown_table(empty))
        write_text(RESULTS_ROOT / "ablation_table.md", markdown_table(empty))
        create_placeholder_plot(
            RESULTS_ROOT / "mechanism_ablation_plot",
            "Mechanism Ablation",
            "Mechanism ablation results are not available yet.",
        )
        write_mechanism_takeaway(frame)
        return frame

    frame.to_csv(mechanism_root / "ablation_table.csv", index=False)
    frame.to_csv(RESULTS_ROOT / "ablation_table.csv", index=False)
    write_text(mechanism_root / "ablation_table.md", markdown_table(frame))
    write_text(RESULTS_ROOT / "ablation_table.md", markdown_table(frame))
    create_bar_plot(
        frame,
        RESULTS_ROOT / "mechanism_ablation_plot",
        "Mechanism Ablation",
        metric_columns=["easy_mean", "hard_mean", "overall_mean"],
    )
    write_mechanism_takeaway(frame)
    return frame


def create_core_outputs() -> pd.DataFrame:
    core_root = RESULTS_ROOT / "core_variants"
    core_root.mkdir(parents=True, exist_ok=True)
    frame = build_mechanism_table(core_root)
    if frame.empty:
        empty = pd.DataFrame(columns=["variant", "easy_mean", "easy_std", "hard_mean", "hard_std", "overall_mean", "overall_std"])
        empty.to_csv(RESULTS_ROOT / "main_results_table.csv", index=False)
        write_text(RESULTS_ROOT / "main_results_table.md", markdown_table(empty))
        create_placeholder_plot(
            RESULTS_ROOT / "training_curves_core_variants",
            "Core Variant Training Curves",
            "Core-variant training curves are not available yet.",
        )
        create_placeholder_plot(
            RESULTS_ROOT / "heuristic_vs_hybrid_plot",
            "Final Return Comparison",
            "Core-variant comparison bars are not available yet.",
        )
        return frame

    frame.to_csv(RESULTS_ROOT / "main_results_table.csv", index=False)
    write_text(RESULTS_ROOT / "main_results_table.md", markdown_table(frame))

    variant_dirs = {}
    for variant in ["ppo_only", "qwen2_5_3b", "qwen2_5_7b"]:
        variant_root = core_root / variant
        if variant_root.exists():
            variant_dirs[variant] = sorted(path for path in variant_root.iterdir() if path.is_dir())

    if variant_dirs:
        create_training_curve_plot(
            variant_dirs,
            RESULTS_ROOT / "training_curves_core_variants",
            "Core Variant Training Curves",
        )

    create_bar_plot(
        frame,
        RESULTS_ROOT / "heuristic_vs_hybrid_plot",
        "Final Return Comparison",
        metric_columns=["overall_mean"],
    )
    return frame


def create_cadence_outputs() -> pd.DataFrame:
    cadence_root = RESULTS_ROOT / "cadence_ablation"
    cadence_root.mkdir(parents=True, exist_ok=True)
    frame = build_mechanism_table(cadence_root)
    if frame.empty:
        pd.DataFrame(columns=["variant", "easy_mean", "easy_std", "hard_mean", "hard_std", "overall_mean", "overall_std"]).to_csv(
            cadence_root / "aggregate_results.csv",
            index=False,
        )
        create_placeholder_plot(
            RESULTS_ROOT / "cadence_plot",
            "Guidance Cadence Ablation",
            "Cadence ablation results are not available yet.",
        )
        write_cadence_interpretation()
        return frame

    frame.to_csv(cadence_root / "aggregate_results.csv", index=False)
    create_cadence_plot(frame, RESULTS_ROOT / "cadence_plot")
    write_cadence_interpretation()
    return frame


def write_paper_snippets(study: Dict[str, Any], core_frame: pd.DataFrame, mechanism_frame: pd.DataFrame, cadence_frame: pd.DataFrame, fallback_summary: Dict[str, Any]) -> None:
    hyper_frame = build_hyperparameter_table(study)
    hyper_frame.to_csv(RESULTS_ROOT / "hyperparameter_table.csv", index=False)
    write_text(RESULTS_ROOT / "hyperparameter_table.md", markdown_table(hyper_frame))

    scenario_names = ", ".join(fire["name"] for fire in study["defaults"].get("eval_scenarios", []))
    setup = (
        "AURORA experiments used the shared ablation pipeline in this repository with "
        f"{study['defaults']['num_drones']} drones, a {study['defaults']['grid_size']}x{study['defaults']['grid_size']} grid, "
        f"{study['defaults']['total_timesteps']} PPO timesteps per run, guidance interval "
        f"K={study['defaults']['guidance_interval']}, and evaluation on {scenario_names}."
    )

    fallback_paragraph = (
        f"Across logged LLM runs, the suite recorded {fallback_summary.get('llm_queries')} LLM queries, "
        f"{fallback_summary.get('valid_structured_parses')} valid structured parses, and "
        f"{fallback_summary.get('fallback_invocations')} fallback invocations "
        f"({fallback_summary.get('fallback_rate_percentage')}%)."
    )

    heuristic_paragraph = "Heuristic baseline results are unavailable."
    if not core_frame.empty and (RESULTS_ROOT / "heuristic_strategist" / "aggregate_summary.json").exists():
        heuristic = json.loads((RESULTS_ROOT / "heuristic_strategist" / "aggregate_summary.json").read_text(encoding="utf-8"))
        hybrid_path = RESULTS_ROOT / "core_variants" / "qwen2_5_3b" / "aggregate_summary.json"
        if hybrid_path.exists():
            hybrid = json.loads(hybrid_path.read_text(encoding="utf-8"))
            heuristic_paragraph = (
                f"The heuristic strategist reached a mean final return of {heuristic.get('mean_final_return')}, "
                f"compared with {hybrid.get('mean_final_return')} for the Qwen2.5-3B hybrid."
            )

    mechanism_paragraph = "Mechanism ablation results are unavailable."
    if not mechanism_frame.empty:
        best = mechanism_frame.sort_values("overall_mean", ascending=False).iloc[0]
        mechanism_paragraph = (
            f"In the mechanism ablation, {best['variant']} achieved the best overall mean return "
            f"({best['overall_mean']:.4f}), with easy mean {best['easy_mean']:.4f} and hard mean {best['hard_mean']:.4f}."
        )

    cadence_paragraph = "Cadence ablation results are unavailable."
    if not cadence_frame.empty:
        best = cadence_frame.sort_values("overall_mean", ascending=False).iloc[0]
        cadence_paragraph = (
            f"In the cadence ablation, {best['variant']} guidance performed best with overall mean "
            f"{best['overall_mean']:.4f}."
        )

    snippets = f"""# Paper Snippets

## Experimental setup

{setup}

## Fallback-rate result

{fallback_paragraph}

## Heuristic baseline result

{heuristic_paragraph}

## Mechanism ablation result

{mechanism_paragraph}

## Cadence ablation result

{cadence_paragraph}

## Hyperparameter table

{markdown_table(hyper_frame)}
"""
    write_text(PAPER_SNIPPETS_PATH, snippets)


def artifact_has_data(path: Path) -> bool:
    if not path.exists():
        return False
    if path.suffix == ".csv":
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        return len(lines) > 1
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            if "num_runs" in payload:
                return int(payload.get("num_runs", 0)) > 0
            if "llm_queries" in payload:
                return int(payload.get("llm_queries", 0)) > 0
            return bool(payload)
        if isinstance(payload, list):
            return len(payload) > 0
    return path.stat().st_size > 0


def write_final_audit(study: Dict[str, Any], run_results: Dict[str, Any]) -> None:
    log_payload = json.loads(RUN_LOG_PATH.read_text(encoding="utf-8")) if RUN_LOG_PATH.exists() else []
    completed = []
    failed = []
    for family_result in run_results.values():
        completed.extend(family_result.get("completed_runs", []))
        failed.extend(family_result.get("failed_runs", []))

    family_artifacts = {
        "budget_matched_ppo": RESULTS_ROOT / "budget_matched_ppo" / "aggregate_summary.json",
        "heuristic_strategist": RESULTS_ROOT / "heuristic_strategist" / "aggregate_summary.json",
        "core_variants_ppo_only": RESULTS_ROOT / "core_variants" / "ppo_only" / "aggregate_summary.json",
        "core_variants_qwen2_5_3b": RESULTS_ROOT / "core_variants" / "qwen2_5_3b" / "aggregate_summary.json",
        "core_variants_qwen2_5_7b": RESULTS_ROOT / "core_variants" / "qwen2_5_7b" / "aggregate_summary.json",
        "mechanism_ablation": RESULTS_ROOT / "mechanism_ablation" / "ablation_table.csv",
        "cadence_ablation": RESULTS_ROOT / "cadence_ablation" / "aggregate_results.csv",
        "fallback_analysis": RESULTS_ROOT / "fallback_analysis" / "fallback_rate_summary.json",
    }
    discovered_completed = [name for name, path in family_artifacts.items() if artifact_has_data(path)]

    output_checks = []
    required_outputs = [
        REPO_AUDIT_PATH,
        RESULTS_ROOT / "estrat_spec.md",
        RESULTS_ROOT / "fallback_analysis" / "fallback_rate_summary.json",
        RESULTS_ROOT / "fallback_analysis" / "example_prompt.txt",
        RESULTS_ROOT / "fallback_analysis" / "example_response.json",
        RESULTS_ROOT / "main_results_table.csv",
        RESULTS_ROOT / "main_results_table.md",
        RESULTS_ROOT / "ablation_table.csv",
        RESULTS_ROOT / "ablation_table.md",
        RESULTS_ROOT / "training_curves_core_variants.pdf",
        RESULTS_ROOT / "training_curves_core_variants.png",
        RESULTS_ROOT / "heuristic_vs_hybrid_plot.pdf",
        RESULTS_ROOT / "heuristic_vs_hybrid_plot.png",
        RESULTS_ROOT / "cadence_plot.pdf",
        RESULTS_ROOT / "cadence_plot.png",
        RESULTS_ROOT / "mechanism_ablation_plot.pdf",
        RESULTS_ROOT / "mechanism_ablation_plot.png",
        RESULTS_ROOT / "hyperparameter_table.csv",
        RESULTS_ROOT / "hyperparameter_table.md",
        RESULTS_ROOT / "PAPER_SNIPPETS.md",
    ]
    for path in required_outputs:
        output_checks.append(f"- {'present' if path.exists() else 'missing'}: {path}")

    package_is_sufficient = (
        not failed
        and (RESULTS_ROOT / "budget_matched_ppo" / "aggregate_summary.json").exists()
        and (RESULTS_ROOT / "heuristic_strategist" / "aggregate_summary.json").exists()
        and (RESULTS_ROOT / "core_variants" / "qwen2_5_3b" / "aggregate_summary.json").exists()
        and (RESULTS_ROOT / "core_variants" / "qwen2_5_7b" / "aggregate_summary.json").exists()
        and (RESULTS_ROOT / "mechanism_ablation" / "ablation_table.csv").exists()
        and (RESULTS_ROOT / "cadence_ablation" / "aggregate_results.csv").exists()
    )

    exact_commands = "\n".join(f"- {entry['command']}" for entry in log_payload) if log_payload else "- none recorded"
    scenarios = ", ".join(fire["name"] for fire in study["defaults"].get("eval_scenarios", []))

    text = f"""# Final Audit

## Completed experiments

{json.dumps(completed, indent=2, default=json_default)}

## Completed experiment families discovered on disk

{json.dumps(discovered_completed, indent=2, default=json_default)}

## Failed experiments

{json.dumps(failed, indent=2, default=json_default)}

## Missing dependencies

- LLM-model availability still depends on local Hugging Face access, local cache state, and device memory.
- The current Python environment emits duplicate `cv2`/`av` AVFoundation class warnings on import.
- `timm` was upgraded to make Qwen loading work, which now conflicts with `nerfstudio`'s pinned `timm==0.6.7` requirement.

## Unresolved blockers

- Qwen 2.5-3B single-call loading and structured response generation succeeded on MPS, but Qwen 2.5-7B has not yet been cached or validated in this environment.
- Full-budget LLM-guided training is likely much slower than PPO-only or heuristic runs because the strategist is queried during episodes.
- Prompt/response extraction and fallback-rate reporting now have diagnostic coverage, but a completed full-budget LLM family is still required for final paper claims.
- Older extracted SB3 model directories already present under `results/` are not reusable as checkpoints because loading them raises `KeyError: 'policy.optimizer'`.

## Exact commands used

{exact_commands}

## Exact seeds used

- {study['defaults']['seeds']}

## Exact budgets used

- {study['defaults']['total_timesteps']} timesteps per run

## Exact evaluation scenarios used

- {scenarios}

## Output checks

{chr(10).join(output_checks)}

## Package sufficiency

- Sufficient to update the paper: {'yes' if package_is_sufficient else 'no'}
"""
    write_text(FINAL_AUDIT_PATH, text)


def hydrate_eval_scenarios(study: Dict[str, Any]) -> None:
    study["defaults"]["eval_scenarios"] = [
        {"name": fire["name"], "state": fire["state"], "year": fire["year"], "acres": fire["acres"], "lat": fire["lat"], "lon": fire["lon"]}
        for fire in __import__("evaluate").EVALUATION_FIRES
    ]


def run_mode(mode: str, force: bool = False) -> Dict[str, Any]:
    study = load_study_definition()
    hydrate_eval_scenarios(study)
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)

    append_run_log(
        {
            "timestamp": now_iso(),
            "command": f"python run_ablation_suite.py --mode {mode}" + (" --force" if force else ""),
        }
    )

    write_estrat_spec(RESULTS_ROOT / "estrat_spec.md")

    results: Dict[str, Any] = {}
    if mode in {"audit", "all"}:
        if not REPO_AUDIT_PATH.exists():
            raise RuntimeError("REPO_AUDIT.md must exist before running the suite.")

    if mode in {"budget_ppo", "core", "all"}:
        results["budget_matched_ppo"] = run_family(
            study,
            family_name="budget_matched_ppo",
            variants=["ppo_only"],
            force=force,
            single_variant_family=True,
        )
    if mode in {"core", "all"}:
        results["core_variants"] = run_family(
            study,
            family_name="core_variants",
            variants=["ppo_only", "qwen2_5_3b", "qwen2_5_7b"],
            force=force,
        )

    if mode in {"heuristic", "all"}:
        results["heuristic_strategist"] = run_family(
            study,
            family_name="heuristic_strategist",
            variants=["heuristic_strategist"],
            force=force,
            single_variant_family=True,
        )
        write_heuristic_interpretation(study)

    if mode in {"mechanism", "all"}:
        results["mechanism_ablation"] = run_family(
            study,
            family_name="mechanism_ablation",
            variants=["ppo_only", "reward_only", "obs_only", "full_hybrid", "heuristic_strategist"],
            force=force,
        )

    if mode in {"cadence", "all"}:
        results["cadence_ablation"] = run_cadence_family(study, force=force)

    if mode in {"fallback", "all"}:
        results["fallback_analysis"] = write_fallback_analysis(RESULTS_ROOT)

    if mode == "plots":
        core_frame = create_core_outputs()
        mechanism_frame = create_mechanism_outputs()
        cadence_frame = create_cadence_outputs()
        fallback_summary = (
            json.loads((RESULTS_ROOT / "fallback_analysis" / "fallback_rate_summary.json").read_text(encoding="utf-8"))
            if (RESULTS_ROOT / "fallback_analysis" / "fallback_rate_summary.json").exists()
            else {}
        )
        write_paper_snippets(study, core_frame, mechanism_frame, cadence_frame, fallback_summary)
        write_final_audit(study, results)

    if mode == "all":
        core_frame = create_core_outputs()
        mechanism_frame = create_mechanism_outputs()
        cadence_frame = create_cadence_outputs()
        fallback_summary = write_fallback_analysis(RESULTS_ROOT)
        write_paper_snippets(study, core_frame, mechanism_frame, cadence_frame, fallback_summary)
        write_final_audit(study, results)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AURORA ablation suite.")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["audit", "budget_ppo", "core", "heuristic", "mechanism", "cadence", "fallback", "plots", "all"],
    )
    parser.add_argument("--force", action="store_true", default=False)
    args = parser.parse_args()
    run_mode(args.mode, force=args.force)


if __name__ == "__main__":
    main()
