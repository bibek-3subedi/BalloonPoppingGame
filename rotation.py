import math
import numpy as np
def rotation(x,y,tx,ty,radians):
    #Composite matrix (CM) for rotation by a fixed point tx,ty
    CM = np.array([
        [ math.cos(radians), -math.sin(radians), tx * (1 - math.cos(radians)) + ty * math.sin(radians) ],
        [ math.sin(radians), math.cos(radians), ty * (1 - math.cos(radians)) - tx * math.sin(radians) ],
        [0, 0, 1],
    ])

    #points to be rotated by certain angle
    P = np.array([
        [x],
        [y],
        [1]
    ])

    newpoint = CM @ P

    return newpoint

