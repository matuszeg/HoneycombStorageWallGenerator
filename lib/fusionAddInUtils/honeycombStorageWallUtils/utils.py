import adsk.fusion
import adsk.core
import math

from .constants import *

def create_half_comb(
        sketchFeature: adsk.fusion.Sketch,
        component: adsk.fusion.Component
):
    #create bottom border sketch profiles
    centerPoint = adsk.core.Point3D.create(SIDE_LENGTH * 2.5, 0, 0)
    innerHexagon = sketchFeature.sketchCurves.sketchLines.addScribedPolygon(centerPoint, 6, math.pi/2, INNER_RADIUS, False)
    bottomEdgeOuterHexagon = sketchFeature.sketchCurves.sketchLines.addScribedPolygon(centerPoint, 6, math.pi/2, OUTER_RADIUS, False)

    bottomEdgeSplitLine = sketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        bottomEdgeOuterHexagon.item(0).endSketchPoint,
        bottomEdgeOuterHexagon.item(3).endSketchPoint
    )

    bottomXOffset = RADIUS_OFFSET/math.tan(math.pi/3)
    firstPoint = adsk.core.Point3D.create(innerHexagon.item(0).endSketchPoint.geometry.x + bottomXOffset, innerHexagon.item(0).endSketchPoint.geometry.y + RADIUS_OFFSET, 0)
    secondPoint = adsk.core.Point3D.create(innerHexagon.item(3).endSketchPoint.geometry.x - bottomXOffset, innerHexagon.item(3).endSketchPoint.geometry.y + RADIUS_OFFSET, 0)
    sketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        firstPoint,
        secondPoint
    )

    #grab profiles and extrude upwards
    profileCollection = adsk.core.ObjectCollection.create()
    profileCollection.add(sketchFeature.profiles.item(2))
    profileCollection.add(sketchFeature.profiles.item(4))

    bottomBorderExtrudeInput = component.features.extrudeFeatures.createInput(profileCollection, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    bottomBorderExtrudeInput.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(TOTAL_THICKNESS), adsk.fusion.ExtentDirections.PositiveExtentDirection)
    bottomBorderExtrudeFeature = component.features.extrudeFeatures.add(bottomBorderExtrudeInput)

    borderTopSketch = component.sketches.add(bottomBorderExtrudeFeature.endFaces[0])
    borderTopSketch.name = "Honeycomb_BorderTop"
    
    topCornerOffsetX = INNER_OFFSET / math.tan(math.pi/3)
    cornerOffset = math.sqrt((INNER_OFFSET*2)*(INNER_OFFSET*2)-INNER_OFFSET*INNER_OFFSET)

    manualPolyBottomLeft = adsk.core.Point3D.create(firstPoint.x-cornerOffset, firstPoint.y - INNER_OFFSET)
    manualPolyBottomRight = adsk.core.Point3D.create(secondPoint.x+cornerOffset, secondPoint.y - INNER_OFFSET)
    
    manualPolyTopLeft = adsk.core.Point3D.create(
        innerHexagon.item(5).endSketchPoint.geometry.x-topCornerOffsetX,
        innerHexagon.item(5).endSketchPoint.geometry.y+INNER_OFFSET
    )

    manualPolyTopRight = adsk.core.Point3D.create(
        innerHexagon.item(4).endSketchPoint.geometry.x+topCornerOffsetX,
        innerHexagon.item(4).endSketchPoint.geometry.y+INNER_OFFSET
    )

    borderTopSketch.sketchCurves.sketchLines.addByTwoPoints(
        manualPolyBottomLeft,
        manualPolyBottomRight,
    )

    borderTopSketch.sketchCurves.sketchLines.addByTwoPoints(
        manualPolyBottomLeft,
        manualPolyTopLeft
    )

    borderTopSketch.sketchCurves.sketchLines.addByTwoPoints(
        manualPolyTopLeft,
        manualPolyTopRight
    )

    borderTopSketch.sketchCurves.sketchLines.addByTwoPoints(
        manualPolyTopRight,
        manualPolyBottomRight
    )

    #extrude down to start the lip
    bottomBorderCutFeature = component.features.extrudeFeatures.addSimple(
        borderTopSketch.profiles.item(0),
        adsk.core.ValueInput.createByReal(LIP_DEPTH),
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    
    #chamfer new inner edge
    borderBottomChamferEdgeCollection = adsk.core.ObjectCollection.create()
    borderBottomChamferEdgeCollection.add(bottomBorderExtrudeFeature.bodies[0].edges.item(12))
    borderBottomChamferEdgeCollection.add(bottomBorderExtrudeFeature.bodies[0].edges.item(13))
    borderBottomChamferEdgeCollection.add(bottomBorderExtrudeFeature.bodies[0].edges.item(14))
    borderBottomChamferEdgeCollection.add(bottomBorderExtrudeFeature.bodies[0].edges.item(15))

    borderBottomInnerChamferInput = component.features.chamferFeatures.createInput2()
    borderBottomInnerChamferInput.chamferEdgeSets.addTwoDistancesChamferEdgeSet(borderBottomChamferEdgeCollection, INNER_CHAMFER_DISTANCES[0], INNER_CHAMFER_DISTANCES[1], False, True)
    borderBottomInnerChamferFeature = component.features.chamferFeatures.add(borderBottomInnerChamferInput)

    # #chamfer bottom
    # count=0
    # for edge in bottomBorderExtrudeFeature.bodies[0].edges:
    #     borderBottomChamferEdgeCollection = adsk.core.ObjectCollection.create()
    #     borderBottomChamferEdgeCollection.add(bottomBorderExtrudeFeature.bodies[0].edges.item(count))
    #     design.selectionSets.add(borderBottomChamferEdgeCollection.asArray(), "{count}")
    #     count+=1

    borderBottomChamferEdgeCollection = adsk.core.ObjectCollection.create()
    borderBottomChamferEdgeCollection.add(bottomBorderExtrudeFeature.bodies[0].edges.item(13))
    borderBottomChamferEdgeCollection.add(bottomBorderExtrudeFeature.bodies[0].edges.item(16))
    borderBottomChamferEdgeCollection.add(bottomBorderExtrudeFeature.bodies[0].edges.item(26))
    borderBottomChamferEdgeCollection.add(bottomBorderExtrudeFeature.bodies[0].edges.item(27))

    borderBottomBottomChamferInput = component.features.chamferFeatures.createInput2()
    borderBottomBottomChamferInput.chamferEdgeSets.addTwoDistancesChamferEdgeSet(borderBottomChamferEdgeCollection, BOTTOM_CHAMFER_DISTANCES[0], BOTTOM_CHAMFER_DISTANCES[1], False, True)
    borderBottomBottomChamferFeature = component.features.chamferFeatures.add(borderBottomBottomChamferInput)

    borderBottomBody = bottomBorderExtrudeFeature.bodies[0]