import adsk.core
import adsk.fusion
import math

from .constants import *

def create_half_comb(
        type: BorderType,
        topPlane: adsk.fusion.ConstructionPlane,
        component: adsk.fusion.Component,
        startingCenterPoint: adsk.core.Point3D
):
    name = ""
    rotationFactor = 0

    if type == BorderType.BOTTOM:
        name = "Bottom"
        rotationFactor = 0

    elif type == BorderType.TOP:
        name = "Top"
        rotationFactor = math.pi

    sketchFeature = component.sketches.add(component.xYConstructionPlane)
    sketchFeature.name = "Honeycomb_Border_" + name

    #create bottom border sketch profiles
    innerHexagon = sketchFeature.sketchCurves.sketchLines.addScribedPolygon(startingCenterPoint, 6, math.pi/2, INNER_RADIUS, False)
    outerHexagon = sketchFeature.sketchCurves.sketchLines.addScribedPolygon(startingCenterPoint, 6, math.pi/2, OUTER_RADIUS, False)

    outerHexagon.item(1)

    splitLine = sketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        outerHexagon.item(0).endSketchPoint,
        outerHexagon.item(3).endSketchPoint
    )

    xOffset = RADIUS_OFFSET/math.tan(math.pi/3)
    firstPoint = adsk.core.Point3D.create(innerHexagon.item(0).endSketchPoint.geometry.x + xOffset, innerHexagon.item(0).endSketchPoint.geometry.y + RADIUS_OFFSET, 0)
    secondPoint = adsk.core.Point3D.create(innerHexagon.item(3).endSketchPoint.geometry.x - xOffset, innerHexagon.item(3).endSketchPoint.geometry.y + RADIUS_OFFSET, 0)
    innerLine = sketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        firstPoint,
        secondPoint
    )

    #grab profiles and extrude upwards
    profileCollection = adsk.core.ObjectCollection.create()
    profileCollection.add(sketchFeature.profiles.item(2))
    profileCollection.add(sketchFeature.profiles.item(4))

    extrudeInput = component.features.extrudeFeatures.createInput(profileCollection, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrudeInput.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(TOTAL_THICKNESS), adsk.fusion.ExtentDirections.PositiveExtentDirection)
    extrudeFeature = component.features.extrudeFeatures.add(extrudeInput)


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

    topSketchFeature = component.sketches.add(topPlane)
    topSketchFeature.name = "Honeycomb_BorderTop_" + name

    topSketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        manualPolyBottomLeft,
        manualPolyBottomRight,
    )

    topSketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        manualPolyBottomLeft,
        manualPolyTopLeft
    )

    topSketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        manualPolyTopLeft,
        manualPolyTopRight
    )

    topSketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        manualPolyTopRight,
        manualPolyBottomRight
    )

    #extrude down to start the lip
    bottomBorderCutFeature = component.features.extrudeFeatures.addSimple(
        topSketchFeature.profiles.item(0),
        adsk.core.ValueInput.createByReal(LIP_DEPTH),
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    
    #chamfer new inner edge
    borderBottomChamferEdgeCollection = adsk.core.ObjectCollection.create()
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(12))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(13))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(14))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(15))

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
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(13))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(16))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(26))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(27))

    borderBottomBottomChamferInput = component.features.chamferFeatures.createInput2()
    borderBottomBottomChamferInput.chamferEdgeSets.addTwoDistancesChamferEdgeSet(borderBottomChamferEdgeCollection, BOTTOM_CHAMFER_DISTANCES[0], BOTTOM_CHAMFER_DISTANCES[1], False, True)
    borderBottomBottomChamferFeature = component.features.chamferFeatures.add(borderBottomBottomChamferInput)

    if rotationFactor != 0:
        # axisInput = component.constructionAxes.createInput()
        
        # axisInput.setByPerpendicularAtPoint(profileCollection[0], sketchFeature.sketchPoints[0])

        # axis = component.constructionAxes.add(axisInput)

        rotationTransform = adsk.core.Matrix3D.create()
        rotationTransform.setToRotation(rotationFactor, adsk.core.Vector3D.create(0,0,1), startingCenterPoint)

        entities = adsk.core.ObjectCollection.create()
        entities.add(extrudeFeature.bodies[0])
        
        moveFeatureInput =  component.features.moveFeatures.createInput(entities, rotationTransform)

        # Add the move feature to the design
        component.features.moveFeatures.add(moveFeatureInput)


    return extrudeFeature.bodies[0]

def duplicate_border_body(
        component: adsk.fusion.Component,
        body: adsk.fusion.BRepBody,
        quantity: adsk.core.ValueInput,
        distance: adsk.core.ValueInput
):
    bottomBorderCollection = adsk.core.ObjectCollection.create()
    bottomBorderCollection.add(body)

    bottomBorderPatternInput = component.features.rectangularPatternFeatures.createInput(
        bottomBorderCollection,
        component.xConstructionAxis,
        quantity,
        distance,
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType
    )

    return component.features.rectangularPatternFeatures.add(bottomBorderPatternInput)