"""Placement of compact arc menus and speech, in Qt logical screen coordinates."""
from PySide6.QtCore import QPoint, QRect, QSize


def inside(point, size, work):
    return QPoint(max(work.left(), min(point.x(), work.right() + 1 - size.width())),
                  max(work.top(), min(point.y(), work.bottom() + 1 - size.height())))


def arc_offsets(side):
    return {'right': (QPoint(0, 0), QPoint(18, 62), QPoint(0, 124)),
            'left': (QPoint(18, 0), QPoint(0, 62), QPoint(18, 124)),
            'top': (QPoint(0, 18), QPoint(62, 0), QPoint(124, 18)),
            'bottom': (QPoint(0, 0), QPoint(62, 18), QPoint(124, 0))}[side]


def menu_placement(body: QRect, work: QRect):
    gaps = {'right': (work.right() - body.right()) / work.width(),
            'left': (body.left() - work.left()) / work.width(),
            'bottom': (work.bottom() - body.bottom()) / work.height(),
            'top': (body.top() - work.top()) / work.height()}
    nearest = min(gaps, key=gaps.get)
    opposite = {'right': 'left', 'left': 'right', 'top': 'bottom', 'bottom': 'top'}
    preferred = opposite[nearest] if gaps[nearest] < .22 else 'right'
    order = [preferred] + [s for s in sorted(gaps, key=gaps.get, reverse=True) if s != preferred]
    candidates = {
        'right': (QSize(68, 182), QPoint(body.right() + 10, body.center().y() - 91)),
        'left': (QSize(68, 182), QPoint(body.left() - 78, body.center().y() - 91)),
        'top': (QSize(174, 76), QPoint(body.center().x() - 87, body.top() - 86)),
        'bottom': (QSize(174, 76), QPoint(body.center().x() - 87, body.bottom() + 10))}
    ranked = []
    for index, side in enumerate(order):
        size, point = candidates[side]
        rect = QRect(inside(point, size, work), size)
        overlap = rect.intersected(body.adjusted(-4, -4, 4, 4))
        outside = max(0, size.width() - work.width()) + max(0, size.height() - work.height())
        ranked.append((overlap.width() * overlap.height() + outside * 1000, index, side, rect))
    _, _, side, rect = min(ranked, key=lambda row: row[:2])
    return side, rect


def panel_placement(body, menu, size, work):
    union = body.united(menu)
    candidates = [QPoint(union.right() + 10, union.center().y() - size.height() // 2),
                  QPoint(union.left() - size.width() - 10, union.center().y() - size.height() // 2),
                  QPoint(union.center().x() - size.width() // 2, union.top() - size.height() - 10),
                  QPoint(union.center().x() - size.width() // 2, union.bottom() + 10)]
    def score(point):
        rect = QRect(point, size)
        pet_overlap, menu_overlap = rect.intersected(body), rect.intersected(menu)
        return pet_overlap.width() * pet_overlap.height() * 10 + menu_overlap.width() * menu_overlap.height()
    return min((inside(p, size, work) for p in candidates), key=score)


def speech_placement(body, size, work, obstacles=(), *, allow_distant=False):
    candidates = [QPoint(body.center().x() - size.width() // 2, body.top() - size.height() - 8),
                  QPoint(body.left() - size.width() - 8, body.top()),
                  QPoint(body.right() + 8, body.top()),
                  QPoint(body.center().x() - size.width() // 2, body.bottom() + 8)]
    # At corners, the menu may occupy the entire space above the pet.
    # Also try just beyond each obstacle instead of covering a control.
    if allow_distant:
        for obstacle in obstacles:
            candidates.extend((QPoint(body.center().x() - size.width() // 2, obstacle.top() - size.height() - 8),
                               QPoint(body.center().x() - size.width() // 2, obstacle.bottom() + 8)))
    def score(point):
        rect = QRect(point, size)
        overlap = rect.intersected(body)
        area = overlap.width() * overlap.height() * 20
        for obstacle in obstacles:
            overlap = rect.intersected(obstacle)
            area += overlap.width() * overlap.height()
        return area
    return min((inside(p, size, work) for p in candidates), key=score)
