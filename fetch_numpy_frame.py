import blickfeld_scanner
import numpy as np
from blickfeld_scanner.protocol.config import scan_pattern_pb2
from math import pi

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


NUM_SCANLINES = 56  # hardcoded for "High frame rate" scan pattern
HALF_SCANLINES = NUM_SCANLINES // 2
# Generate zig-zag pattern for each half
LAST_ODD = HALF_SCANLINES - 1 if HALF_SCANLINES % 2 == 0 else HALF_SCANLINES - 2
DESCENDING_ODDS = np.arange(LAST_ODD, -1, -2)
ASCENDING_EVENS = np.arange(0, HALF_SCANLINES, 2)
ZIGZAG_INDICES = np.concatenate((DESCENDING_ODDS, ASCENDING_EVENS))


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
    num_scanlines = len(distances)
    # calculate corrected distances
    corrected = distances * np.cos(
        (np.arange(len(distances)) / (num_scanlines - 1)) * max_angle_rad * 2 - max_angle_rad)
    return corrected


def read_frames_from_file(stream_to_matrix, queue):
    frame, points = stream_to_matrix.recv_frame_as_numpy()
    num_points = len(points) // NUM_SCANLINES

    # Split points into two halves and process each half
    sep = HALF_SCANLINES * num_points
    points1, points2 = points[:sep], points[sep:]

    range_matrix1 = process_matrix(points1, HALF_SCANLINES, num_points, DESCENDING_ODDS, ZIGZAG_INDICES)
    range_matrix2 = process_matrix(points2, HALF_SCANLINES, num_points, ASCENDING_EVENS, ZIGZAG_INDICES)

    # Rotate matrix 180 degrees if the scanner is rotated too
    range_matrix1 = np.rot90(range_matrix1, k=2)

    max_angle = pi / 4  # 45  # replace with your scanner's max angle
    scanner_height = 1.95

    range_matrix1 = correct_distances(range_matrix1, max_angle, scanner_height)
    range_matrix2 = correct_distances(range_matrix2, max_angle, scanner_height)

    # Queue each processed half
    queue.put(range_matrix1)
    queue.put(range_matrix2)

    # print(f"Scanline 0: {range_matrix1[0]}\n")
    # print(f"Scanline 13: {range_matrix1[13]}\n")
    # print(f"Scanline 27: {range_matrix1[27]}\n\n")

    # range_matrix = np.transpose(range_matrix)

    # index_matrix = np.transpose(index_matrix)

    # print(index_matrix)
    # print(index_matrix[28])

    print(range_matrix1)
    # print(range_matrix[28])
    # print(range_matrix[55])

    # print("min of scanline 54: {}".format(min(range_matrix[54])))
    # print("min of scanline 36: {}".format(min(range_matrix[36])))
    # print("min of scanline 28: {}".format(min(range_matrix[28])))
    # print("min of scanline 37: {}".format(min(range_matrix[37])))
    # print("min of scanline 55: {}\n".format(min(range_matrix[55])))
    # print("min of matrix: {}".format(np.min(range_matrix)))
    # print("max of matrix: {}\n".format(np.max(range_matrix)))

    # # get the index of the maximum value
    # max_index = np.unravel_index(np.argmax(range_matrix, axis=None), range_matrix.shape)
    # print(f"Max index: {max_index}")
    #
    # # get the index of the minimum value
    # min_index = np.unravel_index(np.argmin(range_matrix, axis=None), range_matrix.shape)
    # print(f"Min index: {min_index}\n\n")

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
