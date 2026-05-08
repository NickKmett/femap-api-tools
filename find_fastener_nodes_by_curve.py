from femap_connect import connect
App, feConstants = connect()

App.feAppUndoCheckpoint("Undo Python Script")

App.feAppMessageClear()
App.feAppMessage(feConstants.FCM_NORMAL, "API Started: find_fastener_nodes_by_curve")

def main():
    feElemSet = App.feSet
    feElemBypassSet = App.feSet
    fePointSet = App.feSet
    fePointsOnCurveSet = App.feSet
    feGroup = App.feGroup
    feCurve = App.feCurve
    fePoint1 = App.fePoint
    fePoint2 = App.fePoint
    feNewPoint = App.fePoint
    feNode = App.feNode
