# =============================================================================
# find_fastener_nodes_by_curve.py
#
# Description: Finds fastener nodes along curves and optionally moves them
#              to the closest point on the curve centerline.
#
# Author:      Nicholas Kmett
# Created:     2026-05-08
# Modified:    2026-05-09
# =============================================================================


import math
from femap_connect import connect
App, feConstants = connect()


def dot(a, b):
    """Returns the dot product of two tuples."""
    return sum(x*y for x, y in zip(a, b))


def subtract(a, b):
    """Returns element-wise subtraction of two tuples (a - b)."""
    return tuple(x - y for x, y in zip(a, b))


def to_tuple(point):
    """Converts a Femap point object to an (x, y, z) tuple."""
    return point.x, point.y, point.z


def main():
    # Setup
    App.feAppUndoCheckpoint("Undo Python Script")
    App.feAppMessageClear()
    App.feAppMessage(feConstants.FCM_WARNING, "API Started: find_fastener_nodes_by_curve")

    feGroupSet = App.feSet
    feElemSet = App.feSet
    feElemBypassSet = App.feSet
    feCurveSet = App.feSet
    feCurveSet2 = App.feSet
    feNodeSet = App.feSet
    fePointSet = App.feSet
    fePointsOnCurveSet = App.feSet
    feGroup = App.feGroup
    feCurve = App.feCurve
    fePoint1 = App.fePoint
    fePoint2 = App.fePoint
    feNewPoint = App.fePoint
    feNode = App.feNode

    # Reset all element colors in model
    feElemSet.AddAll(feConstants.FT_ELEM)
    App.feModifyColor(feConstants.FT_ELEM, feElemSet.ID, feConstants.FCL_WHITE, 0)
    feElemSet.clear()

    # Reset all node colors in model
    feNodeSet.AddAll(feConstants.FT_NODE)
    App.feModifyColor(feConstants.FT_NODE, feNodeSet.ID, feConstants.FCL_LIME, 0)
    feNodeSet.clear()

    App.feViewRegenerate(0)

    # User select groups with curves to find fastener nodes near
    App.feAppBringToTop(True, 0)
    rc, n = feGroupSet.SelectID(feConstants.FT_GROUP, "Select group containing curves to find fastener nodes.")
    if rc == feConstants.FE_CANCEL:
        App.feAppMessage(feConstants.FCM_ERROR, "No group selected. Exiting.")
        return
    
    feGroup.Get(n)
    feCurveSet.AddGroup(feConstants.FT_CURVE, feGroup.ID)
    App.feAppMessage(feConstants.FCM_NORMAL, "Using group " + feGroup.title + " to find fastener nodes.")

    # User set search tolerance (acceptable distance from center of fastener curve to closest node)
    rc, search_tolerance = App.feGetReal("Specify Search Tolerance", 0, 100)
    if rc == feConstants.FE_CANCEL:
        App.feAppMessage(feConstants.FCM_ERROR, "No search tolerance specified. Exiting...")
        feCurveSet.clear()
        return
    App.feAppMessage(feConstants.FCM_NORMAL, "Finding nodes within " + str(search_tolerance) + " inches of curve centerlines.")

    # User option to project nodes on to fastener centerlines
    rc = App.feAppMessageBox(3, "Move Fastener Nodes to CL Location?")
    if rc == feConstants.FE_OK:
        move_nodes = True
        App.feAppMessage(feConstants.FCM_NORMAL, "Nodes are being projected on to fastener centerlines.")
    elif rc == feConstants.FE_FAIL:
        move_nodes = False
        App.feAppMessage(feConstants.FCM_NORMAL, "Nodes will NOT be moved to fastener centerlines.")
    elif rc == feConstants.FE_CANCEL:
        App.feAppMessage(feConstants.FCM_ERROR, "No option selected. Exiting...")
        feCurveSet.clear()
        return

    App.feAppLock

    while feCurveSet.Next():
        feCurve.Get(feCurveSet.CurrentID)
        rc, box = feCurve.BoundingBox()
        
        # Calculate midpoint of curve bounding box to use as reference point for finding closest node
        mid_loc = [
            (box[0] + box[3]) / 2,
            (box[1] + box[4]) / 2,
            (box[2] + box[5]) / 2
        ]
        
        feNode.GetClosest(mid_loc)

        # Calculate distance from closest node to midpoint of curve bounding box
        distance = math.dist(mid_loc, (feNode.x, feNode.y, feNode.z))

        if distance <= search_tolerance:
            feNodeSet.Add(feNode.ID)
            feCurveSet2.Add(feCurve.ID)
            rc, start_point, end_point = feCurve.EndPoints()
            fePoint1.Get(start_point)
            fePoint2.Get(end_point)
            fePointsOnCurveSet.Add(start_point)
            fePointsOnCurveSet.Add(end_point)

            if move_nodes:
                v = subtract(to_tuple(fePoint2), to_tuple(fePoint1))  # Vector along curve from start to end point
                w = subtract(to_tuple(feNode), to_tuple(fePoint1))  # Vector from start point to node location
                t = dot(w, v) / dot(v, v)  # Parameter t for projecting node onto curve centerline

                # Calculate projected point Q on curve centerline corresponding to node location
                Q = [
                    fePoint1.x + t * v[0],
                    fePoint1.y + t * v[1],
                    fePoint1.z + t * v[2]
                ]

                feNewPoint.x = Q[0]
                feNewPoint.y = Q[1]
                feNewPoint.z = Q[2]
                feNewPoint.Put(feNewPoint.NextEmptyID())
                fePointSet.Add(feNewPoint.ID)
                App.feMoveTo(feConstants.FT_NODE, -1*feNode.ID, feNewPoint.x, feNewPoint.y, feNewPoint.z, True, True, True, 0, False)
    
    # Count fastener nodes found
    count_fasteners = feNodeSet.Count()

    if count_fasteners == 0:
        App.feAppMessage(feConstants.FCM_NORMAL, "No fastener nodes found. Exiting...")

        feGroupSet.clear()
        feElemSet.clear()
        feElemBypassSet.clear()
        feCurveSet.clear()
        feCurveSet2.clear()
        feNodeSet.clear()
        fePointSet.clear()
        fePointsOnCurveSet.clear()

        App.feAppUnlock()
        App.feViewRegenerate(0)
        App.feAppMessage(feConstants.FCM_WARNING, "Script complete.")
        return
    else:
        # Color fastener nodes red
        App.feModifyColor(feConstants.FT_NODE, feNodeSet.ID, feConstants.FCL_RED, 0)

        # Create new group with found fastener nodes
        feGroupSet.clear()
        feGroupSet.AddAll(feConstants.FT_GROUP)
        group_ID = feGroupSet.Last() + 1
        feGroup.clear()
        feGroup.title = "Fasteners"
        feGroup.Put(group_ID)
        feGroup.Get(group_ID)

        # Add fastener nodes to group
        feGroup.SetAdd(feConstants.FT_NODE, feNodeSet.ID)

        # Add fastener node bearing elements to group
        feElemSet.AddSetRule(feNodeSet.ID, feConstants.FGD_ELEM_BYNODE)
        App.feModifyColor(feConstants.FT_ELEM, feElemSet.ID, 115, 0)
        feGroup.SetAdd(feConstants.FT_ELEM, feElemSet.ID)
        feNodeSet.clear()

        # Add fastener node bypass elements to group
        feNodeSet.AddSetRule(feElemSet.ID, feConstants.FGD_NODE_ONELEM)
        feElemBypassSet.AddSetRule(feNodeSet.ID, feConstants.FGD_ELEM_BYNODE)
        feElemBypassSet.AddNewRemoveCommonSet(feElemSet.ID)
        App.feModifyColor(feConstants.FT_ELEM, feElemBypassSet.ID, 69, 0)
        feGroup.SetAdd(feConstants.FT_ELEM, feElemBypassSet.ID)
        feNodeSet.clear()
        feElemSet.clear()
        feElemBypassSet.clear()

        # Add curves to group
        feGroup.SetAdd(feConstants.FT_CURVE, feCurveSet2.ID)

        # Add curve points to group
        feGroup.SetAdd(feConstants.FT_POINT, fePointsOnCurveSet.ID)

        # Add new point to group
        App.feModifyColor(feConstants.FT_POINT, fePointSet.ID, feConstants.FCL_ORANGE, 0)
        feGroup.SetAdd(feConstants.FT_POINT, fePointSet.ID)

        # Update group
        feGroup.Put(group_ID)

        # Clean up
        feGroupSet.clear()
        feElemSet.clear()
        feElemBypassSet.clear()
        feCurveSet.clear()
        feCurveSet2.clear()
        feNodeSet.clear()
        fePointSet.clear()
        fePointsOnCurveSet.clear()

        App.feAppMessage(feConstants.FCM_NORMAL, "Found " + str(count_fasteners) + " fasteners.")
        App.feAppUnlock()
        App.feViewRegenerate(0)
        App.feAppMessage(feConstants.FCM_WARNING, "Script complete.")


if __name__ == "__main__":
    main()