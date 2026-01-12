#!/usr/bin/env python3
"""
Comprehensive Pipeline Test

Tests the complete book development pipeline from project creation
through all 22 layers to final marketing materials.
"""

import asyncio
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import BookProject, LAYERS, AgentStatus, LayerStatus
from models.agents import AGENT_REGISTRY, get_agent_execution_order
from core.orchestrator import Orchestrator, ExecutionContext


def test_project_creation():
    """Test creating a new project."""
    print("\n" + "="*60)
    print("TEST: Project Creation")
    print("="*60)

    orchestrator = Orchestrator()

    constraints = {
        "genre": "Dark Romance",
        "target_word_count": 75000,
        "description": "A forbidden love story between enemies in a dangerous world",
        "themes": ["redemption", "trust", "sacrifice"],
        "target_audience": "Adult women 25-45",
        "tone": "Dark, sensual, emotional",
        "comparable_titles": ["Twisted Love", "Den of Vipers"]
    }

    project = orchestrator.create_project("Shadows of Desire", constraints)

    # Verify project
    assert project is not None, "Project should be created"
    assert project.title == "Shadows of Desire", "Title should match"
    assert len(project.layers) == 22, f"Should have 22 layers, got {len(project.layers)}"

    # Count agents
    total_agents = sum(len(layer.agents) for layer in project.layers.values())
    assert total_agents == 34, f"Should have 34 agents, got {total_agents}"

    print(f"✓ Project created: {project.project_id}")
    print(f"✓ Layers: {len(project.layers)}")
    print(f"✓ Total agents: {total_agents}")

    return orchestrator, project


def test_agent_availability(orchestrator: Orchestrator, project: BookProject):
    """Test that agents become available correctly."""
    print("\n" + "="*60)
    print("TEST: Agent Availability")
    print("="*60)

    # Initially, only layer 0 should be available
    available = orchestrator.get_available_agents(project)
    print(f"Initially available: {available}")

    assert "orchestrator" in available, "Orchestrator should be available first"

    print(f"✓ Initial available agents: {available}")
    return True


async def test_agent_execution(orchestrator: Orchestrator, project: BookProject):
    """Test executing agents through the pipeline."""
    print("\n" + "="*60)
    print("TEST: Agent Execution (Demo Mode)")
    print("="*60)

    # Get execution order
    execution_order = get_agent_execution_order()
    print(f"Execution order has {len(execution_order)} agents")

    # Execute first 15 agents to test pipeline flow
    executed = []
    errors = []

    for i in range(min(15, len(execution_order))):
        available = orchestrator.get_available_agents(project)
        if not available:
            print(f"  No more agents available after {i} executions")
            break

        agent_id = available[0]
        try:
            output = await orchestrator.execute_agent(project, agent_id)
            executed.append(agent_id)
            gate_status = "PASSED" if output.gate_result and output.gate_result.passed else "FAILED"
            print(f"  ✓ {agent_id}: {gate_status}")
        except Exception as e:
            errors.append((agent_id, str(e)))
            print(f"  ✗ {agent_id}: ERROR - {e}")

    print(f"\n✓ Executed {len(executed)} agents")
    if errors:
        print(f"✗ {len(errors)} errors encountered")
        for agent_id, error in errors:
            print(f"  - {agent_id}: {error}")

    return executed, errors


async def test_story_bible_generation(orchestrator: Orchestrator, project: BookProject):
    """Test Story Bible generation specifically."""
    print("\n" + "="*60)
    print("TEST: Story Bible Generation")
    print("="*60)

    from agents.story_bible import execute_story_bible, format_story_bible_for_chapter

    # Create mock context
    context = ExecutionContext(
        project=project,
        inputs={
            "character_architecture": {
                "protagonist_profile": {
                    "name": "Isabella Romano",
                    "role": "Undercover agent",
                    "traits": ["intelligent", "guarded", "determined"]
                },
                "antagonist_profile": {
                    "name": "Vincent Blackwood",
                    "role": "Crime lord"
                }
            },
            "world_rules": {
                "physical_rules": {"geography": "New York City"},
            },
            "relationship_dynamics": {},
            "user_constraints": {"genre": "Dark Romance"}
        },
        llm_client=None  # Demo mode
    )

    result = await execute_story_bible(context)

    assert "character_registry" in result, "Should have character registry"
    assert "location_registry" in result, "Should have location registry"
    assert "timeline" in result, "Should have timeline"
    assert "consistency_rules" in result, "Should have consistency rules"

    print(f"✓ Story Bible generated")
    print(f"  - Characters: {len(result.get('character_registry', []))}")
    print(f"  - Locations: {len(result.get('location_registry', {}).get('key_locations', []))}")
    print(f"  - Timeline events: {len(result.get('timeline', {}).get('key_dates', []))}")

    # Test formatting for chapter writer
    formatted = format_story_bible_for_chapter(result)
    assert "STORY BIBLE" in formatted, "Formatted output should have header"
    print(f"✓ Story Bible formatted for chapter writer ({len(formatted)} chars)")

    return result


async def test_marketing_agents(orchestrator: Orchestrator, project: BookProject):
    """Test marketing agent generation."""
    print("\n" + "="*60)
    print("TEST: Marketing Agents")
    print("="*60)

    from agents.marketing import (
        execute_blurb_generator,
        execute_keyword_optimizer,
        execute_series_bible
    )

    # Create mock context
    context = ExecutionContext(
        project=project,
        inputs={
            "concept_definition": {
                "one_line_hook": "She was sent to destroy him. She never expected to fall.",
                "core_promise": {"transformation": "From enemies to lovers"}
            },
            "character_architecture": {
                "protagonist_profile": {"name": "Isabella", "role": "Undercover agent"}
            },
            "story_question": {
                "stakes_ladder": {"ultimate": {"risk": "Her life and her heart"}}
            },
            "user_constraints": {"genre": "Dark Romance", "themes": ["redemption", "trust"]},
            "story_bible": {},
            "draft_generation": {"chapters": []},
            "thematic_architecture": {},
            "plot_structure": {"major_beats": []}
        },
        llm_client=None
    )

    # Test blurb generator
    blurb = await execute_blurb_generator(context)
    assert "short_blurb" in blurb, "Should have short blurb"
    assert "full_blurb" in blurb, "Should have full blurb"
    assert "tagline" in blurb, "Should have tagline"
    print(f"✓ Blurb generated")
    print(f"  - Short: {blurb['short_blurb'][:60]}...")
    print(f"  - Tagline: {blurb['tagline'][:60]}...")

    # Test keyword optimizer
    keywords = await execute_keyword_optimizer(context)
    assert "primary_keywords" in keywords, "Should have primary keywords"
    assert len(keywords["primary_keywords"]) == 7, "Should have 7 primary keywords"
    print(f"✓ Keywords generated: {keywords['primary_keywords'][:3]}...")

    # Test series bible
    series = await execute_series_bible(context)
    assert "series_potential" in series, "Should have series potential"
    assert "unresolved_threads" in series, "Should have unresolved threads"
    print(f"✓ Series Bible generated")
    print(f"  - Potential: {series['series_potential']['score']}/10 ({series['series_potential']['type']})")

    return blurb, keywords, series


async def test_continuity_audit():
    """Test continuity audit with sample text."""
    print("\n" + "="*60)
    print("TEST: Continuity Audit")
    print("="*60)

    from agents.validation import execute_continuity_audit

    # Create a project with intentional inconsistencies
    orchestrator = Orchestrator()
    project = orchestrator.create_project("Test Book", {"genre": "Romance"})

    context = ExecutionContext(
        project=project,
        inputs={
            "draft_generation": {
                "chapters": [
                    {
                        "number": 1,
                        "text": "Vincent Blackwood walked into the room. He was from Chicago."
                    },
                    {
                        "number": 2,
                        "text": "Vincent Torrino smiled. The New York skyline was beautiful."
                    }
                ]
            },
            "story_bible": {
                "character_registry": [
                    {"canonical_name": "Vincent Blackwood", "role": "antagonist"}
                ],
                "location_registry": {"primary_city": "New York"},
                "timeline": {"key_dates": []}
            }
        },
        llm_client=None
    )

    result = await execute_continuity_audit(context)

    # Should detect name variation
    name_issues = result.get("character_logic_check", {}).get("issues", [])
    print(f"✓ Continuity audit completed")
    print(f"  - Name issues found: {len(name_issues)}")
    print(f"  - Location issues: {len(result.get('world_rule_check', {}).get('issues', []))}")
    print(f"  - Total issues: {result['continuity_report']['total_issues']}")

    return result


def test_layer_definitions():
    """Verify all layers are properly defined."""
    print("\n" + "="*60)
    print("TEST: Layer Definitions")
    print("="*60)

    # Check layers match agents
    for layer_id, layer_name in LAYERS.items():
        agents_in_layer = [a for a in AGENT_REGISTRY.values() if a.layer == layer_id]
        print(f"  Layer {layer_id}: {layer_name} ({len(agents_in_layer)} agents)")

    # Verify no orphan agents
    max_layer = max(LAYERS.keys())
    for agent_id, agent in AGENT_REGISTRY.items():
        assert agent.layer <= max_layer, f"Agent {agent_id} has layer {agent.layer} > max {max_layer}"

    print(f"✓ All {len(LAYERS)} layers verified")
    return True


async def run_all_tests():
    """Run the complete test suite."""
    print("\n" + "="*60)
    print("MILLION DOLLAR BOOK MACHINE - FULL PIPELINE TEST")
    print("="*60)

    results = {
        "passed": [],
        "failed": []
    }

    try:
        # Test 1: Layer definitions
        test_layer_definitions()
        results["passed"].append("Layer Definitions")
    except Exception as e:
        results["failed"].append(("Layer Definitions", str(e)))
        print(f"✗ FAILED: {e}")

    try:
        # Test 2: Project creation
        orchestrator, project = test_project_creation()
        results["passed"].append("Project Creation")
    except Exception as e:
        results["failed"].append(("Project Creation", str(e)))
        print(f"✗ FAILED: {e}")
        return results

    try:
        # Test 3: Agent availability
        test_agent_availability(orchestrator, project)
        results["passed"].append("Agent Availability")
    except Exception as e:
        results["failed"].append(("Agent Availability", str(e)))
        print(f"✗ FAILED: {e}")

    try:
        # Test 4: Agent execution
        executed, errors = await test_agent_execution(orchestrator, project)
        if not errors:
            results["passed"].append("Agent Execution")
        else:
            results["failed"].append(("Agent Execution", f"{len(errors)} errors"))
    except Exception as e:
        results["failed"].append(("Agent Execution", str(e)))
        print(f"✗ FAILED: {e}")

    try:
        # Test 5: Story Bible
        await test_story_bible_generation(orchestrator, project)
        results["passed"].append("Story Bible")
    except Exception as e:
        results["failed"].append(("Story Bible", str(e)))
        print(f"✗ FAILED: {e}")

    try:
        # Test 6: Marketing agents
        await test_marketing_agents(orchestrator, project)
        results["passed"].append("Marketing Agents")
    except Exception as e:
        results["failed"].append(("Marketing Agents", str(e)))
        print(f"✗ FAILED: {e}")

    try:
        # Test 7: Continuity audit
        await test_continuity_audit()
        results["passed"].append("Continuity Audit")
    except Exception as e:
        results["failed"].append(("Continuity Audit", str(e)))
        print(f"✗ FAILED: {e}")

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {len(results['passed'])}")
    for test in results["passed"]:
        print(f"  ✓ {test}")

    if results["failed"]:
        print(f"\nFailed: {len(results['failed'])}")
        for test, error in results["failed"]:
            print(f"  ✗ {test}: {error}")
    else:
        print("\n✓ ALL TESTS PASSED!")

    return results


if __name__ == "__main__":
    results = asyncio.run(run_all_tests())

    # Exit with error code if any tests failed
    if results["failed"]:
        sys.exit(1)
