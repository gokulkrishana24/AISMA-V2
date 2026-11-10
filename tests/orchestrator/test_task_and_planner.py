import pytest

from orchestrator.planner import TaskPlanner
from schemas.task import Task, TaskStatus


def test_task_validation_and_legal_transitions():
    t = Task(task_id="1", business_id="b", agent_id="market_radar", task_type="competitor_analysis", objective="x")
    assert t.status == TaskStatus.QUEUED
    t2 = t.transition_to(TaskStatus.VALIDATED)
    t3 = t2.transition_to(TaskStatus.RUNNING)
    assert t3.status == TaskStatus.RUNNING
    with pytest.raises(ValueError):
        t.transition_to(TaskStatus.COMPLETED)  # illegal jump


def test_dependency_planning_batches():
    planner = TaskPlanner()
    tasks = [
        Task(task_id="a", business_id="b", agent_id="x", task_type="t", objective="o"),
        Task(task_id="b", business_id="b", agent_id="x", task_type="t", objective="o", dependencies=["a"]),
        Task(task_id="c", business_id="b", agent_id="x", task_type="t", objective="o", dependencies=["a"]),
    ]
    plan = planner.plan(tasks, strategy="dependency_based")
    batches = plan["batches"]
    assert len(batches) == 2
    assert batches[0][0]["task_id"] == "a"
    assert {batches[1][0]["task_id"], batches[1][1]["task_id"]} == {"b", "c"}


def test_sequential_planning():
    planner = TaskPlanner()
    tasks = [
        Task(task_id="2", business_id="b", agent_id="x", task_type="t", objective="o", priority=1),
        Task(task_id="1", business_id="b", agent_id="x", task_type="t", objective="o", priority=10),
    ]
    plan = planner.plan(tasks, strategy="sequential")
    assert plan["ordered_task_ids"] == ["1", "2"]
