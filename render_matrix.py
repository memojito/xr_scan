import numpy as np
import pygame
from scipy import ndimage

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
