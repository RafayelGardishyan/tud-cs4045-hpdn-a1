# 1. Start iperf servers on Host 2 (TCP and UDP)
h2 iperf -s &
h2 iperf -s -u &

# 2. Print status
sh echo "--- Starting Traffic (TCP, UDP, ICMP) ---"

# 3. Start Traffic from Host 1
# TCP flow (runs for 20 seconds)
h1 iperf -c h2 -t 20 &
# UDP flow (5Mbps, runs for 20 seconds)
h1 iperf -u -c h2 -b 5M -t 20 &
# ICMP ping (runs for 20 seconds)
h1 ping -c 20 h2 &

# 4. Wait 10 seconds to establish baseline bandwidth
sh echo "--- Traffic running. Waiting 10s before breaking link... ---"
sh sleep 10

# 5. Break the UDP Link
# Note: Ensure s1 and s2 are the switches connected by the UDP link.
# If your UDP path goes through an intermediate switch (e.g., s1-s3-s2),
# change this to 'link s1 s3 down'.
sh echo "--- BREAKING UDP LINK NOW ---"
link s1 s2 down

# 6. Wait to observe failover
sh echo "--- Link broken. Observing bandwidth/failover for 10s... ---"
sh sleep 10

# 7. Cleanup
sh echo "--- Test Finished. Stopping iperf... ---"
h1 killall iperf
h2 killall iperf