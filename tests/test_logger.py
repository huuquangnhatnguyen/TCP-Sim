import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.logger import LoggerFactory

def test_logger_initialization(tmp_path):
    # Change working directory to a temporary path
    os.chdir(tmp_path)

    logger_factory = LoggerFactory()

    # Check if log directory is created
    log_dir = tmp_path / "logs"
    assert log_dir.exists() and log_dir.is_dir()

    # Check if log file is created
    log_file = log_dir / "simulation.log"
    assert log_file.exists() and log_file.is_file()

    # Check if initial log message is written
    with open(log_file, 'r') as f:
        logs = f.read()
        assert "Logger initialized" in logs
def test_logger_recording(tmp_path):
    # Change working directory to a temporary path
    os.chdir(tmp_path)

    logger_factory = LoggerFactory()

    # Record some entries
    logger_factory.record_cwnd(time=1.0, flow_id=1, cwnd=10)
    logger_factory.record_queue(time=1.0, link_id=1, queue_size=5)
    logger_factory.record_event(time=1.0, event_type="PACKET_SENT", details="Packet 1 sent")

    # Check if entries are recorded correctly
    assert len(logger_factory.cwnd_logger) == 1
    assert logger_factory.cwnd_logger[0] == {"time": 1.0, "flow_id": 1, "cwnd": 10}

    assert len(logger_factory.queue_logger) == 1
    assert logger_factory.queue_logger[0] == {"time": 1.0, "link_id": 1, "queue_size": 5}

    assert len(logger_factory.event_logger) == 1
    assert logger_factory.event_logger[0] == {"time": 1.0, "event_type": "PACKET_SENT", "details": "Packet 1 sent"}
def test_logger_writing_csv(tmp_path):
    # Change working directory to a temporary path
    os.chdir(tmp_path)

    logger_factory = LoggerFactory()

    # Record some entries
    logger_factory.record_cwnd(time=1.0, flow_id=1, cwnd=10)
    logger_factory.record_queue(time=1.0, link_id=1, queue_size=5)
    logger_factory.record_event(time=1.0, event_type="PACKET_SENT", details="Packet 1 sent")

    # Write CSV files
    logger_factory._write_csv(logger_factory.cwnd_logger, "cwnd_log.csv", ["time", "flow_id", "cwnd"])
    logger_factory._write_csv(logger_factory.queue_logger, "queue_log.csv", ["time", "link_id", "queue_size"])
    logger_factory._write_csv(logger_factory.event_logger, "event_log.csv", ["time", "event_type", "details"])

    # Check if CSV files are created
    cwnd_log_file = tmp_path / "logs" / "cwnd_log.csv"
    queue_log_file = tmp_path / "logs" / "queue_log.csv"
    event_log_file = tmp_path / "logs" / "event_log.csv"

    assert cwnd_log_file.exists() and cwnd_log_file.is_file()
    assert queue_log_file.exists() and queue_log_file.is_file()
    assert event_log_file.exists() and event_log_file.is_file()

    # Check contents of one CSV file
    with open(cwnd_log_file, 'r') as f:
        lines = f.readlines()
        assert lines[0].strip() == "time,flow_id,cwnd"
        assert lines[1].strip() == "1.0,1,10"