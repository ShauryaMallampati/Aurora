"""
Hybrid PPO + LLM Agent for AURORA

This agent combines:
1. PPO (Proximal Policy Optimization) for low-level action execution
2. LLM (GPT-4o-mini or LLaMA) for high-level strategic guidance

The LLM provides strategic decisions every N steps:
- Which area of the fire to prioritize
- Resource allocation across drones
- When to retreat/recharge vs. continue suppression

PPO handles the low-level actions:
- Movement (up/down/left/right)
- Suppression timing
- Battery/water management

This hybrid approach leverages:
- LLM: Strategic reasoning, contextual understanding, long-term planning
- PPO: Fast, reactive, learned motor skills and tactics

Author: Shaurya Mallampati
Date: October 13, 2025
ISEF 2025 Competition
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import json
from datetime import datetime
import os

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️  Transformers not available. Install with: pip install transformers torch")


class HybridPPOLLMAgent:
    """Hybrid agent combining PPO execution with LLM strategic guidance."""
    
    def __init__(self,
                 llm_model: str = "meta-llama/Llama-3.2-1B-Instruct",
                 llm_guidance_frequency: int = 10,
                 temperature: float = 0.7,
                 hf_token: Optional[str] = None,
                 llm_backend: str = "gemini",
                 device: str = "auto"):
        """Initialize hybrid agent.
        
        Args:
            llm_model: HuggingFace model ID (meta-llama/Llama-2-7b-chat-hf, etc.)
            llm_guidance_frequency: Steps between LLM consultations
            temperature: LLM sampling temperature
            hf_token: HuggingFace API token (or set HF_TOKEN env var)
            device: Device to run model on ("cuda", "cpu", or "auto")
        """
        self.llm_model = llm_model
        self.llm_guidance_frequency = llm_guidance_frequency
        self.temperature = temperature
        self.llm_backend = llm_backend.lower() if isinstance(llm_backend, str) else llm_backend
        
        # Initialize LLM
        self.model = None
        self.tokenizer = None
        self.pipe = None
        
        # If Gemini backend is selected, skip attempting to load heavy HF models to avoid
        # long downloads or gated model failures. We'll use Gemini API for strategic guidance.
        hf_token = hf_token or "[REDACTED]"
        if self.llm_backend == 'gemini':
            print("🔁 Gemini backend selected — skipping transformers model load.")
            # Ensure gemini API key is set (hardcoded per user request)
            self.gemini_api_key = getattr(self, 'gemini_api_key', None) or "[REDACTED_GOOGLE_KEY]"
            self.gemini_model = getattr(self, 'gemini_model', None) or "text-bison-001"
        else:
            if TRANSFORMERS_AVAILABLE:
                # Keep an HF token available (left in code per user request). WARNING: embedding
                # tokens in source is insecure; prefer HF_TOKEN env var or passing hf_token.
                if hf_token:
                    print("🔒 HuggingFace token present in code (will be used for gated meta-llama models).")
                else:
                    print("⚠️  No HuggingFace token found. Using heuristic fallback for strategic guidance if model load fails.")

                # Attempt to load the requested model. For gated/meta-llama models we will pass the token.
                try:
                    # Determine device
                    if device == "auto":
                        device = "cuda" if torch.cuda.is_available() else "cpu"

                    # Decide whether model is a meta-llama gated model
                    is_meta_llama = llm_model.startswith("meta-llama") or llm_model.startswith("meta/llama")

                    # Load tokenizer: pass token only if model is gated and token is available
                    tokenizer_kwargs = {"trust_remote_code": True}
                    if is_meta_llama and hf_token:
                        tokenizer_kwargs["token"] = hf_token

                    self.tokenizer = AutoTokenizer.from_pretrained(
                        llm_model,
                        **tokenizer_kwargs
                    )

                    # Choose dtype and device_map recommendations
                    # For Llama 3.2 family, BF16 is recommended; fall back to float32 on CPU
                    if is_meta_llama:
                        torch_dtype = torch.bfloat16 if device == "cuda" else torch.float32
                        device_map = "auto"
                    else:
                        torch_dtype = torch.float16 if device == "cuda" else torch.float32
                        device_map = device if device in ("cpu", "cuda") else "auto"

                    model_kwargs = {
                        "torch_dtype": torch_dtype,
                        "device_map": device_map,
                        "trust_remote_code": True
                    }
                    if is_meta_llama and hf_token:
                        model_kwargs["token"] = hf_token

                    self.model = AutoModelForCausalLM.from_pretrained(
                        llm_model,
                        **model_kwargs
                    )

                    # Create pipeline
                    self.pipe = pipeline(
                        "text-generation",
                        model=self.model,
                        tokenizer=self.tokenizer,
                        max_new_tokens=512,
                        temperature=temperature,
                        do_sample=True,
                        top_p=0.95
                    )

                    print(f"✅ LLM loaded on {device}: {llm_model}")

                except Exception as e:
                    print(f"⚠️  Error loading LLM: {e}")
                    print("    Using heuristic fallback for strategic guidance.")
            else:
                print("⚠️  Transformers library not available. Using heuristic fallback.")
        # If user selected Gemini backend, store API key (hardcoded per user request)
        if self.llm_backend == 'gemini':
            # WARNING: embedding API keys in source is insecure.
            self.gemini_api_key = "[REDACTED_GOOGLE_KEY]"
            self.gemini_model = "text-bison-001"  # change to preferred Gemini model if needed
            print("🔁 Gemini backend selected for LLM calls.")
        else:
            print("⚠️  Transformers library not available. Using heuristic fallback.")
        
        # Strategic guidance state
        self.current_strategy = None
        self.steps_since_guidance = 0
        self.guidance_history = []
        
        # Statistics
        self.llm_calls = 0
        self.llm_tokens_used = 0
        self.llm_errors = 0
        
    def get_strategic_guidance(self, 
                              fire_state: np.ndarray,
                              drone_positions: List[Tuple[int, int]],
                              drone_states: List[Dict],
                              weather: Dict,
                              step: int) -> Dict[str, Any]:
        """Get high-level strategic guidance from LLM.
        
        Args:
            fire_state: Grid showing fire locations (0=safe, 1=burning, 2=burnt)
            drone_positions: List of (row, col) positions
            drone_states: List of dicts with battery, water, etc.
            weather: Dict with temperature, wind, humidity
            step: Current simulation step
            
        Returns:
            Dict with strategic guidance:
            - priority_zones: List of (row, col) areas to prioritize
            - drone_assignments: Which drone should focus where
            - resource_strategy: When to retreat/recharge
            - reasoning: Explanation of strategy
        """
        
        if not self.pipe:
            # Fallback: simple heuristic strategy
            return self._fallback_strategy(fire_state, drone_positions, drone_states)
        
        try:
            # Analyze current situation
            total_burning = np.sum(fire_state == 1)
            grid_size = fire_state.shape[0]
            fire_pct = (total_burning / (grid_size * grid_size)) * 100
            
            # Find fire hotspots (clusters of burning cells)
            hotspots = self._find_fire_hotspots(fire_state)
            
            # Summarize drone states
            avg_battery = np.mean([d['battery_percentage'] for d in drone_states])
            avg_water = np.mean([d['water_percentage'] for d in drone_states])
            
            # Construct prompt for Llama-2 with proper chat format
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

            # Format prompt for Llama-2-chat
            prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_prompt} [/INST]"
            
            # Generate response via selected backend
            if self.llm_backend == 'gemini':
                response_text = self._call_gemini(prompt)
            else:
                outputs = self.pipe(prompt, max_new_tokens=400, temperature=self.temperature)
                response_text = outputs[0].get('generated_text', '')
            
            # Extract JSON from response (after [/INST])
            if '[/INST]' in response_text:
                json_text = response_text.split('[/INST]')[-1].strip()
            else:
                json_text = response_text
            
            # Try to extract JSON
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', json_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                guidance = json.loads(json_str)
            else:
                # Fallback if no JSON found
                raise ValueError("No valid JSON in response")
            
            # Update statistics
            self.llm_calls += 1
            # Estimate tokens (rough approximation)
            prompt_tokens = len(prompt.split())
            response_tokens = len(json_text.split())
            self.llm_tokens_used += prompt_tokens + response_tokens
            
            # Store guidance
            guidance['timestamp'] = datetime.now().isoformat()
            guidance['step'] = step
            self.guidance_history.append(guidance)
            
            print(f"🧠 Llama Strategy: {guidance.get('resource_strategy', 'N/A')} - {guidance.get('reasoning', 'N/A')[:80]}...")
            
            return guidance
            
        except Exception as e:
            print(f"⚠️  LLM error: {e}")
            self.llm_errors += 1
            return self._fallback_strategy(fire_state, drone_positions, drone_states)

    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini / Generative Language API (text-bison endpoint).

        This uses an API key (hardcoded above). Returns the text output or raises an exception.
        """
        try:
            import requests

            api_key = getattr(self, 'gemini_api_key', None)
            if not api_key:
                raise RuntimeError('Gemini API key not configured')

            url = f'https://generativelanguage.googleapis.com/v1/models/{self.gemini_model}:generate?key={api_key}'
            headers = {'Content-Type': 'application/json'}
            body = {
                'prompt': { 'text': prompt },
                'temperature': float(self.temperature),
                'maxOutputTokens': 512,
            }

            resp = requests.post(url, json=body, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            # text-bison returns candidates[0].output
            if 'candidates' in data and len(data['candidates']) > 0 and 'output' in data['candidates'][0]:
                return data['candidates'][0]['output']
            # chat-like responses may be in 'output' or 'content'
            if 'output' in data:
                return data['output']
            return json.dumps(data)

        except Exception as e:
            raise RuntimeError(f'Gemini API error: {e}')
    
    def _fallback_strategy(self, fire_state, drone_positions, drone_states) -> Dict:
        """Simple heuristic strategy when LLM unavailable."""
        
        hotspots = self._find_fire_hotspots(fire_state)
        
        # Priority zones = largest hotspots
        priority_zones = [h['centroid'] for h in hotspots[:5]]
        
        # Assign drones to nearest priority zones
        assignments = {}
        for i, pos in enumerate(drone_positions):
            if priority_zones:
                # Find nearest zone
                distances = [abs(pos[0] - z[0]) + abs(pos[1] - z[1]) for z in priority_zones]
                nearest_idx = np.argmin(distances)
                assignments[f"drone_{i}"] = nearest_idx
        
        return {
            'priority_zones': priority_zones,
            'drone_assignments': assignments,
            'resource_strategy': 'balanced',
            'retreat_threshold': 20,
            'reasoning': 'Heuristic fallback: target largest fire clusters',
            'source': 'heuristic'
        }
    
    def _find_fire_hotspots(self, fire_state: np.ndarray, min_size: int = 5) -> List[Dict]:
        """Find clusters of burning cells."""
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
        """Get bounding box of a binary mask."""
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
        """Format drone state info for prompt."""
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
        """Check if it's time to request new strategic guidance."""
        self.steps_since_guidance += 1
        
        if self.steps_since_guidance >= self.llm_guidance_frequency:
            self.steps_since_guidance = 0
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            'llm_calls': self.llm_calls,
            'llm_tokens_used': self.llm_tokens_used,
            'llm_errors': self.llm_errors,
            'guidance_history_length': len(self.guidance_history),
            'avg_tokens_per_call': self.llm_tokens_used / max(1, self.llm_calls)
        }


def test_hybrid_agent():
    """Test the hybrid agent."""
    print("\n" + "="*60)
    print("TESTING HYBRID PPO + LLM AGENT")
    print("="*60 + "\n")
    
    # Create agent
    agent = HybridPPOLLMAgent(
        llm_model="meta-llama/Llama-2-7b-chat-hf",
        llm_guidance_frequency=10,
        hf_token=None  # Will use HF_TOKEN env var if set
    )
    
    # Create mock fire state
    grid_size = 50
    fire_state = np.zeros((grid_size, grid_size), dtype=np.uint8)
    
    # Add some fire clusters
    fire_state[10:15, 10:15] = 1  # Hotspot 1
    fire_state[30:35, 25:32] = 1  # Hotspot 2
    fire_state[20:22, 40:43] = 1  # Hotspot 3
    
    # Mock drone states
    drone_positions = [(5, 5), (25, 25), (40, 40)]
    drone_states = [
        {'battery_percentage': 80, 'water_percentage': 60, 'suppression_count': 3},
        {'battery_percentage': 45, 'water_percentage': 30, 'suppression_count': 5},
        {'battery_percentage': 90, 'water_percentage': 80, 'suppression_count': 1}
    ]
    
    # Mock weather
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
