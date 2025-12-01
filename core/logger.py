import pathlib
import logging
from logging import Logger
import csv

class LoggerFactory:
    def __init__(self):
        self.cwnd_logger = []
        self.queue_logger = []
        self.event_logger = []

        self.logger: Logger = logging.getLogger("network_simulator")
        self.logger.setLevel(logging.DEBUG)
        log_path = pathlib.Path("logs")
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path / "simulation.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.info("Logger initialized")

    def record_cwnd(self, time: float, flow_id: int, cwnd: int):
        self.cwnd_logger.append(
            {
                "time": time,
                "flow_id": flow_id,
                "cwnd": cwnd
            }
        )
        self.logger.debug(f"Recorded cwnd: time={time}, flow_id={flow_id}, cwnd={cwnd}")
    
    def record_queue(self, time: float, link_id: int, queue_size: int):
        self.queue_logger.append(
            {
                "time": time,
                "link_id": link_id,
                "queue_size": queue_size
            }
        )
        self.logger.debug(f"Recorded queue: time={time}, link_id={link_id}, queue_size={queue_size}")
    
    def record_event(self, time: float, event_type: str, details: str):
        self.event_logger.append(
            {
                "time": time,
                "event_type": event_type,
                "details": details
            }
        )
        self.logger.debug(f"Recorded event: time={time}, event_type={event_type}, details={details}")

    def _write_csv(self, data: list, filename: str, fieldnames: list):
        log_path = pathlib.Path("logs")
        with open(log_path / filename, mode='w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        self.logger.info(f"Wrote log to {filename}")

    def write_all_logs(self):
        self._write_csv(self.cwnd_logger, "cwnd_log.csv", ["time", "flow_id", "cwnd"])
        self._write_csv(self.queue_logger, "queue_log.csv", ["time", "link_id", "queue_size"])
        self._write_csv(self.event_logger, "event_log.csv", ["time", "event_type", "details"])