import asyncio
import pytest
from friday.core.task_scheduler import TaskScheduler, ScheduledTask


@pytest.mark.asyncio
async def test_scheduled_task_runs():
    results = []

    async def my_coro():
        results.append("done")
        return 42

    st = ScheduledTask(0.01, my_coro())
    val = await st.run()
    assert val == 42
    assert results == ["done"]


@pytest.mark.asyncio
async def test_task_scheduler_add_and_start():
    scheduler = TaskScheduler()
    results = []

    async def task_a():
        results.append("a")

    async def task_b():
        results.append("b")

    id_a = await scheduler.add(0.01, task_a())
    id_b = await scheduler.add(0.02, task_b())
    assert id_a is not None
    assert id_b is not None
    assert isinstance(id_a, str)

    await scheduler.start()
    await asyncio.sleep(0.1)
    await scheduler.stop()

    assert "a" in results
    assert "b" in results


@pytest.mark.asyncio
async def test_task_scheduler_task_id():
    scheduler = TaskScheduler()

    async def noop():
        pass

    cid = await scheduler.add(0.01, noop(), task_id="custom-id")
    assert cid == "custom-id"
    await scheduler.stop()
