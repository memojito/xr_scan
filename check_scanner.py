import argparse

import blickfeld_scanner
import numpy as np
from blickfeld_scanner.protocol.config import scan_pattern_pb2


def fetch_numpy_frame(target):
    """Fetch the point cloud of a device as a numpy structued array.

    This example will stop after 10 received frames.

    :param target: hostname or IP address of the device
    """
    device = blickfeld_scanner.scanner(target)  # Connect to the device

    # Create filter to filter points and returns by point attributes during the post-processing on the device.
    point_filter = scan_pattern_pb2.ScanPattern().Filter()
    point_filter.max_number_of_returns_per_point = 2  # Set max number of returns to 2. The default value is 1.
    point_filter.delete_points_without_returns = True  # Filter points with no returns. This reduces the dataset only
    # to valid returns.

    # Create a point cloud stream object
    # The `as_numpy` flag enables the numpy support.
    stream = device.get_point_cloud_stream(point_filter=point_filter, as_numpy=True)

    named_scan_patterns = device.get_named_scan_patterns()  # Get named scan patterns
    for scan_pattern in named_scan_patterns.configs:
        print("'" + str(scan_pattern.name) + "' succesfully stored.")

    device.set_scan_pattern(name="INSPIRe")

    for i in range(10):
        frame, data = stream.recv_frame_as_numpy()
        print("Frame", str(frame.id) + ":", data)
        print("Size:", data.size, "Type:", data.dtype)

        # Example for filtering the strucuted array
        multiple_returns = data[np.argwhere(data['return_id'] > 0)]
        print("Got %d multiple returns" % (len(multiple_returns)))

        # Extract cartesian coordinates
        x, y, z = (data['cartesian']['x'], data['cartesian']['y'], data['cartesian']['z'])
        print(x, y, z)
        print(frame.scanlines)

        print()  # newline

    stream.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()  # Command line argument parser
    parser.add_argument("target",
                        help="hostname or IP of scanner to connect to")  # host name or IP address of the device

    args = parser.parse_args()  # Parse command line arguments
    fetch_numpy_frame(args.target)  # Start example