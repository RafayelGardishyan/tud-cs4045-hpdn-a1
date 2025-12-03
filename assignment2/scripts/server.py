#!/usr/bin/env python3
"""
udp_server.py

UDP server that counts packets received from client 10.0.1.1
and prints the count every 5 seconds.
"""

import argparse
import socket
import time
import select


def main():
    parser = argparse.ArgumentParser(description="UDP server counting packets from 10.0.1.1.")
    parser.add_argument("--bind-ip", default="10.0.5.5", help="IP address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, required=True, help="UDP port to listen on")
    parser.add_argument("--client-ip", default="10.0.1.1",
                        help="Client IP to count packets from (default: 10.0.1.1)")
    parser.add_argument("--interval", type=float, default=5.0,
                        help="Print interval in seconds (default: 5)")
    args = parser.parse_args()

    target_client_ip = args.client_ip
    interval = args.interval

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind_ip, args.port))

    print(f"[*] UDP server listening on {args.bind_ip}:{args.port}")
    print(f"[*] Counting packets from client {target_client_ip}")
    print(f"[*] Reporting every {interval} seconds. Press Ctrl+C to stop.\n")

    # Counters
    window_count = 0   # packets in current interval from target client
    total_count = 0    # total packets from target client
    last_report_time = time.time()

    try:
        while True:
            now = time.time()
            timeout = max(0.0, last_report_time + interval - now)

            # Wait for incoming data with timeout so we can report periodically
            rlist, _, _ = select.select([sock], [], [], timeout)

            # If socket is ready, receive packet(s)
            if rlist:
                data, addr = sock.recvfrom(65535)  # (bytes, (ip, port))
                src_ip, src_port = addr

                # Count only packets from target client
                if src_ip == target_client_ip:
                    window_count += 1
                    total_count += 1

            # Time to report?
            now = time.time()
            if now - last_report_time >= interval:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                      f"Packets from {target_client_ip} in last {interval:.0f}s: {window_count}, "
                      f"total: {total_count}")
                window_count = 0
                last_report_time = now

    except KeyboardInterrupt:
        print("\n[*] Stopping server.")
        print(f"[*] Final total packets from {target_client_ip}: {total_count}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()

