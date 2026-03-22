"""
Hybrid PPO + LLM agent.
LLM = strategy, PPO = tactics.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import json
from datetime import datetime
import os
from pathlib import Path

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️  Transformers not available. Install with: pip install transformers torch")


class HybridPPOLLMAgent:
    """LLM-guided strategic layer for PPO drone control."""
    
    def __init__(self,
                 llm_model: str = "Qwen/Qwen2.5-1.5B-Instruct",
                 llm_guidance_frequency: int = 500,
                 temperature: float = 0.7,
                 hf_token: Optional[str] = None,
                 llm_backend: str = "transformers",
                 device: str = "auto",
                 force_heuristic: bool = False,
                 require_model_loaded: bool = False,
                 guidance_log_path: Optional[str] = None,
                 max_new_tokens: int = 256,
                 do_sample: bool = False):
        """
        Args:
            llm_model: HuggingFace model ID
            llm_guidance_frequency: Steps between LLM calls
            temperature: Sampling temperature (0.7 default)
            hf_token: HF token for gated models (or set HF_TOKEN env var)
            device: cuda/cpu/auto
        """
        self.llm_model = llm_model
        self.llm_guidance_frequency = llm_guidance_frequency
        self.temperature = temperature
        self.llm_backend = llm_backend.lower() if isinstance(llm_backend, str) else llm_backend
        self.force_heuristic = bool(force_heuristic)
        self.require_model_loaded = bool(require_model_loaded)
        self.guidance_log_path = Path(guidance_log_path).expanduser() if guidance_log_path else None
        self.max_new_tokens = int(max_new_tokens)
        self.do_sample = bool(do_sample)
        
        # Set up LLM bits
        self.model = None
        self.tokenizer = None
        self.pipe = None
        
        # Gemini backend removed; avoid heavy loads and use transformers/heuristics instead.
        hf_token = hf_token or os.getenv("HF_TOKEN")

        if self.force_heuristic:
            self.llm_backend = "heuristic"
        elif self.llm_backend == 'gemini':
            # Gemini removed: switch to transformers.
            print("⚠️  Gemini backend requested but unsupported. Switching to 'transformers' backend.")
            self.llm_backend = 'transformers'
        else:
            if TRANSFORMERS_AVAILABLE:
                # HF token is optional; don't hardcode. Prefer HF_TOKEN env var.
                if hf_token:
                    print("🔒 HuggingFace token present in code (will be used for gated meta-llama models).")
                else:
                    print("⚠️  No HuggingFace token found. Using heuristic fallback for strategic guidance if model load fails.")

                # Try to load the model (pass token for gated/meta-llama).
                try:
                    # Pick device
                    if device == "auto":
                        if torch.cuda.is_available():
                            device = "cuda"
                        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                            device = "mps"
                        else:
                            device = "cpu"

                    # Check if model is gated
                    is_gated_model = llm_model.startswith("meta-llama") or llm_model.startswith("meta/llama")

                    # Load tokenizer (token only if gated)
                    tokenizer_kwargs = {"trust_remote_code": True}
                    if is_gated_model and hf_token:
                        tokenizer_kwargs["token"] = hf_token

                    self.tokenizer = AutoTokenizer.from_pretrained(
                        llm_model,
                        **tokenizer_kwargs
                    )

                    # Pick dtype + device map
                    # Gated models prefer BF16/auto; fall back otherwise
                    if is_gated_model:
                        torch_dtype = torch.bfloat16 if device == "cuda" else torch.float16 if device == "mps" else torch.float32
                    else:
                        torch_dtype = torch.float16 if device in ("cuda", "mps") else torch.float32

                    model_kwargs = {
                        "torch_dtype": torch_dtype,
                        "trust_remote_code": True,
                        "low_cpu_mem_usage": True,
                    }
                    if device == "cuda":
                        model_kwargs["device_map"] = "auto"
                    elif device == "cpu":
                        model_kwargs["device_map"] = "cpu"
                    if is_gated_model and hf_token:
                        model_kwargs["token"] = hf_token

                    self.model = AutoModelForCausalLM.from_pretrained(
                        llm_model,
                        **model_kwargs
                    )
                    if device == "mps":
                        self.model.to("mps")

                    # Build pipeline
                    pipeline_device = device if device != "cpu" else -1
                    generation_kwargs = {
                        "max_new_tokens": self.max_new_tokens,
                        "do_sample": self.do_sample,
                    }
                    if self.do_sample:
                        generation_kwargs["temperature"] = self.temperature
                    self.pipe = pipeline(
                        "text-generation",
                        model=self.model,
                        tokenizer=self.tokenizer,
                        device=pipeline_device,
                        **generation_kwargs,
                    )

                    print(f"✅ LLM loaded on {device}: {llm_model}")

                except Exception as e:
                    print(f"⚠️  Error loading LLM: {e}")
                    print("    Using heuristic fallback for strategic guidance.")
            else:
                print("⚠️  Transformers library not available. Using heuristic fallback.")
        # If transformers missing, stick to heuristic
        if self.llm_backend == 'transformers' and not TRANSFORMERS_AVAILABLE:
            print("⚠️  Transformers library not available. Using heuristic fallback.")
        if self.require_model_loaded and not self.force_heuristic and not self.pipe:
            raise RuntimeError(
                f"LLM variant requires a loaded model, but '{self.llm_model}' was not available."
            )
        
        # Strategy state
        self.current_strategy = None
        self.steps_since_guidance = 0
        self.guidance_history = []
        
        # Stats
        self.llm_calls = 0
        self.llm_tokens_used = 0
        self.llm_errors = 0
        self.guidance_requests = 0
        self.llm_query_attempts = 0
        self.valid_structured_responses = 0
        self.fallback_invocations = 0
        self.heuristic_guidance_calls = 0
        self.last_prompt = None
        self.last_raw_response = None
        self.last_parsed_guidance = None

        if self.guidance_log_path is not None:
            self.guidance_log_path.parent.mkdir(parents=True, exist_ok=True)

    def reset_episode_state(self) -> None:
        """Reset per-episode strategy state but keep aggregate counters."""
        self.current_strategy = None
        self.steps_since_guidance = 0

    def _is_valid_guidance(self, payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False
        if not isinstance(payload.get("priority_zones"), list):
            return False
        if not isinstance(payload.get("drone_assignments"), dict):
            return False
        return True

    def _append_guidance_event(self, payload: Dict[str, Any]) -> None:
        if self.guidance_log_path is None:
            return
        event = dict(payload)
        event.setdefault("timestamp", datetime.now().isoformat())
        def _default(value: Any) -> Any:
            if isinstance(value, np.generic):
                return value.item()
            return str(value)
        with self.guidance_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, default=_default) + "\n")
        
    def get_strategic_guidance(self, 
                              fire_state: np.ndarray,
                              drone_positions: List[Tuple[int, int]],
                              drone_states: List[Dict],
                              weather: Dict,
                              step: int) -> Dict[str, Any]:
        """Get LLM guidance on where drones should focus.
        
        Returns dict with priority_zones, drone_assignments, resource_strategy.
        """
        self.guidance_requests += 1
        
        if self.force_heuristic or not self.pipe:
            # No pipeline or heuristic mode
            reason = 'heuristic_only' if self.force_heuristic else 'missing_pipeline'
            return self._fallback_strategy(
                fire_state,
                drone_positions,
                drone_states,
                step=step,
                reason=reason,
            )
        
        try:
            # Analyze current situation
            total_burning = np.sum(fire_state == 1)
            grid_size = fire_state.shape[0]
            fire_pct = (total_burning / (grid_size * grid_size)) * 100
            
            # Find fire hotspots (clusters)
            hotspots = self._find_fire_hotspots(fire_state)
            
            # Summarize drones
            avg_battery = np.mean([d['battery_percentage'] for d in drone_states])
            avg_water = np.mean([d['water_percentage'] for d in drone_states])
            
            # Build prompt for Llama-2 chat format
            system_prompt = "You are an expert wildfire incident commander AI providing strategic guidance to drone operators fighting wildfires."
            
            user_prompt = f"""CURRENT WILDFIRE SITUATION (Step {step}):
- Fire coverage: {fire_pct:.1f}% of {grid_size}x{grid_size} grid ({total_burning} burning cells)
- Hotspots detected: {len(hotspots)} fire clusters
- Average drone battery: {avg_battery:.1f}%
- Average drone water: {avg_water:.1f}%
- Weather: {weather.get('temperature_f', 'N/A')}°F, {weather.get('wind_speed_mph', 'N/A')} mph wind from {weather.get('wind_direction', 'N/A')}

FIRE HOTSPOTS:
{self._format_hotspots(hotspots[:5])}

DRONE STATES:
{self._format_drone_states(drone_states, drone_positions)}

TASK: Provide strategic guidance for the next {self.llm_guidance_frequency} steps.

Respond ONLY with valid JSON (no other text):
{{
  "priority_zones": [[row1, col1], [row2, col2]],
  "drone_assignments": {{"drone_0": 0, "drone_1": 1}},
  "resource_strategy": "aggressive",
  "retreat_threshold": 20,
  "reasoning": "brief explanation"
}}

Focus on:
1. Containing the largest/most dangerous fire clusters
2. Preventing fire spread to unburned areas
3. Balancing suppression with battery/water conservation"""

            # Format prompt
            prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_prompt} [/INST]"
            self.last_prompt = prompt
            self.llm_query_attempts += 1
            
            # Generate response (transformers only)
            # Blocking call: wait for completion
            print(f"⏳ Waiting for Qwen guidance at step {step}...")
            generation_kwargs = {
                "max_new_tokens": self.max_new_tokens,
                "num_return_sequences": 1,
                "do_sample": self.do_sample,
            }
            if self.do_sample:
                generation_kwargs["temperature"] = self.temperature
            outputs = self.pipe(
                prompt,
                **generation_kwargs,
            )
            response_text = outputs[0].get('generated_text', '')
            self.last_raw_response = response_text
            print(f"✅ Qwen responded")
            
            # Extract JSON (after [/INST])
            if '[/INST]' in response_text:
                json_text = response_text.split('[/INST]')[-1].strip()
            else:
                json_text = response_text
            
            # Try regex first, then fallback
            import re
            # First try: match balanced braces
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', json_text, re.DOTALL)
            guidance = None
            
            if json_match:
                try:
                    json_str = json_match.group(0)
                    candidate = json.loads(json_str)
                    if self._is_valid_guidance(candidate):
                        guidance = candidate
                except json.JSONDecodeError:
                    pass
            
            # If regex fails, use first + last brace
            if not guidance:
                start_idx = json_text.find('{')
                end_idx = json_text.rfind('}')
                if start_idx >= 0 and end_idx > start_idx:
                    try:
                        json_str = json_text[start_idx:end_idx+1]
                        candidate = json.loads(json_str)
                        if self._is_valid_guidance(candidate):
                            guidance = candidate
                    except json.JSONDecodeError:
                        pass

            # If the model emitted multiple JSON objects, take the first valid one.
            if not guidance:
                decoder = json.JSONDecoder()
                for index, char in enumerate(json_text):
                    if char != "{":
                        continue
                    try:
                        candidate, _ = decoder.raw_decode(json_text[index:])
                    except json.JSONDecodeError:
                        continue
                    if self._is_valid_guidance(candidate):
                        guidance = candidate
                        break
            
            # If still invalid, fall back to heuristic
            if not guidance:
                self.llm_errors += 1
                return self._fallback_strategy(
                    fire_state,
                    drone_positions,
                    drone_states,
                    step=step,
                    reason='invalid_json',
                    prompt=prompt,
                    raw_response=response_text,
                )
            
            # Update stats
            self.llm_calls += 1
            self.valid_structured_responses += 1
            # Rough token estimate
            prompt_tokens = len(prompt.split())
            response_tokens = len(json_text.split())
            self.llm_tokens_used += prompt_tokens + response_tokens
            
            # Store guidance
            guidance['timestamp'] = datetime.now().isoformat()
            guidance['step'] = step
            self.guidance_history.append(guidance)
            self.last_parsed_guidance = guidance
            self._append_guidance_event(
                {
                    'step': step,
                    'source': 'llm',
                    'prompt': prompt,
                    'raw_response': response_text,
                    'parsed_guidance': guidance,
                    'valid_structured_parse': True,
                    'fallback_invoked': False,
                    'llm_query_attempted': True,
                }
            )
            
            strategy = guidance.get('resource_strategy', 'balanced')
            reasoning = guidance.get('reasoning', 'Strategic guidance provided')[:80]
            print(f"🧠 Qwen Strategy: {strategy} - {reasoning}...")
            
            return guidance
            
        except Exception as e:
            # On error, fall back instead of crashing
            self.llm_errors += 1
            return self._fallback_strategy(
                fire_state,
                drone_positions,
                drone_states,
                step=step,
                reason=f'exception:{type(e).__name__}',
                prompt=self.last_prompt,
                raw_response=self.last_raw_response,
            )

    # Gemini API is intentionally removed.
    # If you add API backends later, keep them in optional adapters
    # so keys never land in source.
    
    def _fallback_strategy(
        self,
        fire_state,
        drone_positions,
        drone_states,
        step: Optional[int] = None,
        reason: str = 'fallback',
        prompt: Optional[str] = None,
        raw_response: Optional[str] = None,
    ) -> Dict:
        """Heuristic fallback when LLM is unavailable."""
        self.fallback_invocations += 1
        self.heuristic_guidance_calls += 1
        
        hotspots = self._find_fire_hotspots(fire_state)
        
        # Priority zones are the biggest hotspots
        priority_zones = [h['centroid'] for h in hotspots[:5]]
        
        # Assign drones to nearest zones
        assignments = {}
        for i, pos in enumerate(drone_positions):
            if priority_zones:
                # Find nearest zone
                distances = [abs(pos[0] - z[0]) + abs(pos[1] - z[1]) for z in priority_zones]
                nearest_idx = np.argmin(distances)
                assignments[f"drone_{i}"] = nearest_idx
        
        guidance = {
            'priority_zones': priority_zones,
            'drone_assignments': assignments,
            'resource_strategy': 'balanced',
            'retreat_threshold': 20,
            'reasoning': 'Heuristic fallback: target largest fire clusters',
            'source': 'heuristic'
        }
        self.last_parsed_guidance = guidance
        self._append_guidance_event(
            {
                'step': step,
                'source': 'heuristic',
                'reason': reason,
                'prompt': prompt,
                'raw_response': raw_response,
                'parsed_guidance': guidance,
                'valid_structured_parse': False,
                'fallback_invoked': True,
                'llm_query_attempted': bool(prompt),
            }
        )
        return guidance
    
    def _find_fire_hotspots(self, fire_state: np.ndarray, min_size: int = 5) -> List[Dict]:
        """Find connected fire clusters."""
        from scipy import ndimage
        
        # Label connected burning regions
        burning_mask = (fire_state == 1).astype(int)
        labeled, num_features = ndimage.label(burning_mask)
        
        hotspots = []
        for label_id in range(1, num_features + 1):
            mask = (labeled == label_id)
            size = np.sum(mask)
            
            if size >= min_size:
                # Find centroid
                coords = np.argwhere(mask)
                centroid = coords.mean(axis=0).astype(int).tolist()
                
                hotspots.append({
                    'label': label_id,
                    'size': int(size),
                    'centroid': centroid,
                    'bbox': self._get_bbox(mask)
                })
        
        # Sort by size (largest first)
        hotspots.sort(key=lambda x: x['size'], reverse=True)
        
        return hotspots
    
    def _get_bbox(self, mask: np.ndarray) -> List[int]:
        """Get bounding box for a fire cluster."""
        coords = np.argwhere(mask)
        if len(coords) == 0:
            return [0, 0, 0, 0]
        r_min, c_min = coords.min(axis=0)
        r_max, c_max = coords.max(axis=0)
        return [int(r_min), int(c_min), int(r_max), int(c_max)]
    
    def _format_hotspots(self, hotspots: List[Dict]) -> str:
        """Format hotspot info for prompt."""
        if not hotspots:
            return "  (No significant hotspots)"
        
        lines = []
        for i, h in enumerate(hotspots):
            lines.append(f"  {i+1}. Size: {h['size']} cells, Center: {h['centroid']}")
        return "\n".join(lines)
    
    def _format_drone_states(self, states: List[Dict], positions: List[Tuple]) -> str:
        """Format drone info to send to the LLM."""
        lines = []
        for i, (state, pos) in enumerate(zip(states, positions)):
            lines.append(
                f"  Drone {i}: Pos {pos}, "
                f"Battery {state['battery_percentage']:.0f}%, "
                f"Water {state['water_percentage']:.0f}%, "
                f"Suppressions: {state['suppression_count']}"
            )
        return "\n".join(lines)
    
    def should_request_guidance(self, step: int) -> bool:
        """Check if it's time for an LLM call."""
        if step == 0 and not self.guidance_history and self.current_strategy is None:
            return True
        self.steps_since_guidance += 1
        
        if self.steps_since_guidance >= self.llm_guidance_frequency:
            self.steps_since_guidance = 0
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return LLM usage stats."""
        return {
            'llm_calls': self.llm_calls,
            'llm_tokens_used': self.llm_tokens_used,
            'llm_errors': self.llm_errors,
            'guidance_requests': self.guidance_requests,
            'llm_query_attempts': self.llm_query_attempts,
            'valid_structured_responses': self.valid_structured_responses,
            'fallback_invocations': self.fallback_invocations,
            'heuristic_guidance_calls': self.heuristic_guidance_calls,
            'guidance_history_length': len(self.guidance_history),
            'avg_tokens_per_call': self.llm_tokens_used / max(1, self.llm_calls),
            'fallback_rate_percentage': (
                (self.fallback_invocations / self.llm_query_attempts) * 100.0
                if self.llm_query_attempts
                else None
            ),
        }


def test_hybrid_agent():
    """Quick test to see if the LLM agent works."""
    print("\n" + "="*60)
    print("TESTING HYBRID PPO + LLM AGENT")
    print("="*60 + "\n")
    
    # Create agent
    agent = HybridPPOLLMAgent(
        llm_model="meta-llama/Llama-2-7b-chat-hf",
        llm_guidance_frequency=10,
        hf_token=None  # will use HF_TOKEN env var if set
    )
    
    # Demo fire state from historical training data
    grid_size = 50
    fire_state = np.zeros((grid_size, grid_size), dtype=np.uint8)
    
    # Example fire clusters (simulated perimeter)
    fire_state[10:15, 10:15] = 1  # hotspot 1
    fire_state[30:35, 25:32] = 1  # hotspot 2
    fire_state[20:22, 40:43] = 1  # hotspot 3
    
    # Example drone setup
    drone_positions = [(5, 5), (25, 25), (40, 40)]  # GPS-style coords
    drone_states = [
        {'battery_percentage': 80, 'water_percentage': 60, 'suppression_count': 3},
        {'battery_percentage': 45, 'water_percentage': 30, 'suppression_count': 5},
        {'battery_percentage': 90, 'water_percentage': 80, 'suppression_count': 1}
    ]
    
    # Sample NOAA-style weather
    weather = {
        'temperature_f': 85,
        'wind_speed_mph': 15,
        'wind_direction': 'SW',
        'humidity': 25
    }
    
    # Get strategic guidance
    print("Requesting strategic guidance from LLM...\n")
    guidance = agent.get_strategic_guidance(
        fire_state=fire_state,
        drone_positions=drone_positions,
        drone_states=drone_states,
        weather=weather,
        step=100
    )
    
    print("\n" + "="*60)
    print("STRATEGIC GUIDANCE")
    print("="*60)
    print(json.dumps(guidance, indent=2))
    
    print("\n" + "="*60)
    print("AGENT STATISTICS")
    print("="*60)
    stats = agent.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Hybrid agent test complete!")


if __name__ == "__main__":
    test_hybrid_agent()
