# experiments/analyze_and_plot.py

import ast
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def load_logs(prefix: str):
    folder = Path(prefix)
    try:
        cwnd_df = pd.read_csv(folder / "cwnd_log.csv")
    except FileNotFoundError:
        cwnd_df = None

    try:
        queue_df = pd.read_csv(folder / "queue_log.csv")
    except FileNotFoundError:   
        queue_df = None
   
    try:
        events_df = pd.read_csv(folder / "event_log.csv")
    except FileNotFoundError:
        events_df = None

    try:
        ack_df = pd.read_csv(folder / "ack_log.csv")
    except FileNotFoundError:
        ack_df = None
    
    # If details is stored as Python dict string, parse it
    if events_df is not None and "details" in events_df.columns:
        def parse_details(x):
            try:
                return ast.literal_eval(x) if isinstance(x, str) else {}
            except Exception:
                return {}
        events_df["details_parsed"] = events_df["details"].apply(parse_details)

    return cwnd_df, queue_df, events_df, ack_df


def compute_throughput(ack_df, mss_bytes=1500):
    if ack_df is None or ack_df.empty:
        return 0.0

    mask = ack_df["event_type"] == "ACK_RECEIVED"
    arrivals = ack_df[mask]
    if arrivals.empty:
        return 0.0

    # total bytes delivered
    total_packets = len(arrivals)
    total_bytes = total_packets * mss_bytes

    # simulation duration: from first to last event time
    t_start = arrivals["time"].min()
    t_end = arrivals["time"].max()
    sim_time = max(t_end - t_start, 1e-9)

    throughput_mbps = (total_bytes * 8) / sim_time / 1e6
    return throughput_mbps

def compute_rtt_stats(events_df, base_rtt_ms: float):
    """
    Compute mean RTT and average queueing delay (RTT - base_RTT).
    Assumes you log events with event_type == 'rtt_sample' and details['rtt'] in seconds.
    """
    if events_df is None or events_df.empty:
        return None

    mask = events_df["event_type"] == "rtt_sample"
    rtt_events = events_df[mask]
    if rtt_events.empty:
        return None

    rtts = rtt_events["details_parsed"].apply(lambda d: d.get("rtt", None)).dropna()
    if rtts.empty:
        return None

    mean_rtt_s = rtts.mean()
    mean_rtt_ms = mean_rtt_s * 1000.0
    mean_queue_delay_ms = max(mean_rtt_ms - base_rtt_ms, 0.0)

    return {
        "mean_rtt_ms": mean_rtt_ms,
        "mean_queue_delay_ms": mean_queue_delay_ms
    }


def compute_loss_stats(events_df):
    """
    Count congestion, random/bursty losses, and timeouts.
    """
    if events_df is None or events_df.empty:
        return {"congestion_losses": 0, "random_losses": 0, "timeouts": 0}

    congestion = (events_df["event_type"] == "CONGESTION_LOSS").sum()
    random_like = events_df["event_type"].isin(["RANDOM_LOSS", "BURSTY_LOSS"]).sum()
    timeouts = (events_df["event_type"].isin(["TIMEOUT", "timeout"])).sum()

    return {
        "congestion_losses": int(congestion),
        "random_losses": int(random_like),
        "timeouts": int(timeouts)
    }


def summarize_run(prefix: str, base_rtt_ms: float):
    cwnd_df, queue_df, events_df, ack_df = load_logs(prefix)

    throughput = compute_throughput(ack_df)
    rtt_stats = compute_rtt_stats(events_df, base_rtt_ms) or {}
    loss_stats = compute_loss_stats(events_df)

    summary = {
        "prefix": prefix,
        "throughput_mbps": throughput
    }
    summary.update(rtt_stats)
    summary.update(loss_stats)

    return summary


def plot_cwnd(prefix: str, cwnd_df):
    if cwnd_df is None or cwnd_df.empty:
        print(f"No cwnd data for {prefix}")
        return

    plt.figure()
    plt.plot(cwnd_df["time"], cwnd_df["cwnd"])
    plt.xlabel("Time [s]")
    plt.ylabel("cwnd [packets]")
    plt.title(f"cwnd vs time: {prefix}")
    out_path = Path("plots") / f"{Path(prefix).name}_cwnd.png"
    out_path.parent.mkdir(exist_ok=True, parents=True)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()

def plot_queue(prefix: str, queue_df):
    if queue_df is None or queue_df.empty:
        print(f"No queue data for {prefix}")
        return

    plt.figure()
    plt.plot(queue_df["time"], queue_df["queue_size"])
    plt.xlabel("Time [s]")
    plt.ylabel("Queue length [packets]")
    plt.title(f"Queue length vs time: {prefix}")
    out_path = Path("plots") / f"{Path(prefix).name}_queue.png"
    out_path.parent.mkdir(exist_ok=True, parents=True)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()


def plot_rtt(prefix: str, events_df):
    if events_df is None or events_df.empty:
        print(f"No events data for {prefix}")
        return

    mask = events_df["event_type"] == "rtt_sample"
    rtt_events = events_df[mask]
    if rtt_events.empty:
        print(f"No RTT samples for {prefix}")
        return

    times = rtt_events["time"]
    rtts_ms = rtt_events["details_parsed"].apply(lambda d: d.get("rtt", 0) * 1000.0)

    plt.figure()
    plt.scatter(times, rtts_ms, s=5)
    plt.xlabel("Time [s]")
    plt.ylabel("RTT [ms]")
    plt.title(f"RTT samples vs time: {prefix}")
    out_path = Path("plots") / f"{Path(prefix).name}_rtt.png"
    out_path.parent.mkdir(exist_ok=True, parents=True)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    scenarios = [
        ("logs/exp1_no_loss", 40.0),
        ("logs/exp2_random_low_loss", 40.0),
        ("logs/exp3_random_high_loss", 40.0),
        ("logs/exp4_bursty_small_queue", 40.0),
        ("logs/exp5_bursty_big_queue", 40.0),
    ]

    summaries = []
    for prefix, base_rtt_ms in scenarios:
        cwnd_df, queue_df, events_df, ack_df = load_logs(prefix)
        # Plots
        plot_cwnd(prefix, cwnd_df)
        plot_queue(prefix, queue_df)
        plot_rtt(prefix, events_df)

        # Summary stats
        summary = summarize_run(prefix, base_rtt_ms)
        summaries.append(summary)

    summary_df = pd.DataFrame(summaries)
    print(summary_df)
    summary_df.to_csv("plots/run_summaries.csv", index=False)
