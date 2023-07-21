import pygame
from utils import normalize_matrix, resize_matrix

BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)


class ScannerUI:

    def __init__(self, scanner_config: dict):
        pygame.init()
        self._screen, self._screen_size = self._init_screen()
        self._background = self._load_background(scanner_config)

        self._point_size_factor = 10

        self._red_color_dependency = False
        self._green_color_dependency = False
        self._blue_color_dependency = False
        self._size_dependency = False
        self._weight_color_dependency = False
        self._line_dependency = False
        self._plus_minus_shape_dependency = False
        self._circle_shape_dependency = False
        self._background_image_dependency = False
        self._scanner_config = scanner_config

    @staticmethod
    def _init_screen():
        pygame.display.set_mode((0, 0))
        screen_size = (pygame.display.Info().current_w - 800, pygame.display.Info().current_h - 20)
        pygame.display.set_caption("2D Point Cloud")
        return pygame.display.set_mode(screen_size, pygame.FULLSCREEN), screen_size

    @staticmethod
    def _load_background(scanner_config):
        # Load the background image
        background_photo = pygame.image.load(scanner_config['background_photo_path'])
        # Scale the image to fit the screen size
        background = pygame.transform.scale(background_photo, size=(2000, 2000))
        return background

    def loop(self, range_matrix_queue, thread_event):
        running = True
        matrix_size = 0

        while running:
            if range_matrix_queue.empty():
                continue
            range_matrix = range_matrix_queue.get()
            matrix_weights = normalize_matrix(range_matrix)
            self._render_points(matrix_weights)

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        thread_event.set()
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
                        self._point_size_factor -= 1
                        if self._point_size_factor < 1:
                            point_size_factor = 1
                    elif event.key == pygame.K_RIGHT:
                        self._point_size_factor += 1
                    elif event.key == pygame.K_l:
                        self._weight_color_dependency = not self._weight_color_dependency
                    elif event.key == pygame.K_r:
                        self._red_color_dependency = not self._red_color_dependency
                    elif event.key == pygame.K_g:
                        self._green_color_dependency = not self._green_color_dependency
                    elif event.key == pygame.K_b:
                        self._blue_color_dependency = not self._blue_color_dependency
                    elif event.key == pygame.K_s:
                        self._size_dependency = not self._size_dependency
                    elif event.key == pygame.K_p:
                        self._line_dependency = not self._line_dependency
                    elif event.key == pygame.K_n:
                        self._circle_shape_dependency = not self._circle_shape_dependency
                    elif event.key == pygame.K_m:
                        self._plus_minus_shape_dependency = not self._plus_minus_shape_dependency
                    elif event.key == pygame.K_q:
                        self._background_image_dependency = not self._background_image_dependency

            if self._background_image_dependency:
                self._screen.blit(self._background, (0, 0))
            else:
                self._screen.fill(BLACK_COLOR)
            self._render_points(matrix_weights)
            if self._line_dependency:
                self._render_lines(matrix_weights)
            pygame.display.flip()
        # Quit Pygame
        thread_event.set()
        pygame.quit()

    # Define function to render points
    def _render_points(self, matrix):
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                weight = matrix[i][j]
                # Make sure weight is not negative
                weight = max(weight, 0)
                # Make sure weight is not greater than 1
                weight = min(weight, 1)

                if self._weight_color_dependency:
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
                elif self._red_color_dependency:
                    color = (int(weight * 255), 0, 0)
                elif self._green_color_dependency:
                    color = (0, int(weight * 255), 0)
                elif self._blue_color_dependency:
                    color = (0, 0, int(weight * 255))
                else:
                    color = (255, 255, 255)

                x = int(j * self._screen_size[0] / (matrix.shape[1] - 1) + 310)
                y = int(i * self._screen_size[1] / (matrix.shape[0]) + 40)

                size = int(weight * self._point_size_factor)

                if color == (0, 255, 0):
                    size = 0

                if self._circle_shape_dependency:
                    pygame.draw.circle(self._screen, color, (x, y), self._point_size_factor)
                elif self._plus_minus_shape_dependency:
                    if weight > 0.6:
                        # Draw plus
                        pygame.draw.line(self._screen, color, (x - size // 2, y), (x + size // 2, y), 2)
                        pygame.draw.line(self._screen, color, (x, y - size // 2), (x, y + size // 2), 2)
                    elif weight < 0.4:
                        # Draw minus
                        pygame.draw.line(self._screen, color, (x - size // 2, y), (x + size // 2, y), 2)
                elif self._size_dependency:
                    pygame.draw.circle(self._screen, color, (x, y), size)

    def _render_lines(self, matrix):
        # render line for each point to it neighbour point
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1] - 1):
                x1 = int(i * self._screen_size[0] / (matrix.shape[0] - 1) + 200)
                y1 = int(j * self._screen_size[1] / (matrix.shape[1] - 1) + 20)
                weight = matrix[i][j]
                if weight <= 0:
                    continue

                # Only considering the right neighbor, so dx = 0 and dy = 1
                dx = 0
                dy = 1

                weight2 = matrix[i + dx][j + dy]
                if weight2 <= 0:
                    continue
                x2 = int((i + dx) * self._screen_size[0] / (matrix.shape[0] - 1) + 200)
                y2 = int((j + dy) * self._screen_size[1] / (matrix.shape[1] - 1) + 20)

                # line width
                line_width = 3

                # Determine the color based on the weight
                if self._weight_color_dependency:
                    if weight <= 0.2:
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
                elif self._red_color_dependency:
                    color = (weight * 255, 0, 0)
                elif self._green_color_dependency:
                    color = (0, weight * 255, 0)
                elif self._blue_color_dependency:
                    color = (0, 0, weight * 255)
                else:
                    color = (255, 255, 255)

                pygame.draw.line(self._screen, color, (x1, y1), (x2, y2), line_width)
