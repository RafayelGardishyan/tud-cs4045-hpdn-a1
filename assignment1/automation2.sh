echo "--- SETUP: Cleaning previous iperf sessions ---"
h1 killall iperf
h2 killall iperf

echo "=========================================="
echo "TEST 1: TCP TRAFFIC (Path 1)"
echo "Expected: Traffic flows via s1-s2 (Port 2)"
echo "=========================================="

# Start TCP Servers in background
h1 iperf -s &
h2 iperf -s &

# Wait for servers to initialize
sh sleep 1

echo "-> Testing h1 to h2 (TCP)..."
h1 iperf -c h2 -t 3

echo "-> Testing h2 to h1 (TCP)..."
h2 iperf -c h1 -t 3

# Clean up TCP servers
h1 killall iperf
h2 killall iperf

echo "=========================================="
echo "TEST 2: UDP TRAFFIC (Path 2)"
echo "Expected: Traffic flows via s1-s2 (Port 3)"
echo "=========================================="

# Start UDP Servers in background
h1 iperf -s -u &
h2 iperf -s -u &

sh sleep 1

# Note: We limit bandwidth to 5M because links are 10Mbps [cite: 269]
echo "-> Testing h1 to h2 (UDP)..."
h1 iperf -u -c h2 -b 5M -t 3

echo "-> Testing h2 to h1 (UDP)..."
h2 iperf -u -c h1 -b 5M -t 3

# Clean up UDP servers
h1 killall iperf
h2 killall iperf

echo "=========================================="
echo "TEST 3: ICMP TRAFFIC (Path 3)"
echo "Expected: Traffic flows via s1-s2 (Port 4)"
echo "=========================================="

echo "-> Pinging h2 from h1..."
h1 ping -c 3 h2

echo "-> Pinging h1 from h2..."
h2 ping -c 3 h1

echo "--- TESTS COMPLETED ---"