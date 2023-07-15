import argparse
import queue
import threading

import numpy as np
import pygame
from scipy import ndimage

from fetch_numpy_frame import fetch_numpy_frame

background_image_dependency = False

# Define initial point size factor
point_size_factor = 10

# Load the background image
background = pygame.image.load('test-ground.jpg')
# Scale the image to fit the screen size
background = pygame.transform.scale(background, size=(2000, 2000))

# Define colors
black = (0, 0, 0)
white = (255, 255, 255)

# Define dependency mode for color and size
red_color_dependency = False
green_color_dependency = False
blue_color_dependency = False
size_dependency = False
weight_color_dependency = False
line_dependency = False
plus_minus_shape_dependency = False
circle_shape_dependency = False
background_image_dependency = False


# Normalizes a given matrix to range between 0 and 1.
def normalize_matrix(matrix):
    min_val = np.min(matrix)
    max_val = np.max(matrix)
    return (matrix - min_val) / (max_val - min_val)


# Define function to render points
def render_points(matrix, size_factor, screen, screen_size):
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            weight = matrix[i][j]
            # Make sure weight is not negative
            weight = max(weight, 0)
            # Make sure weight is not greater than 1
            weight = min(weight, 1)

            if weight_color_dependency:
                if weight <= 0.2:
                    color = (0, 0, 255)
                elif 0.2 < weight <= 0.4:
                    color = (173, 216, 230)
                elif 0.4 < weight <= 0.6:
                    color = (0, 255, 0)
                elif 0.6 < weight <= 0.8:
                    color = (255, 174, 66)
                else:  # 0.8 <= weight <= 1
                    color = (255, 0, 0)
            elif red_color_dependency:
                color = (int(weight * 255), 0, 0)
            elif green_color_dependency:
                color = (0, int(weight * 255), 0)
            elif blue_color_dependency:
                color = (0, 0, int(weight * 255))
            else:
                color = (255, 255, 255)

            x = int(i * screen_size[0] / (matrix.shape[0] - 1) + 200)
            y = int(j * screen_size[1] / (matrix.shape[1] - 1) + 20)
            size = int(weight * size_factor)

            if color == (0, 255, 0):
                size = 0

            if circle_shape_dependency:
                pygame.draw.circle(screen, color, (x, y), size_factor)
            elif plus_minus_shape_dependency:
                if weight > 0.6:
                    # Draw plus
                    pygame.draw.line(screen, color, (x - size // 2, y), (x + size // 2, y), 2)
                    pygame.draw.line(screen, color, (x, y - size // 2), (x, y + size // 2), 2)
                elif weight < 0.4:
                    # Draw minus
                    pygame.draw.line(screen, color, (x - size // 2, y), (x + size // 2, y), 2)
            elif size_dependency:
                pygame.draw.circle(screen, color, (x, y), size)


def render_lines(matrix, screen, screen_size):
    # render line for each point to it neighbour point
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            x1 = int(i * screen_size[0] / (matrix.shape[0] - 1) + 200)
            y1 = int(j * screen_size[1] / (matrix.shape[1] - 1) + 20)
            weight = matrix[i][j]
            if weight <= 0:
                continue
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    # line width
                    line_width = 3
                    if dx == 0 and dy == 0:
                        continue
                    if i + dx < 0 or i + dx >= matrix.shape[0] or j + dy < 0 or j + dy >= matrix.shape[1]:
                        continue
                    weight2 = matrix[i + dx][j + dy]
                    if weight2 <= 0:
                        continue
                    x2 = int((i + dx) * screen_size[0] / (matrix.shape[0] - 1) + 200)
                    y2 = int((j + dy) * screen_size[1] / (matrix.shape[1] - 1) + 20)
                    if weight_color_dependency:
                        if weight <= 0:
                            weight = 0
                        elif weight <= 0.2:
                            color = (0, 0, 255)
                        elif 0.2 < weight <= 0.4:
                            color = (173, 216, 230)
                        elif 0.6 < weight <= 0.7:
                            color = (255, 174, 66)
                        elif weight > 0.7:
                            color = (255, 0, 0)
                        else:
                            color = (0, 255, 0)
                            line_width = 0
                    elif red_color_dependency:
                        color = (weight * 255, 0, 0)
                    elif green_color_dependency:
                        color = (0, weight * 255, 0)
                    elif blue_color_dependency:
                        color = (0, 0, weight * 255)
                    else:
                        color = (255, 255, 255)
                    pygame.draw.line(screen, color, (x1, y1), (x2, y2), line_width)


def resize_matrix(matrix, new_size):
    zoom_factor = new_size / len(matrix)
    np.clip(matrix, 0.1, 0.9, out=matrix)
    return ndimage.zoom(matrix, zoom_factor)


if __name__ == "__main__":

    matrix_weights = np.zeros((20, 20))

    range_matrix_queue = queue.Queue()

    parser = argparse.ArgumentParser()  # Command line argument parser
    parser.add_argument("target")  # host name or IP address of the device

    args = parser.parse_args()  # Parse command line arguments

    # Create a new thread for listening to the keyboard inputs
    scanner_thread = threading.Thread(target=fetch_numpy_frame, daemon=True, args=(args.target, range_matrix_queue))
    scanner_thread.start()

    pygame.init()
    pygame.display.set_mode((0, 0))

    # Define screen size and point size
    screen_size = (pygame.display.Info().current_w - 400, pygame.display.Info().current_h - 20)
    point_size = 10

    # Set up the screen
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("2D Point Cloud")

    # Main loop
    running = True
    while running:
        try:
            if not range_matrix_queue.empty():
                range_matrix = range_matrix_queue.get()
                matrix_weights = normalize_matrix(range_matrix)
                if matrix_weights is not None:
                    render_points(matrix_weights, point_size_factor, screen, screen_size)
                else:
                    print("No data received.")
        except Exception as e:
            print(f"Caught an exception:\n{str(e)}")

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                elif event.key == pygame.K_UP:
                    matrix_size += 1
                    matrix_weights = resize_matrix(matrix_weights, matrix_size)
                    # print("------------NEW MATRIX------------SIZE = " + str(matrix_size))
                    # print(matrix_weights.round(2))
                elif event.key == pygame.K_DOWN:
                    matrix_size -= 1
                    if matrix_size < 2:
                        matrix_size = 2
                    matrix_weights = resize_matrix(matrix_weights, matrix_size)
                    # print("------------NEW MATRIX------------SIZE = " + str(matrix_size))
                    # print(matrix_weights.round(2))
                elif event.key == pygame.K_LEFT:
                    point_size_factor -= 1
                    if point_size_factor < 1:
                        point_size_factor = 1
                elif event.key == pygame.K_RIGHT:
                    point_size_factor += 1
                elif event.key == pygame.K_l:
                    weight_color_dependency = not weight_color_dependency
                elif event.key == pygame.K_r:
                    red_color_dependency = not red_color_dependency
                elif event.key == pygame.K_g:
                    green_color_dependency = not green_color_dependency
                elif event.key == pygame.K_b:
                    blue_color_dependency = not blue_color_dependency
                elif event.key == pygame.K_s:
                    size_dependency = not size_dependency
                elif event.key == pygame.K_p:
                    line_dependency = not line_dependency
                elif event.key == pygame.K_n:
                    circle_shape_dependency = not circle_shape_dependency
                elif event.key == pygame.K_m:
                    plus_minus_shape_dependency = not plus_minus_shape_dependency
                elif event.key == pygame.K_q:
                    background_image_dependency = not background_image_dependency

        # Render screen
        if background_image_dependency:
            screen.blit(background, (0, 0))
        else:
            screen.fill(black)
        render_points(matrix_weights, point_size_factor, screen, screen_size)
        if line_dependency:
            render_lines(matrix_weights, screen, screen_size)
        pygame.display.flip()

    # Quit Pygame
    pygame.quit()

    scanner_thread.join()
