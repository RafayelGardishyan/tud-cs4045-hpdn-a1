# 1. Start iperf servers on Host 2 (TCP and UDP)
h2 iperf -s &
h2 iperf -s -u &

# 2. Print status
echo "--- Starting Traffic (TCP, UDP, ICMP) ---"

# 3. Start Traffic from Host 1
# TCP flow (runs for 20 seconds)
h1 iperf -c h2 -t 20 &
# UDP flow (5Mbps, runs for 20 seconds)
h1 iperf -u -c h2 -b 5M -t 20 &
# ICMP ping (runs for 20 seconds)
h1 ping -c 20 h2 &

# 4. Wait 10 seconds to establish baseline bandwidth
echo "--- Traffic running. Waiting 10s before breaking link... ---"
sleep 10

# 5. Break the UDP Link
# Note: Ensure s1 and s2 are the switches connected by the UDP link.
# If your UDP path goes through an intermediate switch (e.g., s1-s3-s2),
# change this to 'link s1 s3 down'.
echo "--- BREAKING UDP LINK NOW ---"
ifconfig s1-eth3 down

# 6. Wait to observe failover
echo "--- Link broken. Observing bandwidth/failover for 10s... ---"
sleep 10

# 7. Cleanup
echo "--- Test Finished. Stopping iperf... ---"
h1 killall iperf
h2 killall iperf