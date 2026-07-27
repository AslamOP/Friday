import pytest
from friday.tools.system_monitor import SystemMonitor, SystemMetrics, MonitorResult


@pytest.mark.asyncio
async def test_collect_returns_result():
    sm = SystemMonitor()
    result = await sm.collect()
    assert isinstance(result, MonitorResult)
    assert result.success


@pytest.mark.asyncio
async def test_metrics_contains_cpu():
    sm = SystemMonitor()
    result = await sm.collect()
    assert result.metrics is not None
    assert result.metrics.cpu_percent >= 0
    assert result.metrics.cpu_cores > 0


@pytest.mark.asyncio
async def test_metrics_contains_memory():
    sm = SystemMonitor()
    result = await sm.collect()
    assert result.metrics is not None
    assert result.metrics.memory_total_gb > 0
    assert result.metrics.memory_percent > 0


@pytest.mark.asyncio
async def test_metrics_contains_disk():
    sm = SystemMonitor()
    result = await sm.collect()
    assert result.metrics is not None
    assert result.metrics.disk_total_gb > 0


@pytest.mark.asyncio
async def test_output_is_readable():
    sm = SystemMonitor()
    result = await sm.collect()
    assert "CPU" in result.output
    assert "RAM" in result.output
    assert "DISK" in result.output
    assert "GPU" in result.output
