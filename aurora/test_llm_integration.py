#!/usr/bin/env python3
"""
Test script for LLM integration in AURORA

This script demonstrates how to enable real LLM integration
and shows the difference between mock and real LLM responses.
"""

import numpy as np
import os
from agents.llm_strategy_agent import LLMStrategyAgent

def test_llm_integration():
    """Test LLM integration with different configurations."""
    
    print("🤖 AURORA LLM Integration Test")
    print("=" * 50)
    
    # Create sample simulation data
    fire_state = np.zeros((20, 20))
    fire_state[8:12, 8:12] = 1  # Some fire in the center
    
    terrain = np.random.rand(20, 20) * 100
    
    agent_positions = [(5, 5), (15, 5), (10, 15)]
    agent_statuses = [
        {"is_active": True, "battery_percentage": 80, "water_percentage": 60},
        {"is_active": True, "battery_percentage": 30, "water_percentage": 90},
        {"is_active": True, "battery_percentage": 95, "water_percentage": 20}
    ]
    
    weather = {
        "temperature": 85,
        "humidity": 30,
        "wind_speed": 15,
        "wind_direction": "NW"
    }
    
    print("\n📊 Sample Simulation Data:")
    print(f"Fire coverage: {np.sum(fire_state > 0) / fire_state.size * 100:.1f}%")
    print(f"Active agents: {len(agent_positions)}")
    print(f"Average battery: {np.mean([s['battery_percentage'] for s in agent_statuses]):.1f}%")
    
    # Test 1: Mock LLM (current default)
    print("\n🧪 Test 1: Mock LLM Strategy")
    print("-" * 30)
    
    mock_llm = LLMStrategyAgent(use_mock=True)
    
    # Analyze situation
    situation = mock_llm.analyze_situation(
        fire_state, terrain, agent_positions, agent_statuses, weather, 0
    )
    
    print(f"Threat level: {situation['threat_assessment']['level']}")
    print(f"Fire coverage: {situation['fire_metrics']['coverage_percentage']:.1f}%")
    
    # Generate strategy
    strategy = mock_llm.generate_strategy(situation)
    
    print(f"Strategy: {strategy['strategy']}")
    print(f"Description: {strategy['description']}")
    print(f"LLM Model: {strategy.get('llm_model', 'unknown')}")
    
    # Test 2: Real LLM (if available)
    print("\n🤖 Test 2: Real LLM Strategy")
    print("-" * 30)
    
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        print("✅ OpenAI API key found - testing real LLM...")
        
        real_llm = LLMStrategyAgent(
            model="gpt-4o-mini",
            api_key=api_key,
            use_mock=False
        )
        
        # Generate strategy with real LLM
        real_strategy = real_llm.generate_strategy(situation)
        
        print(f"Strategy: {real_strategy.get('strategy', 'N/A')}")
        print(f"Description: {real_strategy.get('description', 'N/A')}")
        print(f"LLM Model: {real_strategy.get('llm_model', 'unknown')}")
        
        # Compare strategies
        print("\n📈 Strategy Comparison:")
        print(f"Mock Strategy: {strategy['strategy']}")
        print(f"Real LLM Strategy: {real_strategy.get('strategy', 'N/A')}")
        
    else:
        print("⚠️  No OpenAI API key found")
        print("To test real LLM:")
        print("1. Get API key from https://platform.openai.com/api-keys")
        print("2. Set environment variable: export OPENAI_API_KEY='your-key'")
        print("3. Run this script again")
    
    # Test 3: Agent-specific guidance
    print("\n🎯 Test 3: Agent-Specific Guidance")
    print("-" * 30)
    
    for i, agent_id in enumerate([f"drone_{i}" for i in range(3)]):
        guidance = mock_llm.get_agent_guidance(
            agent_id, strategy, agent_positions[i], agent_statuses[i]
        )
        
        print(f"{agent_id}:")
        print(f"  Action: {guidance['action']}")
        print(f"  Reason: {guidance['reason']}")
        print(f"  Priority: {guidance.get('priority', 'N/A')}")
    
    print("\n✅ LLM Integration Test Complete!")
    
    # Summary
    print("\n📋 Summary:")
    print("✅ Mock LLM: Working (default)")
    if api_key:
        print("✅ Real LLM: Available and tested")
    else:
        print("⚠️  Real LLM: API key needed")
    
    print("\n🚀 To enable real LLM in AURORA:")
    print("1. Get OpenAI API key")
    print("2. Set OPENAI_API_KEY environment variable")
    print("3. Run: ./run.sh phase3-full")
    print("4. LLM will automatically be used for strategy generation")

if __name__ == "__main__":
    test_llm_integration() 