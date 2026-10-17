"""Bubble UI placement in Qt logical coordinates, including negative monitors."""
from PySide6.QtCore import QPoint, QRect, QSize


def inside(point, size, work):
    return QPoint(max(work.left(), min(point.x(), work.right() + 1 - size.width())),
                  max(work.top(), min(point.y(), work.bottom() + 1 - size.height())))


def menu_placement(body: QRect, work: QRect):
    vertical, horizontal = QSize(68, 228), QSize(228, 76)
    gap = 10
    candidates = (
        ("right", vertical, QPoint(body.right() + gap, body.center().y() - 114)),
        ("left", vertical, QPoint(body.left() - gap - 68, body.center().y() - 114)),
        ("top", horizontal, QPoint(body.center().x() - 114, body.top() - gap - 76)),
        ("bottom", horizontal, QPoint(body.center().x() - 114, body.bottom() + gap)))
    ranked = []
    for order, (side, size, point) in enumerate(candidates):
        point = inside(point, size, work)
        rect = QRect(point, size)
        overlap = rect.intersected(body.adjusted(-5, -5, 5, 5))
        penalty = overlap.width() * overlap.height()
        ranked.append((penalty, order, side, rect))
    _, _, side, rect = min(ranked, key=lambda row: row[:2])
    return side, rect


def panel_placement(body, menu, size, work):
    union = body.united(menu)
    candidates = [QPoint(union.right() + 12, union.center().y() - size.height() // 2),
                  QPoint(union.left() - size.width() - 12, union.center().y() - size.height() // 2),
                  QPoint(union.center().x() - size.width() // 2, union.top() - size.height() - 12),
                  QPoint(union.center().x() - size.width() // 2, union.bottom() + 12)]
    def score(point):
        rect = QRect(point, size)
        pet_overlap, menu_overlap = rect.intersected(body), rect.intersected(menu)
        return (pet_overlap.width() * pet_overlap.height() * 10
                + menu_overlap.width() * menu_overlap.height())
    points = [inside(p, size, work) for p in candidates]
    return min(points, key=score)
