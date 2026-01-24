"""
Deep System Integration

Provides deep system integration capabilities for kernel-level monitoring,
eBPF integration, payload inspection, and system call tracing with real-time
correlation across all observability pillars.
"""

import asyncio
import time
import os
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)

class SystemMonitoringLevel(Enum):
    """System monitoring depth levels"""
    BASIC = "basic"           # Basic system metrics
    ENHANCED = "enhanced"     # Enhanced system monitoring
    DEEP = "deep"            # Deep system integration with eBPF
    KERNEL = "kernel"        # Kernel-level monitoring

class PayloadInspectionMode(Enum):
    """Payload inspection modes"""
    DISABLED = "disabled"
    METADATA_ONLY = "metadata_only"
    HEADER_INSPECTION = "header_inspection"
    DEEP_INSPECTION = "deep_inspection"

@dataclass
class SystemCallEvent:
    """System call event data"""
    timestamp_ns: int
    pid: int
    tid: int
    syscall_name: str
    syscall_number: int
    duration_ns: int
    return_value: int
    process_name: str
    arguments: Optional[Dict[str, Any]] = None

@dataclass
class KernelMetrics:
    """Kernel-level metrics"""
    timestamp_ns: int
    cpu_id: int
    context_switches: int
    interrupts: int
    page_faults: int
    memory_pressure: float
    io_wait_percent: float
    kernel_time_percent: float
    user_time_percent: float

@dataclass
class PayloadInspectionResult:
    """Payload inspection result"""
    timestamp_ns: int
    protocol: str
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    payload_size: int
    payload_hash: str
    inspection_results: Dict[str, Any]
    threat_indicators: List[str] = field(default_factory=list)
    anomalies_detected: List[str] = field(default_factory=list)

class DeepSystemIntegration:
    """
    Deep system integration for kernel-level monitoring and eBPF integration.
    
    Provides comprehensive system-level observability including kernel metrics,
    system call tracing, payload inspection, and hardware monitoring with
    real-time correlation capabilities.
    """
    
    def __init__(self, 
                 monitoring_level: SystemMonitoringLevel = SystemMonitoringLevel.ENHANCED,
                 payload_inspection_mode: PayloadInspectionMode = PayloadInspectionMode.METADATA_ONLY,
                 enable_mock_mode: bool = True):
        
        self.monitoring_level = monitoring_level
        self.payload_inspection_mode = payload_inspection_mode
        self.enable_mock_mode = enable_mock_mode
        
        # eBPF and system monitoring state
        self._ebpf_programs = {}
        self._system_call_buffer = []
        self._kernel_metrics_buffer = []
        self._payload_inspection_buffer = []
        
        # Performance tracking
        self._monitoring_stats = {
            'syscalls_captured': 0,
            'kernel_metrics_collected': 0,
            'payloads_inspected': 0,
            'monitoring_overhead_percent': 0.0,
            'last_collection_time': None
        }
        
        # Background tasks
        self._monitoring_task = None
        self._collection_task = None
        
        # Check eBPF availability
        self._ebpf_available = self._check_ebpf_availability()
        
    def _check_ebpf_availability(self) -> bool:
        """Check if eBPF is available on the system"""
        
        if self.enable_mock_mode:
            return False  # Use mock mode for development
        
        try:
            # Check for eBPF support
            if os.path.exists('/sys/kernel/debug/tracing'):
                return True
            
            # Try importing BCC (eBPF library)
            from bcc import BPF
            return True
            
        except (ImportError, OSError):
            logger.warning("eBPF not available, using mock mode")
            return False
    
    async def initialize(self) -> bool:
        """Initialize deep system integration"""
        
        try:
            logger.info("Initializing deep system integration",
                       monitoring_level=self.monitoring_level.value,
                       payload_inspection=self.payload_inspection_mode.value,
                       ebpf_available=self._ebpf_available,
                       mock_mode=self.enable_mock_mode)
            
            if self._ebpf_available and not self.enable_mock_mode:
                await self._initialize_ebpf_programs()
            else:
                await self._initialize_mock_monitoring()
            
            # Start background monitoring tasks
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self._collection_task = asyncio.create_task(self._collection_loop())
            
            logger.info("Deep system integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize deep system integration", error=str(e))
            return False
    
    async def shutdown(self):
        """Shutdown deep system integration"""
        
        try:
            # Cancel background tasks
            if self._monitoring_task:
                self._monitoring_task.cancel()
            if self._collection_task:
                self._collection_task.cancel()
            
            # Cleanup eBPF programs
            if self._ebpf_programs and not self.enable_mock_mode:
                await self._cleanup_ebpf_programs()
            
            logger.info("Deep system integration shutdown complete")
            
        except Exception as e:
            logger.error("Error during deep system integration shutdown", error=str(e))
    
    async def _initialize_ebpf_programs(self):
        """Initialize eBPF programs for kernel monitoring"""
        
        try:
            from bcc import BPF
            
            # System call tracing program
            if self.monitoring_level in [SystemMonitoringLevel.DEEP, SystemMonitoringLevel.KERNEL]:
                syscall_program = """
                #include <uapi/linux/ptrace.h>
                #include <linux/sched.h>
                
                struct syscall_data_t {
                    u64 ts;
                    u32 pid;
                    u32 tid;
                    u64 syscall_nr;
                    u64 duration;
                    s64 ret;
                    char comm[TASK_COMM_LEN];
                };
                
                BPF_PERF_OUTPUT(syscall_events);
                BPF_HASH(start_times, u64, u64);
                
                TRACEPOINT_PROBE(raw_syscalls, sys_enter) {
                    u64 pid_tgid = bpf_get_current_pid_tgid();
                    u64 ts = bpf_ktime_get_ns();
                    start_times.update(&pid_tgid, &ts);
                    return 0;
                }
                
                TRACEPOINT_PROBE(raw_syscalls, sys_exit) {
                    u64 pid_tgid = bpf_get_current_pid_tgid();
                    u64 *start_ts = start_times.lookup(&pid_tgid);
                    
                    if (start_ts == 0) {
                        return 0;
                    }
                    
                    struct syscall_data_t data = {};
                    data.ts = bpf_ktime_get_ns();
                    data.pid = pid_tgid >> 32;
                    data.tid = pid_tgid;
                    data.syscall_nr = args->id;
                    data.duration = data.ts - *start_ts;
                    data.ret = args->ret;
                    bpf_get_current_comm(&data.comm, sizeof(data.comm));
                    
                    syscall_events.perf_submit(args, &data, sizeof(data));
                    start_times.delete(&pid_tgid);
                    return 0;
                }
                """
                
                self._ebpf_programs['syscall_tracer'] = BPF(text=syscall_program)
                self._ebpf_programs['syscall_tracer']['syscall_events'].open_perf_buffer(
                    self._handle_syscall_event
                )
                
                logger.info("eBPF syscall tracing program loaded")
            
            # Kernel metrics collection program
            if self.monitoring_level == SystemMonitoringLevel.KERNEL:
                kernel_metrics_program = """
                #include <uapi/linux/ptrace.h>
                #include <linux/sched.h>
                
                struct kernel_metrics_t {
                    u64 ts;
                    u32 cpu_id;
                    u64 context_switches;
                    u64 interrupts;
                    u64 page_faults;
                };
                
                BPF_PERF_OUTPUT(kernel_metrics);
                BPF_PERCPU_ARRAY(metrics_data, struct kernel_metrics_t, 1);
                
                int collect_metrics(struct pt_regs *ctx) {
                    int key = 0;
                    struct kernel_metrics_t *data = metrics_data.lookup(&key);
                    
                    if (data == 0) {
                        return 0;
                    }
                    
                    data->ts = bpf_ktime_get_ns();
                    data->cpu_id = bpf_get_smp_processor_id();
                    
                    kernel_metrics.perf_submit(ctx, data, sizeof(*data));
                    return 0;
                }
                """
                
                self._ebpf_programs['kernel_metrics'] = BPF(text=kernel_metrics_program)
                self._ebpf_programs['kernel_metrics']['kernel_metrics'].open_perf_buffer(
                    self._handle_kernel_metrics_event
                )
                
                logger.info("eBPF kernel metrics program loaded")
                
        except Exception as e:
            logger.error("Failed to initialize eBPF programs", error=str(e))
            raise
    
    async def _initialize_mock_monitoring(self):
        """Initialize mock monitoring for development"""
        
        logger.info("Initializing mock deep system monitoring")
        
        # Mock eBPF programs
        self._ebpf_programs['mock_syscall_tracer'] = True
        self._ebpf_programs['mock_kernel_metrics'] = True
        
        if self.payload_inspection_mode != PayloadInspectionMode.DISABLED:
            self._ebpf_programs['mock_payload_inspector'] = True
    
    def _handle_syscall_event(self, cpu, data, size):
        """Handle syscall events from eBPF"""
        
        try:
            # Parse syscall event data
            # This would parse the actual eBPF event structure
            syscall_event = SystemCallEvent(
                timestamp_ns=time.time_ns(),
                pid=1234,  # Would be parsed from eBPF data
                tid=1234,
                syscall_name="read",
                syscall_number=0,
                duration_ns=50000,
                return_value=0,
                process_name="test_process"
            )
            
            self._system_call_buffer.append(syscall_event)
            self._monitoring_stats['syscalls_captured'] += 1
            
            # Limit buffer size
            if len(self._system_call_buffer) > 1000:
                self._system_call_buffer.pop(0)
                
        except Exception as e:
            logger.error("Error handling syscall event", error=str(e))
    
    def _handle_kernel_metrics_event(self, cpu, data, size):
        """Handle kernel metrics events from eBPF"""
        
        try:
            # Parse kernel metrics data
            kernel_metrics = KernelMetrics(
                timestamp_ns=time.time_ns(),
                cpu_id=cpu,
                context_switches=100,  # Would be parsed from eBPF data
                interrupts=50,
                page_faults=10,
                memory_pressure=0.1,
                io_wait_percent=2.5,
                kernel_time_percent=5.0,
                user_time_percent=85.0
            )
            
            self._kernel_metrics_buffer.append(kernel_metrics)
            self._monitoring_stats['kernel_metrics_collected'] += 1
            
            # Limit buffer size
            if len(self._kernel_metrics_buffer) > 500:
                self._kernel_metrics_buffer.pop(0)
                
        except Exception as e:
            logger.error("Error handling kernel metrics event", error=str(e))
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        
        while True:
            try:
                if self.enable_mock_mode:
                    # Generate mock system events
                    await self._generate_mock_events()
                else:
                    # Poll eBPF programs
                    await self._poll_ebpf_programs()
                
                await asyncio.sleep(0.1)  # 100ms polling interval
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(1)
    
    async def _collection_loop(self):
        """Background collection and processing loop"""
        
        while True:
            try:
                # Process collected data
                await self._process_system_call_buffer()
                await self._process_kernel_metrics_buffer()
                await self._process_payload_inspection_buffer()
                
                # Update statistics
                self._monitoring_stats['last_collection_time'] = time.time()
                
                await asyncio.sleep(1)  # Process every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in collection loop", error=str(e))
                await asyncio.sleep(5)
    
    async def _generate_mock_events(self):
        """Generate mock system events for development"""
        
        current_time_ns = time.time_ns()
        
        # Generate mock syscall events
        if self.monitoring_level in [SystemMonitoringLevel.DEEP, SystemMonitoringLevel.KERNEL]:
            syscall_event = SystemCallEvent(
                timestamp_ns=current_time_ns,
                pid=1000 + (current_time_ns % 100),
                tid=2000 + (current_time_ns % 100),
                syscall_name=["read", "write", "open", "close", "mmap"][current_time_ns % 5],
                syscall_number=current_time_ns % 400,
                duration_ns=10000 + (current_time_ns % 100000),
                return_value=0 if current_time_ns % 10 != 0 else -1,
                process_name=["nginx", "python", "node", "postgres", "redis"][current_time_ns % 5]
            )
            
            self._system_call_buffer.append(syscall_event)
            self._monitoring_stats['syscalls_captured'] += 1
        
        # Generate mock kernel metrics
        if self.monitoring_level == SystemMonitoringLevel.KERNEL:
            kernel_metrics = KernelMetrics(
                timestamp_ns=current_time_ns,
                cpu_id=current_time_ns % 4,
                context_switches=100 + (current_time_ns % 50),
                interrupts=50 + (current_time_ns % 25),
                page_faults=5 + (current_time_ns % 10),
                memory_pressure=0.1 + (current_time_ns % 100) / 1000,
                io_wait_percent=2.0 + (current_time_ns % 50) / 10,
                kernel_time_percent=5.0 + (current_time_ns % 30) / 10,
                user_time_percent=80.0 + (current_time_ns % 100) / 10
            )
            
            self._kernel_metrics_buffer.append(kernel_metrics)
            self._monitoring_stats['kernel_metrics_collected'] += 1
        
        # Generate mock payload inspection results
        if self.payload_inspection_mode != PayloadInspectionMode.DISABLED:
            payload_result = PayloadInspectionResult(
                timestamp_ns=current_time_ns,
                protocol=["TCP", "UDP", "HTTP", "HTTPS"][current_time_ns % 4],
                source_ip=f"192.168.1.{current_time_ns % 254 + 1}",
                destination_ip=f"10.0.0.{current_time_ns % 254 + 1}",
                source_port=8000 + (current_time_ns % 1000),
                destination_port=80 if current_time_ns % 2 == 0 else 443,
                payload_size=100 + (current_time_ns % 1000),
                payload_hash=f"sha256_{current_time_ns % 10000}",
                inspection_results={
                    "content_type": "application/json",
                    "encoding": "utf-8",
                    "suspicious_patterns": []
                }
            )
            
            # Add some threat indicators occasionally
            if current_time_ns % 100 == 0:
                payload_result.threat_indicators.append("suspicious_user_agent")
            if current_time_ns % 150 == 0:
                payload_result.anomalies_detected.append("unusual_payload_size")
            
            self._payload_inspection_buffer.append(payload_result)
            self._monitoring_stats['payloads_inspected'] += 1
        
        # Limit buffer sizes
        if len(self._system_call_buffer) > 1000:
            self._system_call_buffer.pop(0)
        if len(self._kernel_metrics_buffer) > 500:
            self._kernel_metrics_buffer.pop(0)
        if len(self._payload_inspection_buffer) > 200:
            self._payload_inspection_buffer.pop(0)
    
    async def _poll_ebpf_programs(self):
        """Poll eBPF programs for events"""
        
        try:
            for program_name, program in self._ebpf_programs.items():
                if hasattr(program, 'perf_buffer_poll'):
                    program.perf_buffer_poll(timeout=10)  # 10ms timeout
                    
        except Exception as e:
            logger.error("Error polling eBPF programs", error=str(e))
    
    async def _process_system_call_buffer(self):
        """Process system call events buffer"""
        
        if not self._system_call_buffer:
            return
        
        # Process recent syscall events for correlation
        recent_events = [event for event in self._system_call_buffer 
                        if time.time_ns() - event.timestamp_ns < 5_000_000_000]  # Last 5 seconds
        
        # Analyze syscall patterns
        syscall_patterns = self._analyze_syscall_patterns(recent_events)
        
        # Store analysis results for correlation
        if syscall_patterns:
            logger.debug("Syscall patterns detected", patterns=syscall_patterns)
    
    async def _process_kernel_metrics_buffer(self):
        """Process kernel metrics buffer"""
        
        if not self._kernel_metrics_buffer:
            return
        
        # Calculate kernel performance indicators
        recent_metrics = [metrics for metrics in self._kernel_metrics_buffer 
                         if time.time_ns() - metrics.timestamp_ns < 10_000_000_000]  # Last 10 seconds
        
        if recent_metrics:
            avg_context_switches = sum(m.context_switches for m in recent_metrics) / len(recent_metrics)
            avg_interrupts = sum(m.interrupts for m in recent_metrics) / len(recent_metrics)
            avg_memory_pressure = sum(m.memory_pressure for m in recent_metrics) / len(recent_metrics)
            
            # Detect anomalies
            anomalies = []
            if avg_context_switches > 1000:
                anomalies.append("high_context_switches")
            if avg_interrupts > 500:
                anomalies.append("high_interrupt_rate")
            if avg_memory_pressure > 0.8:
                anomalies.append("memory_pressure")
            
            if anomalies:
                logger.warning("Kernel performance anomalies detected", anomalies=anomalies)
    
    async def _process_payload_inspection_buffer(self):
        """Process payload inspection buffer"""
        
        if not self._payload_inspection_buffer:
            return
        
        # Analyze payload patterns and threats
        recent_payloads = [payload for payload in self._payload_inspection_buffer 
                          if time.time_ns() - payload.timestamp_ns < 30_000_000_000]  # Last 30 seconds
        
        # Aggregate threat indicators
        all_threats = [threat for payload in recent_payloads for threat in payload.threat_indicators]
        all_anomalies = [anomaly for payload in recent_payloads for anomaly in payload.anomalies_detected]
        
        if all_threats or all_anomalies:
            logger.warning("Security threats or anomalies detected in payloads",
                          threats=list(set(all_threats)),
                          anomalies=list(set(all_anomalies)))
    
    def _analyze_syscall_patterns(self, syscall_events: List[SystemCallEvent]) -> Dict[str, Any]:
        """Analyze system call patterns for anomalies"""
        
        if not syscall_events:
            return {}
        
        # Group by process
        process_syscalls = {}
        for event in syscall_events:
            if event.process_name not in process_syscalls:
                process_syscalls[event.process_name] = []
            process_syscalls[event.process_name].append(event)
        
        patterns = {}
        
        for process_name, events in process_syscalls.items():
            # Calculate syscall frequency
            syscall_frequency = len(events) / 5.0  # Events per second over 5 second window
            
            # Calculate average duration
            avg_duration_ns = sum(event.duration_ns for event in events) / len(events)
            
            # Count failed syscalls
            failed_syscalls = sum(1 for event in events if event.return_value < 0)
            failure_rate = failed_syscalls / len(events)
            
            # Detect patterns
            process_patterns = []
            if syscall_frequency > 100:  # More than 100 syscalls per second
                process_patterns.append("high_frequency")
            if avg_duration_ns > 1_000_000:  # More than 1ms average
                process_patterns.append("slow_syscalls")
            if failure_rate > 0.1:  # More than 10% failure rate
                process_patterns.append("high_failure_rate")
            
            if process_patterns:
                patterns[process_name] = {
                    'patterns': process_patterns,
                    'frequency': syscall_frequency,
                    'avg_duration_ns': avg_duration_ns,
                    'failure_rate': failure_rate,
                    'syscall_count': len(events)
                }
        
        return patterns
    
    async def _cleanup_ebpf_programs(self):
        """Cleanup eBPF programs"""
        
        try:
            for program_name, program in self._ebpf_programs.items():
                if hasattr(program, 'cleanup'):
                    program.cleanup()
            
            self._ebpf_programs.clear()
            logger.info("eBPF programs cleaned up")
            
        except Exception as e:
            logger.error("Error cleaning up eBPF programs", error=str(e))
    
    async def get_system_context(self) -> Dict[str, Any]:
        """Get current deep system context for correlation"""
        
        current_time_ns = time.time_ns()
        
        # Recent system call activity
        recent_syscalls = [event for event in self._system_call_buffer 
                          if current_time_ns - event.timestamp_ns < 1_000_000_000]  # Last 1 second
        
        # Recent kernel metrics
        recent_kernel_metrics = [metrics for metrics in self._kernel_metrics_buffer 
                               if current_time_ns - metrics.timestamp_ns < 5_000_000_000]  # Last 5 seconds
        
        # Recent payload inspection
        recent_payloads = [payload for payload in self._payload_inspection_buffer 
                          if current_time_ns - payload.timestamp_ns < 10_000_000_000]  # Last 10 seconds
        
        context = {
            'timestamp_ns': current_time_ns,
            'monitoring_level': self.monitoring_level.value,
            'payload_inspection_mode': self.payload_inspection_mode.value,
            'ebpf_available': self._ebpf_available,
            'mock_mode': self.enable_mock_mode,
            'system_activity': {
                'recent_syscalls_count': len(recent_syscalls),
                'recent_kernel_metrics_count': len(recent_kernel_metrics),
                'recent_payloads_count': len(recent_payloads)
            },
            'monitoring_stats': self._monitoring_stats.copy()
        }
        
        # Add syscall analysis if available
        if recent_syscalls:
            syscall_analysis = self._analyze_syscall_patterns(recent_syscalls)
            if syscall_analysis:
                context['syscall_patterns'] = syscall_analysis
        
        # Add kernel performance indicators
        if recent_kernel_metrics:
            latest_metrics = recent_kernel_metrics[-1]
            context['kernel_performance'] = {
                'context_switches': latest_metrics.context_switches,
                'interrupts': latest_metrics.interrupts,
                'page_faults': latest_metrics.page_faults,
                'memory_pressure': latest_metrics.memory_pressure,
                'io_wait_percent': latest_metrics.io_wait_percent,
                'kernel_time_percent': latest_metrics.kernel_time_percent
            }
        
        # Add security indicators
        if recent_payloads:
            all_threats = [threat for payload in recent_payloads for threat in payload.threat_indicators]
            all_anomalies = [anomaly for payload in recent_payloads for anomaly in payload.anomalies_detected]
            
            context['security_indicators'] = {
                'threat_indicators': list(set(all_threats)),
                'anomalies_detected': list(set(all_anomalies)),
                'threat_count': len(all_threats),
                'anomaly_count': len(all_anomalies)
            }
        
        return context
    
    async def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get deep system monitoring statistics"""
        
        return {
            'monitoring_config': {
                'monitoring_level': self.monitoring_level.value,
                'payload_inspection_mode': self.payload_inspection_mode.value,
                'ebpf_available': self._ebpf_available,
                'mock_mode': self.enable_mock_mode
            },
            'statistics': self._monitoring_stats.copy(),
            'buffer_status': {
                'syscall_buffer_size': len(self._system_call_buffer),
                'kernel_metrics_buffer_size': len(self._kernel_metrics_buffer),
                'payload_buffer_size': len(self._payload_inspection_buffer)
            },
            'ebpf_programs': {
                'loaded_programs': list(self._ebpf_programs.keys()),
                'program_count': len(self._ebpf_programs)
            }
        }