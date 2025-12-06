import pathlib
import logging
from logging import Logger
import csv

class LoggerFactory:
    def __init__(self):
        self.cwnd_logger = []
        self.queue_logger = []
        self.event_logger = []
        self.packet_sent_logger = []
        self.ack_logger = []

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
                "event_type": "CWND_UPDATE",
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

    def record_packet_sent(self, time: float, flow_id: int, seq: int):
        self.packet_sent_logger.append(
            {
                "time": time,
                "event_type": "PACKET_SENT",
                "flow_id": flow_id,
                "seq": seq
            }
        )
        self.logger.debug(f"Recorded packet sent: time={time}, flow_id={flow_id}, seq={seq}")

    def record_ack(self, time: float, flow_id: int, ack_seq: int):
        self.ack_logger.append(
            {
                "time": time,
                "event_type": "ACK_RECEIVED",
                "flow_id": flow_id,
                "ack_seq": ack_seq
            }
        )
        self.logger.debug(f"Recorded ACK: time={time}, flow_id={flow_id}, ack_seq={ack_seq}")

    def _write_csv(self, data: list, folder: str, filename: str, fieldnames: list):
        log_path = pathlib.Path(folder)
        with open(log_path / filename, mode='w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        self.logger.info(f"Wrote log to {filename}")

    def write_all_logs(self, folder: str = "logs"):
        log_path = pathlib.Path(folder)
        log_path.mkdir(parents=True, exist_ok=True)
        self._write_csv(self.cwnd_logger, folder, "cwnd_log.csv", ["time", "event_type" ,"flow_id", "cwnd"])
        self._write_csv(self.queue_logger, folder, "queue_log.csv", ["time", "link_id", "queue_size"])
        self._write_csv(self.event_logger, folder, "event_log.csv", ["time", "event_type", "details"])
        self._write_csv(self.packet_sent_logger, folder, "packet_sent_log.csv", ["time", "event_type", "flow_id", "seq"])
        self._write_csv(self.ack_logger, folder, "ack_log.csv", ["time", "event_type", "flow_id", "ack_seq"])