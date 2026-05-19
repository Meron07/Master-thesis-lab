#!/bin/bash

set -u

NUM_RUNS=10
CAPTURE_DURATION=60
OUTDIR="$HOME/iec104-lab/multi_runs_real/noisy_baseline"
LOGDIR="$OUTDIR/logs"
IFACE="lo"
PORT="2404"

SERVER_BIN="$HOME/lib60870/lib60870-C/examples/cs104_server/cs104_server"
CLIENT_BIN="$HOME/lib60870/lib60870-C/examples/cs104_client/cs104_client"

mkdir -p "$OUTDIR" "$LOGDIR"

cleanup() {
  sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
  pkill -f "$SERVER_BIN" 2>/dev/null || true
  pkill -f "$CLIENT_BIN" 2>/dev/null || true
  pkill -f "tshark -i $IFACE" 2>/dev/null || true
}
trap cleanup EXIT

for i in $(seq 1 $NUM_RUNS); do
  echo "=============================="
  echo "Starting run_$i"
  echo "=============================="

  PCAP_FILE="$OUTDIR/run_${i}.pcapng"
  PARAM_FILE="$OUTDIR/run_${i}_params.txt"

  case $i in
    1) DELAY="8ms";  JITTER="2ms"; LOSS="0%"   ;;
    2) DELAY="10ms"; JITTER="3ms"; LOSS="0%"   ;;
    3) DELAY="12ms"; JITTER="4ms"; LOSS="0.5%" ;;
    4) DELAY="9ms";  JITTER="5ms"; LOSS="0%"   ;;
    5) DELAY="15ms"; JITTER="3ms"; LOSS="1%"   ;;
    6) DELAY="7ms";  JITTER="2ms"; LOSS="0%"   ;;
    7) DELAY="11ms"; JITTER="4ms"; LOSS="0.5%" ;;
    8) DELAY="14ms"; JITTER="5ms"; LOSS="1%"   ;;
    9) DELAY="6ms";  JITTER="2ms"; LOSS="0%"   ;;
    10) DELAY="13ms"; JITTER="3ms"; LOSS="0.5%" ;;
  esac
  echo "delay=$DELAY"  > "$PARAM_FILE"
  echo "jitter=$JITTER" >> "$PARAM_FILE"
  echo "loss=$LOSS"     >> "$PARAM_FILE"
  echo "duration=$CAPTURE_DURATION" >> "$PARAM_FILE"
  echo "interface=$IFACE" >> "$PARAM_FILE"
  echo "port=$PORT" >> "$PARAM_FILE"

  cleanup
  sleep 2

  echo "[run_$i] Applying netem: delay $DELAY jitter $JITTER loss $LOSS"
  sudo tc qdisc add dev "$IFACE" root netem delay "$DELAY" "$JITTER" distribution normal loss "$LOSS"

  echo "[run_$i] Starting server"
  "$SERVER_BIN" > "$LOGDIR/run_${i}_server.log" 2>&1 &
  SERVER_PID=$!
  sleep 2

  echo "[run_$i] Starting capture"
  tshark -i "$IFACE" -f "tcp port $PORT" -a duration:$CAPTURE_DURATION -w "$PCAP_FILE" \
> "$LOGDIR/run_${i}_tshark.log" 2>&1 &
  TSHARK_PID=$!
  sleep 2

  echo "[run_$i] Starting client"
  "$CLIENT_BIN" 127.0.0.1 > "$LOGDIR/run_${i}_client.log" 2>&1 &
  CLIENT_PID=$!

  wait $TSHARK_PID

  echo "[run_$i] Capture finished, stopping client/server"
  kill $CLIENT_PID 2>/dev/null || true
  kill $SERVER_PID 2>/dev/null || true
  wait $CLIENT_PID 2>/dev/null || true
  wait $SERVER_PID 2>/dev/null || true

  sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
  sleep 2

  echo "[run_$i] Saved $PCAP_FILE"
done

echo "All noisy baseline runs completed."
