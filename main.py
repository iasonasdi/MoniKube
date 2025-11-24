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
from DataCollection.kubernetes_monitor import KubernetesMonitor
from DataCollection.service_spy import DockerServiceSpy
from Neo4J.neo4j_handler import Neo4JHandler


class MonitoringController:
    """Controller class to handle monitoring with timing and iteration control"""
    
    def __init__(self, neo4j_config=None, enable_docker=True):
        self.monitor = KubernetesMonitor()
        self.docker_spy = DockerServiceSpy() if enable_docker else None
        self.running = True
        self.neo4j_handler = None
        self.neo4j_config = neo4j_config
        self.enable_docker = enable_docker
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize Neo4J if configured
        if neo4j_config:
            self._initialize_neo4j()
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals for graceful shutdown"""
        print(f"\n\nReceived signal {signum}. Shutting down gracefully...")
        self.running = False
        if self.neo4j_handler:
            self.neo4j_handler.disconnect()
    
    def _initialize_neo4j(self):
        """Initialize Neo4J connection"""
        try:
            self.neo4j_handler = Neo4JHandler(
                uri=self.neo4j_config['uri'],
                username=self.neo4j_config['username'],
                password=self.neo4j_config['password'],
                database=self.neo4j_config.get('database', 'neo4j')
            )
            
            if self.neo4j_handler.connect():
                self.neo4j_handler.create_schema()
                print("✅ Neo4J connection established and schema created")
            else:
                print("❌ Failed to connect to Neo4J database")
                self.neo4j_handler = None
                
        except Exception as e:
            print(f"❌ Neo4J initialization failed: {e}")
            self.neo4j_handler = None
    
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
            
            # Monitor Docker containers if enabled
            docker_data = None
            if self.enable_docker and self.docker_spy:
                try:
                    print(f"\n🐳 DOCKER CONTAINER MONITORING:")
                    print(f"{'='*60}")
                    docker_data = self.docker_spy.spy_on_containers()
                    if docker_data:
                        self.docker_spy.print_summary()
                    else:
                        print("   No Docker containers found or accessible")
                except Exception as e:
                    print(f"⚠️  Docker monitoring error: {e}")
            
            # Store data in Neo4J if configured
            if self.neo4j_handler:
                try:
                    # Get current context
                    contexts = self.monitor.get_available_contexts()
                    current_context = contexts[0] if contexts else "default"
                    
                    # Store Kubernetes monitoring data
                    if self.neo4j_handler.store_monitoring_data(self.monitor, current_context):
                        print("💾 Kubernetes data stored in Neo4J database")
                    else:
                        print("⚠️  Failed to store Kubernetes data in Neo4J")
                    
                    # Store Docker monitoring data
                    if docker_data and self.docker_spy:
                        if self.neo4j_handler.store_docker_data(self.docker_spy):
                            print("💾 Docker data stored in Neo4J database")
                        else:
                            print("⚠️  Failed to store Docker data in Neo4J")
                        
                except Exception as e:
                    print(f"⚠️  Neo4J storage error: {e}")
            
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
  
  # With Neo4J database storage:
  python main.py -db                # Store data in Neo4J (default settings)
  python main.py -db -t 30          # Store data every 30 seconds
  python main.py -db --neo4j-uri bolt://neo4j-server:7687 --neo4j-username admin --neo4j-password secret
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
    
    # Neo4J database options
    parser.add_argument(
        '-db', '--database',
        action='store_true',
        help='Enable Neo4J database storage'
    )
    
    parser.add_argument(
        '--neo4j-uri',
        default='bolt://localhost:7687',
        help='Neo4J database URI (default: bolt://localhost:7687)'
    )
    
    parser.add_argument(
        '--neo4j-username',
        default='neo4j',
        help='Neo4J username (default: neo4j)'
    )
    
    parser.add_argument(
        '--neo4j-password',
        default='password',
        help='Neo4J password (default: password)'
    )
    
    parser.add_argument(
        '--neo4j-database',
        default='neo4j',
        help='Neo4J database name (default: neo4j)'
    )
    
    parser.add_argument(
        '--no-docker',
        action='store_true',
        help='Disable Docker container monitoring'
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
    
    # Prepare Neo4J configuration if database option is enabled
    neo4j_config = None
    if args.database:
        neo4j_config = {
            'uri': args.neo4j_uri,
            'username': args.neo4j_username,
            'password': args.neo4j_password,
            'database': args.neo4j_database
        }
        print("🗄️  Neo4J database storage enabled")
        print(f"   URI: {neo4j_config['uri']}")
        print(f"   Database: {neo4j_config['database']}")
    
    # Initialize controller
    enable_docker = not args.no_docker
    controller = MonitoringController(neo4j_config, enable_docker=enable_docker)
    
    if enable_docker:
        print("🐳 Docker container monitoring enabled")
    else:
        print("🐳 Docker container monitoring disabled")
    
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