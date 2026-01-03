import adsk.core
import os
import math
import traceback

import adsk.fusion
from ...lib import fusionAddInUtils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface

# Command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
CMD_NAME = 'Honeycomb Storage Wall'
CMD_Description = 'A Fusion Add-in Command with a dialog for creating Honeycomb Storage Wall'

# Command will be promoted to the panel.
IS_PROMOTED = True

# Command Button Added to the Solid Create Panel ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'

# Path to Icons
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

design = adsk.fusion.Design.cast(app.activeProduct)

# Create a new sketch on the XY plane
newSketch = None

# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED

# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Honeycomb Storage Wall Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # Input Definitions
    width_input = inputs.addDistanceValueCommandInput('width','Width', adsk.core.ValueInput.createByReal(25.6))
    height_input = inputs.addDistanceValueCommandInput('height','Height', adsk.core.ValueInput.createByReal(25.6))
    
    origin = adsk.core.Point3D.create(0, 0, 0)
    # Use a vector to explicitly set the direction (e.g., Y-axis (0, 1, 0))
    direction_vector = adsk.core.Vector3D.create(0, 1, 0)
    height_input.setManipulator(origin, direction_vector)

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Honeycomb Storage Wall Execute Event')
  
    inputs = args.command.commandInputs
    create_hsw(inputs)

# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Honeycomb Storage Wall Preview Event')
    inputs = args.command.commandInputs

    create_hsw(inputs)

# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')

# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs
    
    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    distance_between_turns = inputs.itemById('distance_between_turns')
    if distance_between_turns.value > 0:
        args.areInputsValid = True
    else:
        args.areInputsValid = False
        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []

def create_hsw(inputs: adsk.core.CommandInputs):
    try:    
        occurence = design.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
       
        component = occurence.component
        component.name = "Honeycomb Storage Wall"

        newSketch = component.sketches.add(component.xYConstructionPlane)
        newSketch.name = "HoneyComb_Base"

        sketch = adsk.fusion.Sketch.cast(app.activeEditObject)

        width_input: adsk.core.ValueCommandInput = inputs.itemById('width')
        width = width_input.value
        height_input: adsk.core.ValueCommandInput = inputs.itemById('height')
        height = height_input.value

        sketchLines = newSketch.sketchCurves.sketchLines
        
        #define center and corner of overall construction boundaries
        centerPoint = adsk.core.Point3D.create(0, 0, 0)
        cornerPoint = adsk.core.Point3D.create(width, height, 0) # Defines corner relative to center

        # Add the rectangle
        rectangle = sketchLines.addTwoPointRectangle(centerPoint, cornerPoint)
        
        for line in rectangle:
            line.isConstruction = True 

        xOffset = 0.0
        yOffset = 0.0

        thickness = 0.8

        innerRadius = 1.00
        radiusOffset = 0.18
        outerRadius = innerRadius+radiusOffset
        innerSideLength = innerRadius * (2*math.tan(math.pi/6))
        outerSideLength = outerRadius * (2*math.tan(math.pi/6))

        xSpacing = outerSideLength*2
        ySpacing = outerRadius*2

        honeycombCenterPoint = adsk.core.Point3D.create(outerSideLength, outerRadius, 0)
        honeycombStarterInnerHexagon = sketchLines.addScribedPolygon(honeycombCenterPoint, 6, math.pi/2, innerRadius, False)
        honeycombStarterOuterHexagon = sketchLines.addScribedPolygon(honeycombCenterPoint, 6, math.pi/2, outerRadius, False)

        extrude = component.features.extrudeFeatures

        honeycombBodyExtrudeFeature = extrude.addSimple(newSketch.profiles.item(1), adsk.core.ValueInput.createByReal(thickness), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        honeycombBody = honeycombBodyExtrudeFeature.bodies.item(0)
        honeycombBody.name = "Honeycomb"            

        #create sketch plane on top of newly extruded honeycomb
        honeycombFacePlane = honeycombBodyExtrudeFeature.endFaces[0]
        facePlaneSketch = component.sketches.add(honeycombFacePlane)
        facePlaneSketch.name = "HoneyComb_Top"

        #project honeycomb inner hexagon into new sketch
        projectedEdges = facePlaneSketch.projectCutEdges(honeycombBodyExtrudeFeature.bodies.item(0))
        connectedCurves = facePlaneSketch.findConnectedCurves(projectedEdges.item(0))

        #create one mm offset hexagon from the inner hexagon
        innerOffset = .1
        honeycombStarterInnerHexagon = facePlaneSketch.sketchCurves.sketchLines.addScribedPolygon(honeycombCenterPoint, 6, math.pi/2, innerRadius+innerOffset, False)

        lipDepth = -.29
        honeycombCut = extrude.addSimple(facePlaneSketch.profiles.item(0), adsk.core.ValueInput.createByReal(lipDepth), adsk.fusion.FeatureOperations.CutFeatureOperation)

        #chamfer new inner edge
        chamferEdgeCollection = adsk.core.ObjectCollection.create()
        chamferEdgeCollection.add(honeycombBody.edges.item(18))
        chamferEdgeCollection.add(honeycombBody.edges.item(19))
        chamferEdgeCollection.add(honeycombBody.edges.item(20))
        chamferEdgeCollection.add(honeycombBody.edges.item(21))
        chamferEdgeCollection.add(honeycombBody.edges.item(22))
        chamferEdgeCollection.add(honeycombBody.edges.item(23))

        innerChamferDistance1 = adsk.core.ValueInput.createByReal(.09)
        innerChamferDistance2 = adsk.core.ValueInput.createByReal(.1)

        innerChamferInput = component.features.chamferFeatures.createInput2()
        innerChamferInput.chamferEdgeSets.addTwoDistancesChamferEdgeSet(chamferEdgeCollection, innerChamferDistance1, innerChamferDistance2, False, True)
        innerChamfer = component.features.chamferFeatures.add(innerChamferInput)

        #chamber the bottom inner edge
        bottomChamferEdgeCollection = adsk.core.ObjectCollection.create()
        bottomChamferEdgeCollection.add(honeycombBody.faces.item(25).edges.item(0))
        bottomChamferEdgeCollection.add(honeycombBody.faces.item(25).edges.item(1))
        bottomChamferEdgeCollection.add(honeycombBody.faces.item(25).edges.item(2))
        bottomChamferEdgeCollection.add(honeycombBody.faces.item(25).edges.item(3))
        bottomChamferEdgeCollection.add(honeycombBody.faces.item(25).edges.item(4))
        bottomChamferEdgeCollection.add(honeycombBody.faces.item(25).edges.item(5))

        innerChamferDistance1 = adsk.core.ValueInput.createByReal(.05)
        innerChamferDistance2 = adsk.core.ValueInput.createByReal(.04)

        bottomChamferInput = component.features.chamferFeatures.createInput2()
        bottomChamferInput.chamferEdgeSets.addTwoDistancesChamferEdgeSet(bottomChamferEdgeCollection, innerChamferDistance1, innerChamferDistance2, False, True)
        bottomChamfer = component.features.chamferFeatures.add(bottomChamferInput)

        #mirror honeycomb body so we have a second one to the upper right of it
        mirrorPlane = honeycombBody.faces.item(25)
        
        entitiesToMirror = adsk.core.ObjectCollection.create()
        entitiesToMirror.add(honeycombBody)

        mirrorInput = component.features.mirrorFeatures.createInput(entitiesToMirror, mirrorPlane)
        mirrorInput.isCombine = False 
        mirrorFeature = component.features.mirrorFeatures.add(mirrorInput)

        #duplicate the first honeycomb with a rectangular pattern
        firstHoneycombCollection = adsk.core.ObjectCollection.create()
        firstHoneycombCollection.add(honeycombBody)

        firstPatternDistanceRaw = 2.36
        secondPatternDistanceRaw = outerSideLength*3
        firstPatternDistance1 = adsk.core.ValueInput.createByReal(firstPatternDistanceRaw)
        firstPatternQuantity1 = adsk.core.ValueInput.createByReal(math.floor(height/firstPatternDistanceRaw))
        secondPatternDistance = adsk.core.ValueInput.createByReal(secondPatternDistanceRaw)
        firstPatternQuantity2 = adsk.core.ValueInput.createByReal(math.floor(width/secondPatternDistanceRaw))

        firstPatternInput = component.features.rectangularPatternFeatures.createInput(firstHoneycombCollection, design.rootComponent.yConstructionAxis, firstPatternQuantity1, firstPatternDistance1, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
        firstPatternInput.setDirectionTwo(design.rootComponent.xConstructionAxis, firstPatternQuantity2, secondPatternDistance)
        firstPattern = component.features.rectangularPatternFeatures.add(firstPatternInput)

        #duplicate the second honeycomb with a rectangular pattern
        secondHoneycombCollection = adsk.core.ObjectCollection.create()
        secondHoneycombCollection.add(mirrorFeature.bodies.item(0))

        secondPatternInput = component.features.rectangularPatternFeatures.createInput(secondHoneycombCollection, design.rootComponent.yConstructionAxis, firstPatternQuantity1, firstPatternDistance1, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
        secondPatternInput.setDirectionTwo(design.rootComponent.xConstructionAxis, firstPatternQuantity2, secondPatternDistance)
        secondPattern = component.features.rectangularPatternFeatures.add(secondPatternInput)

        #combine all the bodies
        allbodiesExceptFirst = adsk.core.ObjectCollection.create()
        count=0
        for body in component.bRepBodies:
            if count != 0:
                allbodiesExceptFirst.add(body)
            count+=1

        combineInput = component.features.combineFeatures.createInput(component.bRepBodies.item(0), allbodiesExceptFirst)
        combineInput.isKeepToolBodies = False
        combineFeature = component.features.combineFeatures.add(combineInput)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
