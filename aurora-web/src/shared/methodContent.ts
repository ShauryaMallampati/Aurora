export const methodStats = [
  {
    label: "Policy stack",
    value: "PPO + Qwen 2.5",
    note: "Low-level control comes from PPO, while the language model adds strategic guidance.",
  },
  {
    label: "Guidance cadence",
    value: "Every 50 steps",
    note: "The hybrid controller queries the language model on a fixed interval during training and evaluation.",
  },
  {
    label: "Core inputs",
    value: "Fire + weather + terrain",
    note: "The state combines wildfire perimeter context with NOAA weather and USGS terrain data.",
  },
  {
    label: "Evaluation focus",
    value: "Hard scenarios",
    note: "The main signal is whether the hybrid policy improves difficult containment runs over PPO alone.",
  },
] as const;

export const methodPipeline = [
  {
    title: "Scenario state",
    detail:
      "Historical wildfire cases define the initial fire state. Weather and terrain context are folded into the environment before an episode starts.",
  },
  {
    title: "PPO control loop",
    detail:
      "The PPO policy handles direct suppression and movement decisions for the drone fleet at every simulation step.",
  },
  {
    title: "LLM strategic guidance",
    detail:
      "Qwen 2.5 reads the current state on a fixed cadence and returns priority zones, defensive lines, and coordination notes.",
  },
  {
    title: "Evaluation and replay",
    detail:
      "Completed runs write metrics and metadata to the results directory so the web app can replay, compare, and inspect them later.",
  },
] as const;

export const methodArtifacts = [
  {
    label: "Training",
    file: "train.py / train_hybrid.py",
    detail: "Baseline PPO and hybrid PPO + LLM training entry points.",
  },
  {
    label: "Simulation",
    file: "main_enhanced.py / simulate.py",
    detail: "Runtime simulation and local evaluation utilities.",
  },
  {
    label: "Evaluation",
    file: "evaluate.py / results/",
    detail: "Recorded metrics, metadata, and comparison artifacts consumed by the dashboard.",
  },
  {
    label: "Web app",
    file: "aurora-web/src/app",
    detail: "Simulator, run history, experiment lab, and method views.",
  },
] as const;

export const methodFindings = [
  "The hybrid controller is intended to improve high-complexity cases instead of inflating already-solved easy seeds.",
  "The language model is used for strategy, not direct low-level actuation.",
  "Recorded runs and experiment metadata are the source of truth for the dashboard and run history pages.",
] as const;
