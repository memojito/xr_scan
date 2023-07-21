import blickfeld_scanner
import numpy as np
from blickfeld_scanner.protocol.config import scan_pattern_pb2

file_path = "rec2.bfpc"


# Make a connection to the blickfeld scanner
# scanner_ip = "0.0.0.0"
# scanner = bs.scanner(scanner_ip)

# point_filter = scan_pattern_pb2.ScanPattern().Filter()
# point_filter.range.minimum = 1.5  # minimum range for a point to be sent out is 5m
# point_filter.range.maximum = 5  # maximum range for a point to be sent out is 50m
# point_filter.max_number_of_returns_per_point = 1  # Set max number of returns to 2. The default value is 1.
# point_filter.delete_points_without_returns = False  # Filter points with no returns.
# point_stream = stream.point_cloud(from_file=file_path, filter=point_filter, as_numpy=True)
# metadata = point_stream.get_metadata()
# print(f"Metadata:\n{metadata}")


def read_frames_from_file(stream_to_matrix, queue):
    frame, points = stream_to_matrix.recv_frame_as_numpy()

    # Modifying ranges
    points['range'] = np.clip(points['range'], 1, 6)

    # print(points['point_id'])
    # print(frame.scanlines)

    num_scanlines = 32  # hardcoded for INSPIRe scan pattern
    num_points = len(points) // num_scanlines
    range_matrix = points['range'].reshape(num_scanlines,
                                           num_points)  # gets a matrix (16x362) or (32x181) in case of INSPIRe

    index_matrix = points['point_id'].reshape(num_scanlines, num_points)

    # Generate zig-zag pattern
    last_odd = num_scanlines - 1 if num_scanlines % 2 == 0 else num_scanlines - 2
    descending_odds = np.arange(last_odd, -1, -2)
    ascending_evens = np.arange(0, num_scanlines, 2)
    zigzag_indices = np.concatenate((descending_odds, ascending_evens))

    # print(zigzag_indices)
    # print(index_matrix)
    # print(index_matrix[0])

    # Reorder matrix
    range_matrix = range_matrix[zigzag_indices, :]

    # Reverse column order for the first half of rows in the zigzag pattern
    for i in range(len(descending_odds)):
        range_matrix[i, :] = range_matrix[i, ::-1]

    # Rotate matrix 180 degrees if the scanner is rotated too
    range_matrix = [row[::-1] for row in range_matrix[::-1]]

    print(range_matrix)

    queue.put(range_matrix)

    # range_matrix = np.transpose(range_matrix)

    index_matrix = index_matrix[zigzag_indices, :]

    # index_matrix = np.transpose(index_matrix)

    print(index_matrix)
    # print(index_matrix[29])

    # print(range_matrix)


def fetch_numpy_frame(ip_address, queue, thread_event):
    """Fetch the point cloud of a device as a numpy structued array.
    :param queue: queue for sharing data between threads
    :param ip_address: hostname or IP address of the device
    :param thread_event: event for stop thread
    """
    while not thread_event.is_set():
        try:
            device = blickfeld_scanner.scanner(ip_address)  # Connect to the device

            device.set_scan_pattern(name="High frame rate") # XRgrid, High frame rate

            # named_scan_patterns = device.get_named_scan_patterns()  # Get named scan patterns
            # for scan_pattern in named_scan_patterns.configs:
            #     print("'" + str(scan_pattern.name) + "' succesfully stored.")

            # Create filter to filter points and returns by point attributes during the post-processing on the device.
            point_filter_device = scan_pattern_pb2.ScanPattern().Filter()
            # Create a point cloud stream object
            # The `as_numpy` flag enables the numpy support.
            stream = device.get_point_cloud_stream(point_filter=point_filter_device, as_numpy=True)
            read_frames_from_file(stream, queue)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            thread_event.set()
