from datetime import timedelta
from decimal import Decimal
from streaming.obligation_store import ObligationStore
from streaming.stream_simulator import Snapshot, StreamSimulator


# Configuration 
CSV_PATH = "data/synthetic_obligations_08102026.csv" 
OUTPUT_PNG = "report.png"
WINDOW_MINUTES = 1          # netting window length
SPEED_FACTOR = 0            # instant, no sleep
INITIAL_BALANCE = 100_000  

# Build initial balances for all possible participants
NUM_BANKS = 30
participants = [f"Bank_{i}" for i in range(NUM_BANKS)]
initial_balances = {p: Decimal(INITIAL_BALANCE) for p in participants}

# Run simulation
store = ObligationStore()
snapshot = Snapshot()
sim = StreamSimulator(
    store,
    snapshot,
    initial_balances,
    window_duration=timedelta(minutes=WINDOW_MINUTES),
    speed_factor=SPEED_FACTOR,
)

print(f"Loading {CSV_PATH}...")
sim.run(CSV_PATH)

print(f"Processed {len(snapshot.window_history)} netting windows.")
print(f"Gross volume:   {snapshot.gross_volume:,.2f}")
print(f"Total settled:  {snapshot.total_settled:,.2f}")
print(f"Liquidity saved:{snapshot.liquidity_saved:,.2f}")

# Generate report
snapshot.generate_report(OUTPUT_PNG)
print(f"Report saved to {OUTPUT_PNG}")