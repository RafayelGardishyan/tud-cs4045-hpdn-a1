#!/usr/bin/env python3
"""
udp_client.py

Send a number of connectionless UDP packets to a server.
"""

import argparse
import socket
import time


def main():
    parser = argparse.ArgumentParser(description="Simple UDP packet sender.")
    parser.add_argument("--server-ip", required=True, help="Server IP address")
    parser.add_argument("--server-port", type=int, required=True, help="Server UDP port")
    parser.add_argument("--count", type=int, default=100, help="Number of packets to send")
    parser.add_argument("--interval", type=float, default=0.01,
                        help="Interval between packets in seconds (default: 0.01)")
    parser.add_argument("--message", default="hello",
                        help="Payload to send in each packet (default: 'hello')")

    args = parser.parse_args()

    server_addr = (args.server_ip, args.server_port)
    msg_bytes = args.message.encode("utf-8")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"[*] Sending {args.count} UDP packets to {server_addr} ...")
    try:
        for i in range(1, args.count + 1):
            sock.sendto(msg_bytes, server_addr)
            if i % 100 == 0 or i == args.count:
                print(f"  Sent {i}/{args.count}")
            if args.interval > 0:
                time.sleep(args.interval)
    finally:
        sock.close()
        print("[*] Done sending packets.")


if __name__ == "__main__":
    main()

