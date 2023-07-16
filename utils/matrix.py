import numpy as np
from scipy import ndimage


# Normalizes a given matrix to range between 0 and 1.
def normalize_matrix(matrix):
    min_val = np.min(matrix)
    max_val = np.max(matrix)
    return (matrix - min_val) / (max_val - min_val)


def resize_matrix(matrix, new_size):
    zoom_factor = new_size / len(matrix)
    np.clip(matrix, 0.1, 0.9, out=matrix)
    return ndimage.zoom(matrix, zoom_factor)
