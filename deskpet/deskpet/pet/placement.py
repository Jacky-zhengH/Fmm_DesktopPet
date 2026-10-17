"""Visible-content placement in Qt logical screen coordinates."""
from dataclasses import dataclass
from PySide6.QtCore import QPoint, QRect, QRectF

SNAP_DISTANCE = 24
EDGES = ("bottom", "top", "left", "right")


@dataclass(frozen=True)
class Surface:
    edge: str
    coordinate: float
    reserved: bool = False


def surfaces(screen: QRect, available: QRect):
    """Prefer reserved-area boundaries; fall back to screen edges if undetectable."""
    return [Surface("bottom", available.bottom() + 1, available.bottom() < screen.bottom()),
            Surface("top", available.top(), available.top() > screen.top()),
            Surface("left", available.left(), available.left() > screen.left()),
            Surface("right", available.right() + 1, available.right() < screen.right())]


def distance(position: QPoint, visible: QRectF, surface: Surface):
    world = visible.translated(position)
    value = {"bottom": world.bottom(), "top": world.top(),
             "left": world.left(), "right": world.right()}[surface.edge]
    return abs(value - surface.coordinate)


def nearest_surface(position, visible, screen, available, threshold=SNAP_DISTANCE):
    candidates = surfaces(screen, available)
    world = visible.translated(position)
    def crossed(item):
        return {"bottom": world.bottom() >= item.coordinate, "top": world.top() <= item.coordinate,
                "left": world.left() <= item.coordinate, "right": world.right() >= item.coordinate}[item.edge]
    candidates = [item for item in candidates if threshold is None or crossed(item)
                  or distance(position, visible, item) <= threshold]
    # At a taskbar corner prefer the taskbar over an equally close screen side.
    return min(candidates, key=lambda item: (not item.reserved, distance(position, visible, item))) if candidates else None


def constrain(position: QPoint, visible: QRectF, screen: QRect):
    """Keep the visible body on-screen; transparent window padding may cross it."""
    x_min, x_max = screen.left() - visible.left(), screen.right() + 1 - visible.right()
    y_min, y_max = screen.top() - visible.top(), screen.bottom() + 1 - visible.bottom()
    x = max(x_min, min(position.x(), max(x_min, x_max)))
    y = max(y_min, min(position.y(), max(y_min, y_max)))
    return QPoint(round(x), round(y))


def attach(position, visible, screen, surface):
    x, y = position.x(), position.y()
    if surface.edge == "bottom":
        y = surface.coordinate - visible.bottom()
    elif surface.edge == "top":
        y = surface.coordinate - visible.top()
    elif surface.edge == "left":
        x = surface.coordinate - visible.left()
    elif surface.edge == "right":
        x = surface.coordinate - visible.right()
    return constrain(QPoint(round(x), round(y)), visible, screen)
