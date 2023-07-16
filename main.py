import toml
import queue
import threading

from fetch_numpy_frame import fetch_numpy_frame
from scanner_ui import ScannerUI

if __name__ == "__main__":
    config = toml.load('./static/config.toml')
    ui = ScannerUI(config['scanner_ui'])
    range_matrix_queue = queue.Queue()
    scanner_thread = threading.Thread(target=fetch_numpy_frame,
                                      args=(config['general']['ip'],
                                            range_matrix_queue))
    scanner_thread.start()
    ui.loop(range_matrix_queue)
    scanner_thread.join()
