import math
import adsk.core

#Constants
INNER_OFFSET = .1
LIP_DEPTH = -.29
INNER_RADIUS = 1.00
RADIUS_OFFSET = 0.18

OUTER_RADIUS = INNER_RADIUS + RADIUS_OFFSET
SIDE_LENGTH = OUTER_RADIUS * (2.0 * math.tan(math.pi/6))

TOTAL_THICKNESS = adsk.core.ValueInput.createByReal(0.8)

INNER_CHAMFER_DISTANCES = [adsk.core.ValueInput.createByReal(.09), adsk.core.ValueInput.createByReal(.1)]
BOTTOM_CHAMFER_DISTANCES = [adsk.core.ValueInput.createByReal(.05), adsk.core.ValueInput.createByReal(.04)]