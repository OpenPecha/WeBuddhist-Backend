#!/usr/bin/env python3
"""
Memory monitoring script for WeBuddhist Backend
Usage: python monitor_memory.py
"""

import psutil
import time
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_monitor.log'),
        logging.StreamHandler()
    ]
)

def get_memory_stats():
    """Get current memory statistics"""
    memory = psutil.virtual_memory()
    return {
        'total': memory.total,
        'available': memory.available, 
        'percent': memory.percent,
        'used': memory.used,
        'free': memory.free
    }

def get_process_stats(process_name="uvicorn"):
    """Get memory stats for specific process"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            if process_name in proc.info['name']:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                    'cpu_percent': proc.info['cpu_percent']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def test_api_endpoint():
    """Test the problematic API endpoint"""
    try:
        response = requests.get(
            'http://localhost:8000/api/v1/health',
            timeout=5
        )
        return response.status_code == 204
    except Exception as e:
        logging.error(f"API test failed: {e}")
        return False

def monitor_memory_usage(interval=30, duration=600):
    """Monitor memory usage for specified duration"""
    start_time = time.time()
    
    logging.info(f"Starting memory monitoring for {duration} seconds")
    
    while time.time() - start_time < duration:
        # Get system memory stats
        mem_stats = get_memory_stats()
        
        # Get process stats
        uvicorn_processes = get_process_stats("uvicorn")
        python_processes = get_process_stats("python")
        
        # Test API
        api_healthy = test_api_endpoint()
        
        # Log current stats
        logging.info(f"System Memory: {mem_stats['percent']:.1f}% used "
                    f"({mem_stats['used']/1024/1024/1024:.1f}GB / "
                    f"{mem_stats['total']/1024/1024/1024:.1f}GB)")
        
        if uvicorn_processes:
            for proc in uvicorn_processes:
                logging.info(f"Uvicorn PID {proc['pid']}: {proc['memory_mb']:.1f}MB RAM, "
                           f"{proc['cpu_percent']:.1f}% CPU")
        
        if not api_healthy:
            logging.warning("API health check failed!")
        
        # Alert if memory usage is high
        if mem_stats['percent'] > 80:
            logging.warning(f"HIGH MEMORY USAGE: {mem_stats['percent']:.1f}%")
        
        if uvicorn_processes:
            max_proc_memory = max(p['memory_mb'] for p in uvicorn_processes)
            if max_proc_memory > 500:  # Alert if any process uses more than 500MB
                logging.warning(f"HIGH PROCESS MEMORY: {max_proc_memory:.1f}MB")
        
        time.sleep(interval)

def analyze_memory_patterns():
    """Analyze memory usage patterns from logs"""
    try:
        with open('memory_monitor.log', 'r') as f:
            lines = f.readlines()
        
        memory_values = []
        for line in lines:
            if 'System Memory:' in line:
                try:
                    # Extract percentage from log line
                    percent_str = line.split('System Memory: ')[1].split('%')[0]
                    memory_values.append(float(percent_str))
                except:
                    continue
        
        if memory_values:
            avg_memory = sum(memory_values) / len(memory_values)
            max_memory = max(memory_values)
            min_memory = min(memory_values)
            
            logging.info(f"MEMORY ANALYSIS:")
            logging.info(f"Average: {avg_memory:.1f}%")
            logging.info(f"Peak: {max_memory:.1f}%") 
            logging.info(f"Minimum: {min_memory:.1f}%")
            logging.info(f"Samples: {len(memory_values)}")
            
            return {
                'average': avg_memory,
                'peak': max_memory,
                'minimum': min_memory,
                'samples': len(memory_values)
            }
    except FileNotFoundError:
        logging.error("No memory monitor log file found")
    return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        analyze_memory_patterns()
    else:
        # Default: monitor for 10 minutes
        monitor_memory_usage(interval=30, duration=600)
        
        # Analyze results
        analyze_memory_patterns()