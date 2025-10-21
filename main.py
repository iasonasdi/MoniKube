#!/usr/bin/env python3
"""
Kubernetes Cluster Monitor - Main Entry Point
Supports continuous monitoring with customizable timing and iterations.
"""

import argparse
import time
import signal
import sys
from datetime import datetime
from kubernetes_monitor import KubernetesMonitor


class MonitoringController:
    """Controller class to handle monitoring with timing and iteration control"""
    
    def __init__(self):
        self.monitor = KubernetesMonitor()
        self.running = True
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals for graceful shutdown"""
        print(f"\n\nReceived signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def run_monitoring_cycle(self, cycle_num=None):
        """Run a single monitoring cycle"""
        try:
            print(f"\n{'='*60}")
            if cycle_num:
                print(f"MONITORING CYCLE #{cycle_num} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"CONTINUOUS MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Print cluster summary
            self.monitor.print_summary()
            
            # Get and display additional details
            nodes = self.monitor.get_nodes()
            pods = self.monitor.get_pods()
            services = self.monitor.get_services()
            
            print(f"\n📊 DETAILED STATUS:")
            print(f"   Nodes: {len(nodes)} total")
            print(f"   Pods: {len(pods)} total")
            print(f"   Services: {len(services)} total")
            
            # Show node details
            if nodes:
                print(f"\n🖥️  NODES:")
                for node in nodes:
                    status_icon = "✅" if node.status == "Ready" else "❌"
                    print(f"   {status_icon} {node.name} ({node.status}) - Roles: {', '.join(node.roles) if node.roles else 'worker'}")
            
            # Show pod status summary
            pod_statuses = {}
            for pod in pods:
                status = pod.status
                pod_statuses[status] = pod_statuses.get(status, 0) + 1
            
            if pod_statuses:
                print(f"\n🚀 PODS BY STATUS:")
                for status, count in pod_statuses.items():
                    icon = "🟢" if status == "Running" else "🟡" if status == "Pending" else "🔴"
                    print(f"   {icon} {status}: {count}")
            
            # Show service types
            service_types = {}
            for service in services:
                svc_type = service.type
                service_types[svc_type] = service_types.get(svc_type, 0) + 1
            
            if service_types:
                print(f"\n🌐 SERVICES BY TYPE:")
                for svc_type, count in service_types.items():
                    print(f"   📡 {svc_type}: {count}")
            
            print(f"\n{'='*60}")
            
        except Exception as e:
            print(f"❌ Error during monitoring cycle: {e}")
            self.monitor.logger.error(f"Monitoring cycle error: {e}")
    
    def run_continuous(self, interval_seconds=10):
        """Run monitoring continuously until stopped"""
        print(f"🔄 Starting continuous monitoring (every {interval_seconds}s)")
        print("Press Ctrl+C to stop...")
        
        cycle_count = 0
        while self.running:
            cycle_count += 1
            self.run_monitoring_cycle(cycle_count)
            
            if self.running:
                print(f"⏳ Waiting {interval_seconds} seconds until next cycle...")
                time.sleep(interval_seconds)
        
        print("🛑 Monitoring stopped.")
    
    def run_limited(self, interval_seconds=10, max_iterations=10):
        """Run monitoring for a limited number of iterations"""
        if max_iterations == 0:
            self.run_continuous(interval_seconds)
            return
        
        print(f"🔄 Starting limited monitoring ({max_iterations} iterations, every {interval_seconds}s)")
        
        for i in range(1, max_iterations + 1):
            if not self.running:
                break
                
            self.run_monitoring_cycle(i)
            
            if i < max_iterations and self.running:
                print(f"⏳ Waiting {interval_seconds} seconds until next cycle...")
                time.sleep(interval_seconds)
        
        print(f"✅ Completed {max_iterations} monitoring cycles.")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Kubernetes Cluster Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run continuously (default: every 10s)
  python main.py -t 5               # Run continuously every 5 seconds
  python main.py -t 30 -n 5        # Run 5 times, every 30 seconds
  python main.py -n 0               # Run continuously (same as no args)
  python main.py -t 60 -n 1        # Run once, wait 60 seconds (single report)
        """
    )
    
    parser.add_argument(
        '-t', '--time',
        type=int,
        default=10,
        help='Time interval between monitoring cycles in seconds (default: 10)'
    )
    
    parser.add_argument(
        '-n', '--iterations',
        type=int,
        default=0,
        help='Number of monitoring cycles to run (0 = continuous, default: 0)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point with command line argument support"""
    args = parse_arguments()
    
    print("🚀 Kubernetes Cluster Monitor")
    print("=" * 50)
    
    # Validate arguments
    if args.time < 1:
        print("❌ Error: Time interval must be at least 1 second")
        sys.exit(1)
    
    if args.iterations < 0:
        print("❌ Error: Number of iterations cannot be negative")
        sys.exit(1)
    
    # Initialize controller
    controller = MonitoringController()
    
    # Check if kubectl is available
    contexts = controller.monitor.get_available_contexts()
    if not contexts:
        print("❌ No Kubernetes contexts found. Make sure kubectl is installed and configured.")
        print("   Run: kubectl config get-contexts")
        sys.exit(1)
    
    print(f"✅ Found {len(contexts)} Kubernetes context(s): {', '.join(contexts)}")
    
    try:
        if args.iterations == 0:
            # Continuous monitoring
            controller.run_continuous(args.time)
        else:
            # Limited iterations
            controller.run_limited(args.time, args.iterations)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring interrupted by user.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()