# mass_image_generator/auto_scaler.py
"""
অটো স্কেলার - ডাইনামিকভাবে রিসোর্স ম্যানেজ করে
"""

import os
import sys
import time
import psutil
import threading
import concurrent.futures
from typing import Dict, List, Optional
from datetime import datetime

class ResourceMonitor:
    """রিসোর্স মনিটর ক্লাস"""
    
    def __init__(self):
        self.cpu_threshold = 80  # 80% CPU usage
        self.memory_threshold = 80  # 80% memory usage
        self.network_threshold = 1000000  # 1MB/s
        
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'network_io': [],
            'disk_io': []
        }
        
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval=5):
        """মনিটরিং শুরু করুন"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def _monitor_loop(self, interval):
        """মনিটরিং লুপ"""
        while self.monitoring:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['cpu_usage'].append(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].append(memory.percent)
            
            # Network I/O
            net_io = psutil.net_io_counters()
            self.metrics['network_io'].append({
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            })
            
            # Keep only last 100 readings
            for key in self.metrics:
                if len(self.metrics[key]) > 100:
                    self.metrics[key] = self.metrics[key][-100:]
            
            time.sleep(interval)
    
    def get_current_metrics(self):
        """কারেন্ট মেট্রিক্স পান"""
        return {
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'timestamp': datetime.now().isoformat()
        }
    
    def is_overloaded(self):
        """ওভারলোডেড কি না চেক করুন"""
        metrics = self.get_current_metrics()
        
        if (metrics['cpu'] > self.cpu_threshold or 
            metrics['memory'] > self.memory_threshold):
            return True
        
        return False
    
    def get_optimal_thread_count(self, base_threads=4):
        """অপটিমাল থ্রেড কাউন্ট পান"""
        metrics = self.get_current_metrics()
        
        # CPU based scaling
        cpu_available = 100 - metrics['cpu']
        cpu_scale = max(1, int(base_threads * (cpu_available / 100)))
        
        # Memory based scaling
        mem_available = 100 - metrics['memory']
        mem_scale = max(1, int(base_threads * (mem_available / 100)))
        
        # Take minimum of both
        optimal_threads = min(cpu_scale, mem_scale, base_threads * 2)
        
        return max(1, optimal_threads)  # At least 1 thread
    
    def stop_monitoring(self):
        """মনিটরিং বন্ধ করুন"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

class AutoScaler:
    """অটো স্কেলার ক্লাস"""
    
    def __init__(self, base_workers=4):
        self.resource_monitor = ResourceMonitor()
        self.base_workers = base_workers
        self.current_workers = base_workers
        self.scaling_enabled = True
        self.scaling_history = []
        
        # Start monitoring
        self.resource_monitor.start_monitoring()
    
    def adjust_workers(self, current_queue_size=0):
        """ওয়ার্কার্স অ্যাডজাস্ট করুন"""
        if not self.scaling_enabled:
            return self.current_workers
        
        # Get optimal thread count
        optimal_threads = self.resource_monitor.get_optimal_thread_count(self.base_workers)
        
        # Adjust based on queue size
        if current_queue_size > 100:
            # Large queue, increase workers
            optimal_threads = min(optimal_threads * 2, self.base_workers * 4)
        elif current_queue_size < 10:
            # Small queue, decrease workers
            optimal_threads = max(1, optimal_threads // 2)
        
        # Check if system is overloaded
        if self.resource_monitor.is_overloaded():
            # Reduce workers if overloaded
            optimal_threads = max(1, optimal_threads // 2)
        
        # Update current workers
        old_workers = self.current_workers
        self.current_workers = optimal_threads
        
        # Record scaling event
        if old_workers != optimal_threads:
            self.record_scaling_event(old_workers, optimal_threads)
            print(f"Auto-scaling: {old_workers} -> {optimal_threads} workers")
        
        return optimal_threads
    
    def record_scaling_event(self, old_count, new_count):
        """স্কেলিং ইভেন্ট রেকর্ড করুন"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'old_workers': old_count,
            'new_workers': new_count,
            'metrics': self.resource_monitor.get_current_metrics()
        }
        
        self.scaling_history.append(event)
        
        # Keep only last 50 events
        if len(self.scaling_history) > 50:
            self.scaling_history = self.scaling_history[-50:]
    
    def get_scaling_stats(self):
        """স্কেলিং স্ট্যাটস পান"""
        if not self.scaling_history:
            return {}
        
        total_scales = len(self.scaling_history)
        avg_workers = sum(event['new_workers'] for event in self.scaling_history) / total_scales
        
        return {
            'total_scaling_events': total_scales,
            'average_workers': avg_workers,
            'current_workers': self.current_workers,
            'last_scaling': self.scaling_history[-1] if self.scaling_history else None
        }
    
    def generate_report(self):
        """রিপোর্ট জেনারেট করুন"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'scaling_enabled': self.scaling_enabled,
            'base_workers': self.base_workers,
            'current_workers': self.current_workers,
            'resource_metrics': self.resource_monitor.get_current_metrics(),
            'scaling_stats': self.get_scaling_stats(),
            'scaling_history_count': len(self.scaling_history)
        }
        
        return report
    
    def stop(self):
        """স্টপ করুন"""
        self.resource_monitor.stop_monitoring()
        self.scaling_enabled = False

class SmartThreadPool:
    """স্মার্ট থ্রেড পুল ক্লাস"""
    
    def __init__(self, auto_scaler=None):
        self.auto_scaler = auto_scaler or AutoScaler()
        self.executor = None
        self.tasks = []
        self.results = []
        self.running = False
        
    def submit_task(self, func, *args, **kwargs):
        """টাস্ক সাবমিট করুন"""
        if not self.executor or self.executor._shutdown:
            # Create new executor with current worker count
            worker_count = self.auto_scaler.current_workers
            self.executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=worker_count,
                thread_name_prefix='SmartWorker'
            )
        
        # Adjust workers based on queue size
        pending_tasks = len([t for t in self.tasks if not t.done()])
        self.auto_scaler.adjust_workers(pending_tasks)
        
        # Submit task
        future = self.executor.submit(func, *args, **kwargs)
        self.tasks.append(future)
        
        return future
    
    def submit_batch(self, tasks):
        """ব্যাচ টাস্ক সাবমিট করুন"""
        futures = []
        
        for task in tasks:
            if callable(task['func']):
                future = self.submit_task(
                    task['func'],
                    *task.get('args', []),
                    **task.get('kwargs', {})
                )
                futures.append(future)
        
        return futures
    
    def wait_completion(self, timeout=None):
        """কমপ্লিশনের জন্য অপেক্ষা করুন"""
        if not self.tasks:
            return []
        
        # Wait for completion
        done, not_done = concurrent.futures.wait(
            self.tasks,
            timeout=timeout,
            return_when=concurrent.futures.ALL_COMPLETED
        )
        
        # Collect results
        self.results = []
        for future in done:
            try:
                result = future.result(timeout=1)
                self.results.append({
                    'success': True,
                    'result': result
                })
            except Exception as e:
                self.results.append({
                    'success': False,
                    'error': str(e)
                })
        
        return self.results
    
    def get_stats(self):
        """স্ট্যাটস পান"""
        if not self.executor:
            return {}
        
        pending = len([t for t in self.tasks if not t.done()])
        completed = len([t for t in self.tasks if t.done()])
        
        return {
            'total_tasks': len(self.tasks),
            'pending_tasks': pending,
            'completed_tasks': completed,
            'worker_count': self.auto_scaler.current_workers,
            'executor_active': not self.executor._shutdown
        }
    
    def shutdown(self):
        """শাটডাউন করুন"""
        if self.executor:
            self.executor.shutdown(wait=True)
        self.auto_scaler.stop()

# Usage example
if __name__ == "__main__":
    # Test auto-scaling
    scaler = AutoScaler(base_workers=4)
    
    print("Testing auto-scaling...")
    print("Press Ctrl+C to stop")
    
    try:
        for i in range(20):
            workers = scaler.adjust_workers(current_queue_size=i*10)
            metrics = scaler.resource_monitor.get_current_metrics()
            
            print(f"Iteration {i}: {workers} workers | "
                  f"CPU: {metrics['cpu']}% | "
                  f"Memory: {metrics['memory']}%")
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\nStopping...")
    
    finally:
        # Generate report
        report = scaler.generate_report()
        print("\nFinal Report:")
        print(json.dumps(report, indent=2))
        
        scaler.stop()