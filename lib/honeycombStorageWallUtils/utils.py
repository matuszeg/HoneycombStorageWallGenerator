import adsk.core
import adsk.fusion
import math

from .constants import *

def debug_selection_set_for_bodies_edges(body: 'adsk.fusion.BRepBody'):
    # #chamfer bottom
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    count = 0
    for edge in body.edges:
        edge_collection = adsk.core.ObjectCollection.create()
        edge_collection.add(edge)
        design.selectionSets.add(edge_collection.asArray(), f"{body.name}_edge_{count}")
        count += 1

def debug_selection_set_for_bodies_faces(body: 'adsk.fusion.BRepBody'):
    # #chamfer bottom
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    count = 0
    for face in body.faces:
        face_collection = adsk.core.ObjectCollection.create()
        face_collection.add(face)
        design.selectionSets.add(face_collection.asArray(), f"{body.name}_face_{count}")
        count += 1

def create_quarter_comb(
    type: CornerType,
    topPlane:  'adsk.fusion.ConstructionPlane' ,
    component: 'adsk.fusion.Component',
    startingCenterPoint: adsk.core.Point3D
):
    name = ""
    if type == CornerType.TopLeft:
        name = "TopLeft"
    elif type == CornerType.TopRight:
        name = "TopRight"
    elif type == CornerType.BottomRight:
        name = "BottomRight"
    elif type == CornerType.BottomLeft:
        name = "BottomLeft"

    sketchFeature = component.sketches.add(component.xYConstructionPlane)
    sketchFeature.name = "Honeycomb_Corner_" + name

    innerHexagon = sketchFeature.sketchCurves.sketchLines.addScribedPolygon(startingCenterPoint, 6, math.pi / 2,
                                                                            INNER_RADIUS, False)
    outerHexagon = sketchFeature.sketchCurves.sketchLines.addScribedPolygon(startingCenterPoint, 6, math.pi / 2,
                                                                            OUTER_RADIUS, False)


    horizontalSplitLine = sketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        startingCenterPoint,
        adsk.core.Point3D.create(startingCenterPoint.x + SIDE_LENGTH, startingCenterPoint.y)
    )

    xOffset = RADIUS_OFFSET / math.tan(math.pi / 3)

    horizontalInnerSplitLine = sketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        adsk.core.Point3D.create(startingCenterPoint.x + RADIUS_OFFSET, startingCenterPoint.y - RADIUS_OFFSET),
        adsk.core.Point3D.create(startingCenterPoint.x + SIDE_LENGTH - xOffset, startingCenterPoint.y - RADIUS_OFFSET)
    )

    verticalSplitLine = sketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        startingCenterPoint,
        adsk.core.Point3D.create(startingCenterPoint.x, startingCenterPoint.y - VERTICAL_SPACING / 2)
    )

    verticalInnerSplitLine = sketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        adsk.core.Point3D.create(startingCenterPoint.x + RADIUS_OFFSET, startingCenterPoint.y - RADIUS_OFFSET),
        adsk.core.Point3D.create(startingCenterPoint.x + RADIUS_OFFSET, startingCenterPoint.y - VERTICAL_SPACING / 2)
    )

    #grab profiles and extrude
    profileCollection = adsk.core.ObjectCollection.create()
    profileCollection.add(sketchFeature.profiles.item(0))
    profileCollection.add(sketchFeature.profiles.item(1))
    profileCollection.add(sketchFeature.profiles.item(3))
    profileCollection.add(sketchFeature.profiles.item(4))

    extrudeInput = component.features.extrudeFeatures.createInput(profileCollection,
                                                                  adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrudeInput.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(TOTAL_THICKNESS),
                                  adsk.fusion.ExtentDirections.PositiveExtentDirection)
    extrudeFeature = component.features.extrudeFeatures.add(extrudeInput)

    topSketchFeature = component.sketches.add(topPlane)
    topSketchFeature.name = "Honeycomb_CornerTop_" + name

    manualPolyCoords = []

    innerPointTopLeft = adsk.core.Point3D.create(
        startingCenterPoint.x + RADIUS_OFFSET - INNER_OFFSET,
        startingCenterPoint.y - RADIUS_OFFSET + INNER_OFFSET
    )
    innerPointBottomLeft = adsk.core.Point3D.create(
        startingCenterPoint.x + RADIUS_OFFSET - INNER_OFFSET,
        startingCenterPoint.y - VERTICAL_SPACING / 2 + RADIUS_OFFSET - INNER_OFFSET
    )

    innerPointBottomRightXOffset = INNER_OFFSET * math.tan(math.pi / 6)

    innerPointBottomRight = adsk.core.Point3D.create(
        innerHexagon.item(2).endSketchPoint.geometry.x + innerPointBottomRightXOffset,
        innerHexagon.item(2).endSketchPoint.geometry.y - INNER_OFFSET
    )

    # sin(60) = x / .16
    # x = sin(60) * .16
    # x = sin(60) * (.18-.1)*2

    innerPointTopRightXOffset = math.sin(math.pi / 3) * (RADIUS_OFFSET - INNER_OFFSET) * 2

    innerPointTopRight = adsk.core.Point3D.create(
        outerHexagon.item(3).geometry.endPoint.x - innerPointTopRightXOffset,
        innerPointTopLeft.y
    )

    manualPolyCoords.append([
        innerPointTopLeft,
        innerPointBottomLeft
    ])

    manualPolyCoords.append([
        innerPointBottomLeft,
        innerPointBottomRight
    ])

    manualPolyCoords.append([
        innerPointBottomRight,
        innerPointTopRight
    ])

    manualPolyCoords.append([
        innerPointTopRight,
        innerPointTopLeft
    ])

    for coords in manualPolyCoords:
        topSketchFeature.sketchCurves.sketchLines.addByTwoPoints(
            coords[0],
            coords[1],
        )

    bottomBorderCutFeature = component.features.extrudeFeatures.addSimple(
        topSketchFeature.profiles.item(0),
        adsk.core.ValueInput.createByReal(LIP_DEPTH),
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )

    borderBottomChamferEdgeCollection = adsk.core.ObjectCollection.create()

    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(12))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(13))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(14))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(15))

    borderBottomInnerChamferInput = component.features.chamferFeatures.createInput2()
    borderBottomInnerChamferInput.chamferEdgeSets.addTwoDistancesChamferEdgeSet(borderBottomChamferEdgeCollection, INNER_CHAMFER_DISTANCES[0], INNER_CHAMFER_DISTANCES[1], False, True)
    borderBottomInnerChamferFeature = component.features.chamferFeatures.add(borderBottomInnerChamferInput)

    borderBottomChamferEdgeCollection = adsk.core.ObjectCollection.create()

    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(13))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(16))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(25))
    borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(27))

    borderBottomBottomChamferInput = component.features.chamferFeatures.createInput2()
    borderBottomBottomChamferInput.chamferEdgeSets.addTwoDistancesChamferEdgeSet(borderBottomChamferEdgeCollection, BOTTOM_CHAMFER_DISTANCES[0], BOTTOM_CHAMFER_DISTANCES[1], False, True)
    borderBottomBottomChamferFeature = component.features.chamferFeatures.add(borderBottomBottomChamferInput)



    if type == CornerType.BottomRight:
        cornerBody = extrudeFeature.bodies.item(0)
        mirrorPlane = cornerBody.faces.item(17)

        entitiesToMirror = adsk.core.ObjectCollection.create()
        entitiesToMirror.add(cornerBody)

        mirrorInput = component.features.mirrorFeatures.createInput(entitiesToMirror, mirrorPlane)
        mirrorInput.isCombine = False

        mirrorFeature = component.features.mirrorFeatures.add(mirrorInput)

        #remove body we just mirrored from
        removeFeatures = component.features.removeFeatures
        removeFeature = removeFeatures.add(cornerBody)

        #mirror again
        newCornerBody = mirrorFeature.bodies.item(0)
        mirrorPlane = newCornerBody.faces.item(20)

        entitiesToMirror = adsk.core.ObjectCollection.create()
        entitiesToMirror.add(newCornerBody)

        mirrorInput = component.features.mirrorFeatures.createInput(entitiesToMirror, mirrorPlane)
        mirrorInput.isCombine = False

        mirrorFeature = component.features.mirrorFeatures.add(mirrorInput)

        # remove body we just mirrored from
        removeFeatures = component.features.removeFeatures
        removeFeature = removeFeatures.add(newCornerBody)
    if type == CornerType.TopRight:
        cornerBody = extrudeFeature.bodies.item(0)
        debug_selection_set_for_bodies_faces(cornerBody)
        mirrorPlane = cornerBody.faces.item(20)

        entitiesToMirror = adsk.core.ObjectCollection.create()
        entitiesToMirror.add(cornerBody)

        mirrorInput = component.features.mirrorFeatures.createInput(entitiesToMirror, mirrorPlane)
        mirrorInput.isCombine = False

        mirrorFeature = component.features.mirrorFeatures.add(mirrorInput)

        #remove body we just mirrored from
        removeFeatures = component.features.removeFeatures
        removeFeature = removeFeatures.add(cornerBody)

def create_half_comb(
    type: BorderType,
    topPlane: 'adsk.fusion.ConstructionPlane',
    component: 'adsk.fusion.Component',
    startingCenterPoint: adsk.core.Point3D
):
    name = ""
    rotationFactor = 0
    verticalSplit = False

    if type == BorderType.BOTTOM:
        name = "Bottom"
        rotationFactor = 0
        verticalSplit = False
    elif type == BorderType.TOP:
        name = "Top"
        verticalSplit = False
        rotationFactor = math.pi
    elif type == BorderType.LEFT:
        name = "Left"
        rotationFactor = 0
        verticalSplit = True
    elif type == BorderType.RIGHT:
        name = "Right"
        rotationFactor = math.pi
        verticalSplit = True

    sketchFeature = component.sketches.add(component.xYConstructionPlane)
    sketchFeature.name = "Honeycomb_Border_" + name

    #create border sketch profiles
    innerHexagon = sketchFeature.sketchCurves.sketchLines.addScribedPolygon(startingCenterPoint, 6, math.pi/2, INNER_RADIUS, False)
    outerHexagon = sketchFeature.sketchCurves.sketchLines.addScribedPolygon(startingCenterPoint, 6, math.pi/2, OUTER_RADIUS, False)

    splitLineSketchPoints = []
    innerSplitLineSketchPoints = []

    if verticalSplit:
        # Add the midpoint constraint:
        # Constrains the 'endSketchPoint' of line2 to the midpoint of line1
        bottomMidPoint = adsk.core.Point3D.create(
            (outerHexagon.item(2).startSketchPoint.geometry.x + outerHexagon.item(2).endSketchPoint.geometry.x) / 2.0,
            (outerHexagon.item(2).startSketchPoint.geometry.y + outerHexagon.item(2).endSketchPoint.geometry.y) / 2.0,
            0
        )
        bottomMidPointSketch = sketchFeature.sketchPoints.add(bottomMidPoint)

        topMidPoint = adsk.core.Point3D.create(
            (outerHexagon.item(5).startSketchPoint.geometry.x + outerHexagon.item(5).endSketchPoint.geometry.x) / 2.0,
            (outerHexagon.item(5).startSketchPoint.geometry.y + outerHexagon.item(5).endSketchPoint.geometry.y) / 2.0,
            0
        )
        topMidPointSketch = sketchFeature.sketchPoints.add(topMidPoint)

        bottomMidPointFeature = sketchFeature.geometricConstraints.addMidPoint(bottomMidPointSketch, outerHexagon.item(2))
        topMidPointFeature = sketchFeature.geometricConstraints.addMidPoint(topMidPointSketch, outerHexagon.item(5))

        splitLineSketchPoints.append(topMidPointSketch)
        splitLineSketchPoints.append(bottomMidPointSketch)
    else:
        splitLineSketchPoints.append(outerHexagon.item(0).endSketchPoint)
        splitLineSketchPoints.append(outerHexagon.item(3).endSketchPoint)

        innerSplitLineSketchPoints.append(innerHexagon.item(0).endSketchPoint)
        innerSplitLineSketchPoints.append(innerHexagon.item(3).endSketchPoint)

    splitLine = sketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        splitLineSketchPoints[0],
        splitLineSketchPoints[1]
    )
    

    innerLinePoints = []

    if verticalSplit:
        xOffset = RADIUS_OFFSET
        yOffset = RADIUS_OFFSET

        innerLinePoints.append(adsk.core.Point3D.create(splitLineSketchPoints[0].geometry.x + xOffset, splitLineSketchPoints[0].geometry.y - yOffset, 0))
        innerLinePoints.append(adsk.core.Point3D.create(splitLineSketchPoints[1].geometry.x + xOffset, splitLineSketchPoints[1].geometry.y + yOffset, 0))
    else:
        xOffset = RADIUS_OFFSET/math.tan(math.pi/3)
        yOffset = RADIUS_OFFSET

        innerLinePoints.append(adsk.core.Point3D.create(innerSplitLineSketchPoints[0].geometry.x + xOffset, innerSplitLineSketchPoints[0].geometry.y + yOffset, 0))
        innerLinePoints.append(adsk.core.Point3D.create(innerSplitLineSketchPoints[1].geometry.x - xOffset, innerSplitLineSketchPoints[1].geometry.y + yOffset, 0))

    innerLine = sketchFeature.sketchCurves.sketchLines.addByTwoPoints(
        innerLinePoints[0],
        innerLinePoints[1]
    )

    #grab profiles and extrude upwards
    profileCollection = adsk.core.ObjectCollection.create()
    profileCollection.add(sketchFeature.profiles.item(2))
    profileCollection.add(sketchFeature.profiles.item(4))

    extrudeInput = component.features.extrudeFeatures.createInput(profileCollection, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrudeInput.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(TOTAL_THICKNESS), adsk.fusion.ExtentDirections.PositiveExtentDirection)
    extrudeFeature = component.features.extrudeFeatures.add(extrudeInput)

    topSketchFeature = component.sketches.add(topPlane)
    topSketchFeature.name = "Honeycomb_BorderTop_" + name

    topCornerOffsetX = INNER_OFFSET / math.tan(math.pi / 3)

    manualPolyCoords = []

    if verticalSplit:
        firstPoint = adsk.core.Point3D.create(
            innerLine.startSketchPoint.geometry.x - INNER_OFFSET,
            innerLine.startSketchPoint.geometry.y + INNER_OFFSET
        )
        secondPoint = adsk.core.Point3D.create(
            innerLine.endSketchPoint.geometry.x - INNER_OFFSET,
            innerLine.endSketchPoint.geometry.y - INNER_OFFSET
        )

        thirdPoint = adsk.core.Point3D.create(
            innerHexagon.item(2).endSketchPoint.geometry.x + topCornerOffsetX,
            innerHexagon.item(2).endSketchPoint.geometry.y - INNER_OFFSET
        )

        rightXOffset = INNER_OFFSET / math.cos(math.pi/6)

        fourthPoint = adsk.core.Point3D.create(
            innerHexagon.item(3).endSketchPoint.geometry.x + rightXOffset,
            innerHexagon.item(3).endSketchPoint.geometry.y
        )

        fifthPoint = adsk.core.Point3D.create(
            innerHexagon.item(4).endSketchPoint.geometry.x + topCornerOffsetX,
            innerHexagon.item(4).endSketchPoint.geometry.y + INNER_OFFSET
        )

        manualPolyCoords.append([
            firstPoint,
            secondPoint
        ])

        manualPolyCoords.append([
            secondPoint,
            thirdPoint
        ])

        manualPolyCoords.append([
            thirdPoint,
            fourthPoint
        ])

        manualPolyCoords.append([
            fourthPoint,
            fifthPoint
        ])

        manualPolyCoords.append([
            fifthPoint,
            firstPoint
        ])

    else:

        cornerOffset = math.sqrt((INNER_OFFSET * 2) * (INNER_OFFSET * 2) - INNER_OFFSET * INNER_OFFSET)

        manualPolyBottomLeft = adsk.core.Point3D.create(innerLinePoints[0].x-cornerOffset, innerLinePoints[0].y - INNER_OFFSET)
        manualPolyBottomRight = adsk.core.Point3D.create(innerLinePoints[1].x+cornerOffset, innerLinePoints[1].y - INNER_OFFSET)
        
        manualPolyTopLeft = adsk.core.Point3D.create(
            innerHexagon.item(5).endSketchPoint.geometry.x-topCornerOffsetX,
            innerHexagon.item(5).endSketchPoint.geometry.y+INNER_OFFSET
        )

        manualPolyTopRight = adsk.core.Point3D.create(
            innerHexagon.item(4).endSketchPoint.geometry.x+topCornerOffsetX,
            innerHexagon.item(4).endSketchPoint.geometry.y+INNER_OFFSET
        )

        manualPolyCoords.append([manualPolyBottomLeft,manualPolyBottomRight])
        manualPolyCoords.append([manualPolyBottomLeft,manualPolyTopLeft])
        manualPolyCoords.append([manualPolyTopLeft,manualPolyTopRight])
        manualPolyCoords.append([manualPolyTopRight,manualPolyBottomRight])

    for coords in manualPolyCoords:
        topSketchFeature.sketchCurves.sketchLines.addByTwoPoints(
            coords[0],
            coords[1],
        )

    #extrude down to start the lip
    bottomBorderCutFeature = component.features.extrudeFeatures.addSimple(
        topSketchFeature.profiles.item(0),
        adsk.core.ValueInput.createByReal(LIP_DEPTH),
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    
    #chamfer new inner edge
    borderBottomChamferEdgeCollection = adsk.core.ObjectCollection.create()

    if verticalSplit:
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(15))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(16))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(17))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(18))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(19))
    else:
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(12))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(13))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(14))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(15))

    borderBottomInnerChamferInput = component.features.chamferFeatures.createInput2()
    borderBottomInnerChamferInput.chamferEdgeSets.addTwoDistancesChamferEdgeSet(borderBottomChamferEdgeCollection, INNER_CHAMFER_DISTANCES[0], INNER_CHAMFER_DISTANCES[1], False, True)
    borderBottomInnerChamferFeature = component.features.chamferFeatures.add(borderBottomInnerChamferInput)

    borderBottomChamferEdgeCollection = adsk.core.ObjectCollection.create()

    if verticalSplit:
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(16))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(19))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(21))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(33))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(34))
    else:
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(13))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(16))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(25))
        borderBottomChamferEdgeCollection.add(extrudeFeature.bodies[0].edges.item(27))

    borderBottomBottomChamferInput = component.features.chamferFeatures.createInput2()
    borderBottomBottomChamferInput.chamferEdgeSets.addTwoDistancesChamferEdgeSet(borderBottomChamferEdgeCollection, BOTTOM_CHAMFER_DISTANCES[0], BOTTOM_CHAMFER_DISTANCES[1], False, True)
    borderBottomBottomChamferFeature = component.features.chamferFeatures.add(borderBottomBottomChamferInput)

    if rotationFactor != 0:
        rotationTransform = adsk.core.Matrix3D.create()
        rotationTransform.setToRotation(rotationFactor, adsk.core.Vector3D.create(0,0,1), startingCenterPoint)

        entities = adsk.core.ObjectCollection.create()
        entities.add(extrudeFeature.bodies[0])
        
        moveFeatureInput =  component.features.moveFeatures.createInput(entities, rotationTransform)

        # Add the move feature to the design
        component.features.moveFeatures.add(moveFeatureInput)

    extrudeFeature.bodies[0].name =  "Honeycomb_Border_" + name
    return extrudeFeature.bodies[0]

def duplicate_border_body(
        component: adsk.fusion.Component,
        axis: 'adsk.fusion.ConstructionAxis',
        body: adsk.fusion.BRepBody,
        quantity: int,
        distance: adsk.core.ValueInput
):
    bottomBorderCollection = adsk.core.ObjectCollection.create()
    bottomBorderCollection.add(body)

    bottomBorderPatternInput = component.features.rectangularPatternFeatures.createInput(
        bottomBorderCollection,
        axis,
        adsk.core.ValueInput.createByReal(quantity),
        distance,
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType
    )

    bottomBorderPatternInput.setDirectionTwo(component.xConstructionAxis, adsk.core.ValueInput.createByReal(1), adsk.core.ValueInput.createByReal(0.0))

    return component.features.rectangularPatternFeatures.add(bottomBorderPatternInput)