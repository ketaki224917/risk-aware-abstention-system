"""Tests for syllabus-aligned agent architecture and ethics specification."""

from __future__ import annotations

from raa.agent_ethics import (
    AgentArchitecture,
    EthicsPerspective,
    TaskEnvironment,
    format_agent_ethics_summary,
    get_agent_architecture,
    get_ethics_perspectives,
    get_task_environment,
)


def test_task_environment_peas_completeness():
    env = get_task_environment()
    assert isinstance(env, TaskEnvironment)
    assert "Expected multi-objective clinical utility" in env.performance_measure
    assert "Tripartite routing actuator" in env.actuators
    assert "age" in env.sensors.lower() and "shape" in env.sensors.lower()
    assert env.observability.startswith("Partially observable")
    assert env.episodicity.startswith("Episodic")
    assert env.determinism.startswith("Stochastic")


def test_agent_architecture_utility_specification():
    arch = get_agent_architecture()
    assert isinstance(arch, AgentArchitecture)
    assert "Utility-Based" in arch.agent_type
    assert "Automatic" in arch.action_space
    assert "Assisted" in arch.action_space
    assert "Human Review" in arch.action_space
    assert "Risk" in arch.utility_function
    assert "Epistemic override" in arch.decision_policy


def test_ethics_perspectives_contain_three_schools():
    ethics = get_ethics_perspectives()
    assert set(ethics.keys()) == {"utilitarian", "deontological", "virtue_ethics"}
    for _key, pers in ethics.items():
        assert isinstance(pers, EthicsPerspective)
        assert len(pers.framework_name) > 0
        assert len(pers.core_principle) > 0
        assert len(pers.agent_manifestation) > 0
        assert len(pers.concrete_tradeoff) > 0

    assert "asymmetric clinical consequence" in ethics["utilitarian"].agent_manifestation
    assert "Duty of Epistemic Honesty" in ethics["deontological"].agent_manifestation
    assert "Intellectual Humility" in ethics["virtue_ethics"].agent_manifestation


def test_format_agent_ethics_summary_is_serializable():
    summary = format_agent_ethics_summary()
    assert "task_environment" in summary
    assert "agent_architecture" in summary
    assert "ethics_frameworks" in summary
    assert summary["agent_architecture"]["type"].startswith("Utility-Based")
    assert len(summary["ethics_frameworks"]) == 3
