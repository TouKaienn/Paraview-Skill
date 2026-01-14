#!/usr/bin/env python3
"""
Launch ParaView with pvserver for MCP integration.
Optionally auto-connects the GUI to the server.
"""

import os
import sys
import subprocess
import signal
import time
import argparse
import socket

def check_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_paraview_home() -> str:
    """Get PARAVIEW_HOME from environment."""
    return os.environ.get('PARAVIEW_HOME', '')

def check_status():
    """Check ParaView installation and server status."""
    pv_home = get_paraview_home()
    
    print("=== ParaView Status ===\n")
    
    if not pv_home:
        print("❌ PARAVIEW_HOME not set")
        print("   Set with: export PARAVIEW_HOME=/path/to/ParaView")
    else:
        print(f"✓ PARAVIEW_HOME: {pv_home}")
        
        pvserver = os.path.join(pv_home, 'bin', 'pvserver')
        paraview = os.path.join(pv_home, 'bin', 'paraview')
        pvpython = os.path.join(pv_home, 'bin', 'pvpython')
        
        for name, path in [('pvserver', pvserver), ('paraview', paraview), ('pvpython', pvpython)]:
            if os.path.exists(path):
                print(f"  ✓ {name}: {path}")
            else:
                print(f"  ❌ {name} not found at: {path}")
    
    print("\n=== Port Status ===\n")
    for port in [11111, 22222]:
        if check_port_in_use(port):
            print(f"  Port {port}: IN USE (pvserver may be running)")
        else:
            print(f"  Port {port}: Available")

def start_pvserver(port: int, multi_clients: bool = True):
    """Start pvserver in background."""
    pv_home = get_paraview_home()
    if not pv_home:
        print("Error: PARAVIEW_HOME not set")
        sys.exit(1)
    
    pvserver = os.path.join(pv_home, 'bin', 'pvserver')
    if not os.path.exists(pvserver):
        print(f"Error: pvserver not found at {pvserver}")
        sys.exit(1)
    
    if check_port_in_use(port):
        print(f"Warning: Port {port} already in use. pvserver may already be running.")
        return None
    
    cmd = [pvserver, f'--server-port={port}']
    if multi_clients:
        cmd.append('--multi-clients')
    
    print(f"Starting pvserver on port {port}...")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)  # Give server time to start
    
    if proc.poll() is not None:
        print("Error: pvserver failed to start")
        stdout, stderr = proc.communicate()
        if stdout:
            print(f"stdout: {stdout.decode()}")
        if stderr:
            print(f"stderr: {stderr.decode()}")
        sys.exit(1)
    
    print(f"pvserver started (PID: {proc.pid})")
    return proc

def launch_paraview_gui(host: str, port: int, auto_connect: bool = True):
    """Launch ParaView GUI, optionally auto-connecting to server."""
    pv_home = get_paraview_home()
    if not pv_home:
        print("Error: PARAVIEW_HOME not set")
        sys.exit(1)
    
    paraview = os.path.join(pv_home, 'bin', 'paraview')
    if not os.path.exists(paraview):
        print(f"Error: paraview not found at {paraview}")
        sys.exit(1)
    
    cmd = [paraview]
    if auto_connect:
        cmd.append(f'--server-url=cs://{host}:{port}')
    
    print(f"Launching ParaView GUI...")
    if auto_connect:
        print(f"  Auto-connecting to {host}:{port}")
    
    proc = subprocess.Popen(cmd)
    return proc

def main():
    parser = argparse.ArgumentParser(description="Launch ParaView with pvserver")
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=11111, help='Server port (default: 11111)')
    parser.add_argument('--no-server', action='store_true', help='Launch GUI only without starting pvserver')
    parser.add_argument('--no-connect', action='store_true', help='Launch GUI without auto-connecting')
    parser.add_argument('--server-only', action='store_true', help='Start pvserver only')
    parser.add_argument('--single-client', action='store_true', help='Start pvserver in single-client mode')
    parser.add_argument('--status', action='store_true', help='Check status only')
    
    args = parser.parse_args()
    
    if args.status:
        check_status()
        sys.exit(0)
    
    server_proc = None
    gui_proc = None
    
    def cleanup(signum=None, frame=None):
        print("\nShutting down...")
        if gui_proc:
            gui_proc.terminate()
        if server_proc:
            server_proc.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        # Start server unless --no-server
        if not args.no_server:
            server_proc = start_pvserver(args.port, not args.single_client)
        
        # Launch GUI unless --server-only
        if not args.server_only:
            auto_connect = not args.no_connect and not args.no_server
            gui_proc = launch_paraview_gui(args.host, args.port, auto_connect)
            
            print("\nParaView launched successfully!")
            print("Press Ctrl+C to stop server when done.")
            
            # Wait for GUI to close
            gui_proc.wait()
        else:
            print("\npvserver running. Press Ctrl+C to stop.")
            if server_proc:
                server_proc.wait()
    
    except KeyboardInterrupt:
        cleanup()
    finally:
        cleanup()

if __name__ == "__main__":
    main()
