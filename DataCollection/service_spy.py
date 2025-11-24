#!/usr/bin/env python3
"""
Docker Container Service Spy
Monitors Docker containers, collects process information, resource usage,
and network connections for security analysis.
"""

import subprocess
import json
import logging
import re
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import ipaddress


@dataclass
class ProcessInfo:
    """Process information structure"""
    pid: str
    user: str
    cpu_percent: float
    memory_percent: float
    memory_kb: int
    command: str
    start_time: Optional[str] = None


@dataclass
class NetworkConnection:
    """Network connection information"""
    protocol: str
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    state: str
    process_name: Optional[str] = None
    pid: Optional[str] = None


@dataclass
class ContainerSecurityInfo:
    """Security-related information for a container"""
    container_id: str
    container_name: str
    image: str
    status: str
    processes: List[ProcessInfo]
    network_connections: List[NetworkConnection]
    external_ips: Set[str]
    open_ports: List[Dict[str, Any]]
    users: Set[str]
    timestamp: str


class DockerServiceSpy:
    """Service spy for Docker containers"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.containers_data: List[ContainerSecurityInfo] = []
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('DockerServiceSpy')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def get_running_containers(self) -> List[Dict[str, str]]:
        """Get list of all running Docker containers"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', 'json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        container = json.loads(line)
                        containers.append({
                            'id': container.get('ID', ''),
                            'name': container.get('Names', ''),
                            'image': container.get('Image', ''),
                            'status': container.get('Status', '')
                        })
                    except json.JSONDecodeError:
                        continue
            
            self.logger.info(f"Found {len(containers)} running containers")
            return containers
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error getting containers: {e.stderr}")
            return []
        except FileNotFoundError:
            self.logger.error("Docker command not found. Make sure Docker is installed.")
            return []
    
    def exec_in_container(self, container_id: str, command: List[str], 
                         timeout: int = 10) -> Optional[str]:
        """Execute a command inside a Docker container"""
        try:
            result = subprocess.run(
                ['docker', 'exec', container_id] + command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                self.logger.warning(
                    f"Command failed in container {container_id}: {result.stderr[:100]}"
                )
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Command timeout in container {container_id}")
            return None
        except Exception as e:
            self.logger.error(f"Error executing command in container {container_id}: {e}")
            return None
    
    def get_processes(self, container_id: str) -> List[ProcessInfo]:
        """Get top processes running in a container"""
        processes = []
        
        # Try using 'ps aux' first (more common)
        ps_output = self.exec_in_container(
            container_id, 
            ['ps', 'aux', '--no-headers']
        )
        
        if not ps_output:
            # Fallback to 'top' command
            top_output = self.exec_in_container(
                container_id,
                ['sh', '-c', 'timeout 2 top -b -n 1 || true']
            )
            if top_output:
                return self._parse_top_output(top_output)
            return processes
        
        # Parse ps aux output
        for line in ps_output.strip().split('\n'):
            if not line.strip():
                continue
            
            parts = line.split()
            if len(parts) >= 11:
                try:
                    process = ProcessInfo(
                        pid=parts[1],
                        user=parts[0],
                        cpu_percent=float(parts[2]) if parts[2].replace('.', '').isdigit() else 0.0,
                        memory_percent=float(parts[3]) if parts[3].replace('.', '').isdigit() else 0.0,
                        memory_kb=int(float(parts[5]) * 1024) if parts[5].replace('.', '').isdigit() else 0,
                        command=' '.join(parts[10:])[:200],  # Limit command length
                        start_time=parts[8] if len(parts) > 8 else None
                    )
                    processes.append(process)
                except (ValueError, IndexError) as e:
                    self.logger.debug(f"Error parsing process line: {line[:50]} - {e}")
                    continue
        
        # Sort by CPU usage (descending) and return top 20
        processes.sort(key=lambda x: x.cpu_percent, reverse=True)
        return processes[:20]
    
    def _parse_top_output(self, top_output: str) -> List[ProcessInfo]:
        """Parse top command output (fallback method)"""
        processes = []
        lines = top_output.split('\n')
        in_process_list = False
        
        for line in lines:
            if 'PID' in line and 'CPU' in line and 'MEM' in line:
                in_process_list = True
                continue
            
            if in_process_list and line.strip():
                parts = line.split()
                if len(parts) >= 12 and parts[0].isdigit():
                    try:
                        process = ProcessInfo(
                            pid=parts[0],
                            user=parts[1],
                            cpu_percent=float(parts[8]) if parts[8].replace('.', '').isdigit() else 0.0,
                            memory_percent=float(parts[9]) if parts[9].replace('.', '').isdigit() else 0.0,
                            memory_kb=int(float(parts[5])) if parts[5].replace('.', '').isdigit() else 0,
                            command=' '.join(parts[11:])[:200],
                            start_time=parts[10] if len(parts) > 10 else None
                        )
                        processes.append(process)
                    except (ValueError, IndexError):
                        continue
        
        processes.sort(key=lambda x: x.cpu_percent, reverse=True)
        return processes[:20]
    
    def get_network_connections(self, container_id: str) -> List[NetworkConnection]:
        """Get network connections from a container"""
        connections = []
        
        # Try 'ss' first (modern replacement for netstat)
        ss_output = self.exec_in_container(
            container_id,
            ['ss', '-tunap']
        )
        
        if ss_output:
            connections.extend(self._parse_ss_output(ss_output))
        
        # Also try netstat as fallback
        netstat_output = self.exec_in_container(
            container_id,
            ['netstat', '-tunap']
        )
        
        if netstat_output:
            connections.extend(self._parse_netstat_output(netstat_output))
        
        # Remove duplicates based on (protocol, local, remote)
        seen = set()
        unique_connections = []
        for conn in connections:
            key = (conn.protocol, conn.local_address, conn.local_port, 
                   conn.remote_address, conn.remote_port)
            if key not in seen:
                seen.add(key)
                unique_connections.append(conn)
        
        return unique_connections
    
    def _parse_ss_output(self, ss_output: str) -> List[NetworkConnection]:
        """Parse ss command output"""
        connections = []
        
        for line in ss_output.strip().split('\n'):
            if not line.strip() or line.startswith('State'):
                continue
            
            # ss format: State Recv-Q Send-Q Local Address:Port Peer Address:Port
            parts = line.split()
            if len(parts) >= 5:
                try:
                    state = parts[0]
                    local = parts[4]
                    remote = parts[5] if len(parts) > 5 else ''
                    
                    # Parse local address:port
                    if ':' in local:
                        local_addr, local_port = local.rsplit(':', 1)
                        local_port = int(local_port)
                    else:
                        continue
                    
                    # Parse remote address:port
                    if ':' in remote:
                        remote_addr, remote_port = remote.rsplit(':', 1)
                        remote_port = int(remote_port)
                    else:
                        remote_addr = remote
                        remote_port = 0
                    
                    # Determine protocol from state or address format
                    protocol = 'tcp' if 'tcp' in state.lower() or 'ESTAB' in state else 'udp'
                    
                    # Extract process info if available
                    process_name = None
                    pid = None
                    if len(parts) > 6:
                        process_part = ' '.join(parts[6:])
                        # Look for pattern like "users:(("process",pid=123,fd=4))"
                        pid_match = re.search(r'pid=(\d+)', process_part)
                        if pid_match:
                            pid = pid_match.group(1)
                        proc_match = re.search(r'"([^"]+)"', process_part)
                        if proc_match:
                            process_name = proc_match.group(1)
                    
                    conn = NetworkConnection(
                        protocol=protocol,
                        local_address=local_addr,
                        local_port=local_port,
                        remote_address=remote_addr,
                        remote_port=remote_port,
                        state=state,
                        process_name=process_name,
                        pid=pid
                    )
                    connections.append(conn)
                    
                except (ValueError, IndexError) as e:
                    self.logger.debug(f"Error parsing ss line: {line[:50]} - {e}")
                    continue
        
        return connections
    
    def _parse_netstat_output(self, netstat_output: str) -> List[NetworkConnection]:
        """Parse netstat command output"""
        connections = []
        
        for line in netstat_output.strip().split('\n'):
            if not line.strip() or line.startswith('Active') or line.startswith('Proto'):
                continue
            
            parts = line.split()
            if len(parts) >= 6:
                try:
                    protocol = parts[0].lower()
                    local = parts[3]
                    remote = parts[4]
                    state = parts[5] if len(parts) > 5 else 'UNKNOWN'
                    
                    # Parse addresses
                    if ':' in local:
                        local_addr, local_port = local.rsplit(':', 1)
                        local_port = int(local_port)
                    else:
                        continue
                    
                    if ':' in remote:
                        remote_addr, remote_port = remote.rsplit(':', 1)
                        remote_port = int(remote_port)
                    else:
                        remote_addr = remote
                        remote_port = 0
                    
                    # Extract process info
                    process_name = None
                    pid = None
                    if len(parts) > 6:
                        proc_info = parts[-1]
                        # Format: process_name/pid
                        if '/' in proc_info:
                            process_name, pid = proc_info.rsplit('/', 1)
                    
                    conn = NetworkConnection(
                        protocol=protocol,
                        local_address=local_addr,
                        local_port=local_port,
                        remote_address=remote_addr,
                        remote_port=remote_port,
                        state=state,
                        process_name=process_name,
                        pid=pid
                    )
                    connections.append(conn)
                    
                except (ValueError, IndexError) as e:
                    self.logger.debug(f"Error parsing netstat line: {line[:50]} - {e}")
                    continue
        
        return connections
    
    def extract_external_ips(self, connections: List[NetworkConnection]) -> Set[str]:
        """Extract external IP addresses from network connections"""
        external_ips = set()
        
        # Private IP ranges
        private_ranges = [
            ipaddress.ip_network('10.0.0.0/8'),
            ipaddress.ip_network('172.16.0.0/12'),
            ipaddress.ip_network('192.168.0.0/16'),
            ipaddress.ip_network('127.0.0.0/8'),
        ]
        
        def is_private(ip_str: str) -> bool:
            """Check if IP is in private range"""
            if not ip_str or ip_str in ['*', '0.0.0.0', '::']:
                return True
            try:
                ip = ipaddress.ip_address(ip_str)
                if ip.is_loopback or ip.is_link_local or ip.is_multicast:
                    return True
                for private_range in private_ranges:
                    if ip in private_range:
                        return True
                return False
            except ValueError:
                # Not a valid IP, might be hostname
                return False
        
        for conn in connections:
            # Check remote address
            if conn.remote_address and not is_private(conn.remote_address):
                external_ips.add(conn.remote_address)
        
        return external_ips
    
    def get_open_ports(self, container_id: str) -> List[Dict[str, Any]]:
        """Get open ports in a container"""
        ports = []
        
        # Use ss to get listening ports
        ss_output = self.exec_in_container(
            container_id,
            ['ss', '-tuln']
        )
        
        if ss_output:
            for line in ss_output.strip().split('\n'):
                if not line.strip() or line.startswith('State'):
                    continue
                
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        protocol = parts[0].lower()
                        state = parts[1]
                        local = parts[3]
                        
                        if ':' in local:
                            addr, port = local.rsplit(':', 1)
                            ports.append({
                                'protocol': protocol,
                                'address': addr,
                                'port': int(port),
                                'state': state
                            })
                    except (ValueError, IndexError):
                        continue
        
        return ports
    
    def get_users(self, container_id: str) -> Set[str]:
        """Get list of users in container"""
        users = set()
        
        # Try /etc/passwd
        passwd_output = self.exec_in_container(
            container_id,
            ['cat', '/etc/passwd']
        )
        
        if passwd_output:
            for line in passwd_output.strip().split('\n'):
                if ':' in line:
                    username = line.split(':')[0]
                    users.add(username)
        
        # Also get currently logged in users
        who_output = self.exec_in_container(
            container_id,
            ['who']
        )
        
        if who_output:
            for line in who_output.strip().split('\n'):
                if line.strip():
                    username = line.split()[0]
                    users.add(username)
        
        return users
    
    def collect_container_data(self, container: Dict[str, str]) -> Optional[ContainerSecurityInfo]:
        """Collect all security-related data from a container"""
        container_id = container['id']
        container_name = container['name']
        
        self.logger.info(f"Collecting data from container: {container_name} ({container_id[:12]})")
        
        # Get processes
        processes = self.get_processes(container_id)
        self.logger.info(f"  Found {len(processes)} processes")
        
        # Get network connections
        connections = self.get_network_connections(container_id)
        self.logger.info(f"  Found {len(connections)} network connections")
        
        # Extract external IPs
        external_ips = self.extract_external_ips(connections)
        self.logger.info(f"  Found {len(external_ips)} external IPs")
        
        # Get open ports
        open_ports = self.get_open_ports(container_id)
        self.logger.info(f"  Found {len(open_ports)} open ports")
        
        # Get users
        users = self.get_users(container_id)
        self.logger.info(f"  Found {len(users)} users")
        
        return ContainerSecurityInfo(
            container_id=container_id,
            container_name=container_name,
            image=container['image'],
            status=container['status'],
            processes=processes,
            network_connections=connections,
            external_ips=external_ips,
            open_ports=open_ports,
            users=users,
            timestamp=datetime.now().isoformat()
        )
    
    def spy_on_containers(self) -> List[ContainerSecurityInfo]:
        """Main method to spy on all containers"""
        containers = self.get_running_containers()
        
        if not containers:
            self.logger.warning("No running containers found")
            return []
        
        self.containers_data = []
        
        for container in containers:
            try:
                data = self.collect_container_data(container)
                if data:
                    self.containers_data.append(data)
            except Exception as e:
                self.logger.error(
                    f"Error collecting data from container {container.get('name', 'unknown')}: {e}"
                )
                continue
        
        return self.containers_data
    
    def generate_neo4j_schema(self) -> str:
        """Generate Neo4j schema representation for the collected data"""
        schema = []
        schema.append("=" * 80)
        schema.append("NEO4J SCHEMA FOR DOCKER CONTAINER MONITORING")
        schema.append("=" * 80)
        schema.append("")
        
        # Node Types
        schema.append("## Node Types")
        schema.append("")
        schema.append("### 1. DockerContainer")
        schema.append("")
        schema.append("Represents a Docker container.")
        schema.append("")
        schema.append("**Properties:**")
        schema.append("- `id` (String, Unique, Indexed) - Container ID")
        schema.append("- `name` (String) - Container name")
        schema.append("- `image` (String) - Docker image name")
        schema.append("- `status` (String) - Container status")
        schema.append("- `timestamp` (DateTime) - When data was collected")
        schema.append("- `last_updated` (DateTime) - Last update timestamp")
        schema.append("")
        schema.append("**Constraints:**")
        schema.append("- UNIQUE constraint on `id`")
        schema.append("")
        schema.append("**Indexes:**")
        schema.append("- Index on `id`")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        schema.append("### 2. Process")
        schema.append("")
        schema.append("Represents a process running inside a container.")
        schema.append("")
        schema.append("**Properties:**")
        schema.append("- `id` (String, Unique, Indexed) - Process ID: `process_{pid}_{container_id}`")
        schema.append("- `pid` (String) - Process ID")
        schema.append("- `user` (String) - User running the process")
        schema.append("- `cpu_percent` (Float) - CPU usage percentage")
        schema.append("- `memory_percent` (Float) - Memory usage percentage")
        schema.append("- `memory_kb` (Integer) - Memory usage in KB")
        schema.append("- `command` (String) - Process command")
        schema.append("- `start_time` (String, Optional) - Process start time")
        schema.append("- `container_id` (String) - Reference to container")
        schema.append("- `timestamp` (DateTime) - When data was collected")
        schema.append("")
        schema.append("**Constraints:**")
        schema.append("- UNIQUE constraint on `id`")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        schema.append("### 3. NetworkConnection")
        schema.append("")
        schema.append("Represents a network connection from a container.")
        schema.append("")
        schema.append("**Properties:**")
        schema.append("- `id` (String, Unique, Indexed) - Connection ID: `conn_{protocol}_{local}_{remote}_{container_id}`")
        schema.append("- `protocol` (String) - Protocol (tcp/udp)")
        schema.append("- `local_address` (String) - Local IP address")
        schema.append("- `local_port` (Integer) - Local port")
        schema.append("- `remote_address` (String) - Remote IP address")
        schema.append("- `remote_port` (Integer) - Remote port")
        schema.append("- `state` (String) - Connection state")
        schema.append("- `process_name` (String, Optional) - Associated process name")
        schema.append("- `pid` (String, Optional) - Associated process ID")
        schema.append("- `container_id` (String) - Reference to container")
        schema.append("- `timestamp` (DateTime) - When data was collected")
        schema.append("")
        schema.append("**Constraints:**")
        schema.append("- UNIQUE constraint on `id`")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        schema.append("### 4. ExternalIP")
        schema.append("")
        schema.append("Represents an external IP address that a container communicates with.")
        schema.append("")
        schema.append("**Properties:**")
        schema.append("- `id` (String, Unique, Indexed) - IP ID: `ip_{address}`")
        schema.append("- `address` (String) - IP address")
        schema.append("- `is_private` (Boolean) - Whether IP is in private range")
        schema.append("- `timestamp` (DateTime) - When first seen")
        schema.append("- `last_seen` (DateTime) - Last time seen")
        schema.append("")
        schema.append("**Constraints:**")
        schema.append("- UNIQUE constraint on `id`")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        schema.append("### 5. OpenPort")
        schema.append("")
        schema.append("Represents an open port in a container.")
        schema.append("")
        schema.append("**Properties:**")
        schema.append("- `id` (String, Unique, Indexed) - Port ID: `port_{protocol}_{port}_{container_id}`")
        schema.append("- `protocol` (String) - Protocol (tcp/udp)")
        schema.append("- `address` (String) - Bind address")
        schema.append("- `port` (Integer) - Port number")
        schema.append("- `state` (String) - Port state")
        schema.append("- `container_id` (String) - Reference to container")
        schema.append("- `timestamp` (DateTime) - When data was collected")
        schema.append("")
        schema.append("**Constraints:**")
        schema.append("- UNIQUE constraint on `id`")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        schema.append("### 6. ContainerUser")
        schema.append("")
        schema.append("Represents a user account in a container.")
        schema.append("")
        schema.append("**Properties:**")
        schema.append("- `id` (String, Unique, Indexed) - User ID: `user_{username}_{container_id}`")
        schema.append("- `username` (String) - Username")
        schema.append("- `container_id` (String) - Reference to container")
        schema.append("- `timestamp` (DateTime) - When data was collected")
        schema.append("")
        schema.append("**Constraints:**")
        schema.append("- UNIQUE constraint on `id`")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        # Relationships
        schema.append("## Relationships")
        schema.append("")
        schema.append("### 1. RUNS_PROCESS")
        schema.append("")
        schema.append("**Direction:** `DockerContainer` → `Process`")
        schema.append("")
        schema.append("**Description:** Indicates that a container runs a process.")
        schema.append("")
        schema.append("**Properties:** None")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        schema.append("### 2. HAS_CONNECTION")
        schema.append("")
        schema.append("**Direction:** `DockerContainer` → `NetworkConnection`")
        schema.append("")
        schema.append("**Description:** Indicates that a container has a network connection.")
        schema.append("")
        schema.append("**Properties:** None")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        schema.append("### 3. CONNECTS_TO")
        schema.append("")
        schema.append("**Direction:** `NetworkConnection` → `ExternalIP`")
        schema.append("")
        schema.append("**Description:** Indicates that a network connection connects to an external IP.")
        schema.append("")
        schema.append("**Properties:** None")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        schema.append("### 4. HAS_OPEN_PORT")
        schema.append("")
        schema.append("**Direction:** `DockerContainer` → `OpenPort`")
        schema.append("")
        schema.append("**Description:** Indicates that a container has an open port.")
        schema.append("")
        schema.append("**Properties:** None")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        schema.append("### 5. HAS_USER")
        schema.append("")
        schema.append("**Direction:** `DockerContainer` → `ContainerUser`")
        schema.append("")
        schema.append("**Description:** Indicates that a container has a user account.")
        schema.append("")
        schema.append("**Properties:** None")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        schema.append("### 6. PROCESS_USES")
        schema.append("")
        schema.append("**Direction:** `Process` → `NetworkConnection`")
        schema.append("")
        schema.append("**Description:** Indicates that a process uses a network connection.")
        schema.append("")
        schema.append("**Properties:** None")
        schema.append("")
        schema.append("---")
        schema.append("")
        
        # Schema Structure
        schema.append("## Schema Structure Diagram")
        schema.append("")
        schema.append("```")
        schema.append("DockerContainer")
        schema.append(" ├─[:RUNS_PROCESS]→ Process")
        schema.append(" │   └─[:PROCESS_USES]→ NetworkConnection")
        schema.append(" │       └─[:CONNECTS_TO]→ ExternalIP")
        schema.append(" ├─[:HAS_CONNECTION]→ NetworkConnection")
        schema.append(" │   └─[:CONNECTS_TO]→ ExternalIP")
        schema.append(" ├─[:HAS_OPEN_PORT]→ OpenPort")
        schema.append(" └─[:HAS_USER]→ ContainerUser")
        schema.append("```")
        schema.append("")
        schema.append("=" * 80)
        
        return "\n".join(schema)
    
    def print_summary(self):
        """Print summary of collected data"""
        if not self.containers_data:
            print("No container data collected.")
            return
        
        print("\n" + "=" * 80)
        print("DOCKER CONTAINER MONITORING SUMMARY")
        print("=" * 80)
        print(f"\nTotal Containers Monitored: {len(self.containers_data)}")
        
        total_processes = sum(len(c.processes) for c in self.containers_data)
        total_connections = sum(len(c.network_connections) for c in self.containers_data)
        total_external_ips = len(set().union(*[c.external_ips for c in self.containers_data]))
        total_open_ports = sum(len(c.open_ports) for c in self.containers_data)
        total_users = len(set().union(*[c.users for c in self.containers_data]))
        
        print(f"Total Processes: {total_processes}")
        print(f"Total Network Connections: {total_connections}")
        print(f"Total External IPs: {total_external_ips}")
        print(f"Total Open Ports: {total_open_ports}")
        print(f"Total Users: {total_users}")
        
        print("\n" + "-" * 80)
        print("CONTAINER DETAILS:")
        print("-" * 80)
        
        for container in self.containers_data:
            print(f"\n📦 Container: {container.container_name}")
            print(f"   ID: {container.container_id[:12]}")
            print(f"   Image: {container.image}")
            print(f"   Status: {container.status}")
            print(f"   Processes: {len(container.processes)}")
            print(f"   Connections: {len(container.network_connections)}")
            print(f"   External IPs: {len(container.external_ips)}")
            if container.external_ips:
                print(f"      {', '.join(list(container.external_ips)[:10])}")
                if len(container.external_ips) > 10:
                    print(f"      ... and {len(container.external_ips) - 10} more")
            print(f"   Open Ports: {len(container.open_ports)}")
            if container.open_ports:
                for port in container.open_ports[:5]:
                    print(f"      {port['protocol']}/{port['port']} on {port['address']}")
            print(f"   Users: {len(container.users)}")
            
            # Top processes by CPU
            if container.processes:
                print(f"   Top 3 Processes by CPU:")
                for proc in container.processes[:3]:
                    print(f"      {proc.pid}: {proc.command[:50]} (CPU: {proc.cpu_percent:.1f}%, MEM: {proc.memory_percent:.1f}%)")


def main():
    """Main entry point"""
    print("🔍 Docker Container Service Spy")
    print("=" * 80)
    print()
    
    spy = DockerServiceSpy()
    
    # Collect data from all containers
    containers_data = spy.spy_on_containers()
    
    if not containers_data:
        print("❌ No container data collected. Make sure Docker is running and containers are available.")
        return
    
    # Print summary
    spy.print_summary()
    
    # Generate and print Neo4j schema
    print("\n" + "=" * 80)
    print("NEO4J SCHEMA")
    print("=" * 80)
    print()
    schema = spy.generate_neo4j_schema()
    print(schema)
    print()


if __name__ == "__main__":
    main()
