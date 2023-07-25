import blickfeld_scanner
import numpy as np
from blickfeld_scanner.protocol.config import scan_pattern_pb2
from math import pi
import traceback

file_path = "rec2.bfpc"
NUM_SCANLINES = 56  # hardcoded for "High frame rate" scan pattern
HALF_SCANLINES = NUM_SCANLINES // 2
# Generate zig-zag pattern for each half
LAST_ODD = HALF_SCANLINES - 1 if HALF_SCANLINES % 2 == 0 else HALF_SCANLINES - 2
DESCENDING_ODDS = np.arange(LAST_ODD, -1, -2)
ASCENDING_EVENS = np.arange(0, HALF_SCANLINES, 2)
ZIGZAG_INDICES = np.concatenate((DESCENDING_ODDS, ASCENDING_EVENS))
ZIGZAG_INDICES_REV = np.concatenate((ASCENDING_EVENS, DESCENDING_ODDS))


def process_matrix(points, num_scanlines, num_points, descending_odds, zigzag_indices):
    range_matrix = points['range'].reshape(num_scanlines, num_points)
    # Reorder matrix
    range_matrix = range_matrix[zigzag_indices, :]

    # Reverse column order for the first half of rows in the zigzag pattern
    range_matrix[:len(descending_odds), :] = range_matrix[:len(descending_odds), ::-1]
    # cut the middle slice of the matrix
    range_matrix = range_matrix[:, 34:146]
    return range_matrix


def correct_distances(distances, max_angle_rad, _scanner_height):
    num_scanlines, num_angles = distances.shape

    # Create a 1D array for the angles
    angles = np.linspace(-max_angle_rad/2, max_angle_rad/2, num_angles)
    angles_2d = np.tile(angles, (num_scanlines, 1))
    corrected = distances * np.cos(angles_2d)
    return corrected


def read_frames_from_file(stream_to_matrix, queue):
    frame, points = stream_to_matrix.recv_frame_as_numpy()
    num_points = len(points) // NUM_SCANLINES

    # Split points into two halves and process each half
    sep = HALF_SCANLINES * num_points
    points1, points2 = points[:sep], points[sep:]

    range_matrix1 = process_matrix(points1, HALF_SCANLINES, num_points, DESCENDING_ODDS, ZIGZAG_INDICES)
    range_matrix2 = process_matrix(points2, HALF_SCANLINES, num_points, ASCENDING_EVENS, ZIGZAG_INDICES_REV)

    # Rotate matrix 180 degrees if the scanner is rotated too
    range_matrix1 = np.rot90(range_matrix1, k=2)

    max_angle = 2*pi / 5  # 72
    scanner_height = 1.95

    range_matrix1 = correct_distances(range_matrix1, max_angle, scanner_height)
    range_matrix2 = correct_distances(range_matrix2, max_angle, scanner_height)

    # Queue each processed half
    queue.put(range_matrix1)
    queue.put(range_matrix2)


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
            print(traceback.format_exc())
            thread_event.set()
