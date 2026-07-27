import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("friday.system_monitor")


@dataclass
class SystemMetrics:
    cpu_percent: float = 0.0
    cpu_cores: int = 0
    cpu_temp: float | None = None
    memory_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    gpu_available: bool = False
    gpu_util: float | None = None
    gpu_memory_used_mb: float | None = None
    gpu_memory_total_mb: float | None = None
    gpu_name: str = ""


@dataclass
class MonitorResult:
    success: bool
    metrics: SystemMetrics | None = None
    output: str = ""
    error: str = ""


class SystemMonitor:
    async def collect(self) -> MonitorResult:
        try:
            metrics = SystemMetrics()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._cpu(metrics))
            await loop.run_in_executor(None, lambda: self._memory(metrics))
            await loop.run_in_executor(None, lambda: self._disk(metrics))
            await self._gpu(metrics)
            lines = [
                f"CPU:  {metrics.cpu_percent}% ({metrics.cpu_cores} cores)" +
                (f" {metrics.cpu_temp}°C" if metrics.cpu_temp is not None else ""),
                f"RAM:  {metrics.memory_used_gb:.1f}/{metrics.memory_total_gb:.1f} GB ({metrics.memory_percent}%)",
                f"DISK: {metrics.disk_used_gb:.1f}/{metrics.disk_total_gb:.1f} GB ({metrics.disk_percent}%)",
            ]
            if metrics.gpu_available:
                lines.append(f"GPU:  {metrics.gpu_name} util={metrics.gpu_util}% mem={metrics.gpu_memory_used_mb:.0f}/{metrics.gpu_memory_total_mb:.0f} MB")
            else:
                lines.append("GPU:  not detected")
            return MonitorResult(success=True, metrics=metrics, output="\n".join(lines))
        except Exception as e:
            return MonitorResult(success=False, error=str(e))

    def _cpu(self, m: SystemMetrics):
        import psutil
        m.cpu_percent = psutil.cpu_percent(interval=0.5)
        m.cpu_cores = psutil.cpu_count(logical=True)
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                m.cpu_temp = round(int(f.read().strip()) / 1000, 1)
        except Exception:
            pass

    def _memory(self, m: SystemMetrics):
        import psutil
        mem = psutil.virtual_memory()
        m.memory_percent = round(mem.percent, 1)
        m.memory_used_gb = round(mem.used / (1024**3), 1)
        m.memory_total_gb = round(mem.total / (1024**3), 1)

    def _disk(self, m: SystemMetrics):
        import psutil
        d = psutil.disk_usage("/")
        m.disk_percent = round(d.percent, 1)
        m.disk_used_gb = round(d.used / (1024**3), 1)
        m.disk_total_gb = round(d.total / (1024**3), 1)

    async def _gpu(self, m: SystemMetrics):
        try:
            proc = await asyncio.create_subprocess_exec(
                "nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0 and stdout:
                line = stdout.decode().strip().split("\n")[0]
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 5:
                    m.gpu_available = True
                    m.gpu_name = parts[1]
                    m.gpu_util = float(parts[2])
                    m.gpu_memory_used_mb = float(parts[3])
                    m.gpu_memory_total_mb = float(parts[4])
        except Exception:
            pass
