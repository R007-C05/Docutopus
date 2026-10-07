# This Python file uses the following encoding: utf-8

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsPolygonItem
from PySide6.QtGui import QPen, QBrush, QPolygonF, QColor
from PySide6.QtCore import Qt, QPointF
from document_image import DocumentImage, Point, ScanMode
import math

class CornerHandle(QGraphicsEllipseItem):
    _FILL_COLOR = QColor(75, 97, 117)
    _BORDER_COLOR = QColor(82, 81, 92)

    def __init__(self, group, index, view, radius=10):
        super().__init__(-radius, -radius, radius * 2, radius * 2)

        self.group = group
        self.index = index
        self.view = view

        self.setBrush(QBrush(self._FILL_COLOR))
        self.setPen(QPen(self._FILL_COLOR))
        self.setZValue(10)

        self.setFlags(
            QGraphicsEllipseItem.ItemIsMovable |
            QGraphicsEllipseItem.ItemSendsGeometryChanges |
            QGraphicsEllipseItem.ItemIsSelectable
        )

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            self.view.handle_moved(self.group, self.index, self.pos())
        return super().itemChange(change, value)


class ImageView(QGraphicsView):
    MAX_ZOOM = 20
    MIN_ZOOM = -5
    _ZOOM_STEP = 1.1

    _SELECTION_COLOR = QColor(66, 238, 163)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.selectionMode = False

        self._zoom = 0

        self.current_image: DocumentImage | None = None
        self.marker_items = []     # CornerHandle items currently in the scene
        self.polygon_items = {}    # group index -> QGraphicsPolygonItem

    # Helpers
    @staticmethod
    def _order_corners(corners):
        if len(corners) < 3:
            return corners

        cx = sum(p.x for p in corners) / len(corners)
        cy = sum(p.y for p in corners) / len(corners)

        return sorted(corners, key=lambda p: math.atan2(p.y - cy, p.x - cx))

    def _is_ocr_mode(self):
        return (
            self.current_image is not None
            and self.current_image.scan_mode == ScanMode.OCR
        )

    def _groups(self):
        if self.current_image is None:
            return []
        if self._is_ocr_mode():
            return self.current_image.text_selections
        return [self.current_image.corners]

    def _discard_incomplete(self):
        if self.current_image is None:
            return
        full = DocumentImage.MAX_CORNERS
        if self._is_ocr_mode():
            selections = self.current_image.text_selections
            selections[:] = [s for s in selections if len(s) == full]
        elif len(self.current_image.corners) != full:
            self.current_image.corners.clear()

    def _rebuild_scene(self):
        self.scene.clear()
        self.marker_items.clear()
        self.polygon_items.clear()

        if self.current_image is None:
            return

        if not self.selectionMode:
            self._discard_incomplete()

        self.scene.addPixmap(self.current_image.pixmap())

        for group_idx, points in enumerate(self._groups()):
            if self.selectionMode:
                for index, point in enumerate(points):
                    self._add_handle(group_idx, index, point)
            self._update_polygon(group_idx)

    # View / image management
    def fit_to_window(self):
        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        self._zoom = 0

    def _reset_image(self, image):
        self.current_image = image
        self._rebuild_scene()
        self.fit_to_window()

    def set_mode(self, scan_mode: ScanMode):
        if self.current_image is None:
            return
        # An unfinished selection of the mode we are leaving is dropped;
        # completed selections of BOTH modes stay stored in the image.
        if self.selectionMode:
            self.selectionMode = False
        self._discard_incomplete()
        self.current_image.set_mode(scan_mode)
        self._reset_image(self.current_image)

    def load_new_image(self, document_image):
        self._reset_image(document_image)
        self.set_mode(document_image.scan_mode)

    def clear_image(self):
        self.scene.clear()
        self.marker_items.clear()
        self.polygon_items.clear()
        self.current_image = None

    def reload_image(self):
        self._rebuild_scene()

    # Selection handling
    def toggle_selection_mode(self):
        if not self.current_image:
            return

        if self.selectionMode:
            self.selectionMode = False
            self.reload_image()   # drops unfinished groups, hides handles
            return

        self.selectionMode = True
        self.redraw_markers()

    def save_selection(self):
        if not self.selectionMode or self.current_image is None:
            return
        full = DocumentImage.MAX_CORNERS
        # Need at least one finished polygon (Document: the 4 corners).
        if not any(len(g) == full for g in self._groups()):
            return
        self.selectionMode = False
        self.reload_image()       # discards a trailing unfinished group

    def clear_selection(self):
        if self.current_image is None:
            return
        if self._is_ocr_mode():
            self.current_image.text_selections.clear()
        else:
            self.current_image.corners.clear()
        self._rebuild_scene()

    def remove_last_selection(self):
        if self._is_ocr_mode() and self.current_image.text_selections:
            self.current_image.text_selections.pop()
            self._rebuild_scene()

    def add_corner(self, pos: Point):
        if self.current_image is None or not self.selectionMode:
            return

        groups = self._groups()
        full = DocumentImage.MAX_CORNERS

        # OCR mode: when the last selection is complete, start a new one.
        if self._is_ocr_mode() and (not groups or len(groups[-1]) >= full):
            groups.append([])

        group_idx = len(groups) - 1
        group = groups[group_idx]
        if len(group) >= full:    # Document mode: already has its 4 corners
            return

        group.append(pos)
        self._add_handle(group_idx, len(group) - 1, pos)
        self._update_polygon(group_idx)

    def _add_handle(self, group_idx, index, pos):
        w, h = self.current_image.width(), self.current_image.height()
        item = CornerHandle(group_idx, index, self, 5 + 0.005 * min(w, h))
        item.setPos(QPointF(pos.x, pos.y))
        self.scene.addItem(item)
        self.marker_items.append(item)

    def clear_markers(self):
        for item in self.marker_items:
            self.scene.removeItem(item)
        self.marker_items.clear()

    def redraw_markers(self):
        if self.current_image is None:
            return
        self.clear_markers()
        for group_idx, points in enumerate(self._groups()):
            for index, point in enumerate(points):
                self._add_handle(group_idx, index, point)
            self._update_polygon(group_idx)

    def handle_moved(self, group_idx, index, new_pos):
        groups = self._groups()
        if group_idx >= len(groups) or index >= len(groups[group_idx]):
            return
        groups[group_idx][index] = Point(new_pos.x(), new_pos.y())
        self._update_polygon(group_idx)

    def _update_polygon(self, group_idx):
        if self.current_image is None:
            return
        groups = self._groups()
        if group_idx >= len(groups) or len(groups[group_idx]) < 2:
            return

        ordered = ImageView._order_corners(groups[group_idx])
        poly = QPolygonF([QPointF(p.x, p.y) for p in ordered])

        item = self.polygon_items.get(group_idx)
        if item is None:
            item = QGraphicsPolygonItem()
            item.setPen(QPen(self._SELECTION_COLOR, 2))

            fill = QColor(self._SELECTION_COLOR)
            fill.setAlpha(60)
            item.setBrush(QBrush(fill))
            item.setZValue(5)
            self.scene.addItem(item)
            self.polygon_items[group_idx] = item

        item.setPolygon(poly)

    # Rotation / zoom / events
    def rotate_image(self, direction):
        if self.current_image is None:
            return

        w, h = self.current_image.width(), self.current_image.height()
        self.current_image.rotate(direction)

        def rotate_point(point):
            x, y = point.x, point.y
            if direction == 1:
                return Point(h - y, x)
            if direction == -1:
                return Point(y, w - x)
            return Point(x, y)

        # Rotate the stored points of BOTH modes so the inactive one stays aligned.
        corners = self.current_image.corners
        corners[:] = [rotate_point(p) for p in corners]
        selections = self.current_image.text_selections
        selections[:] = [[rotate_point(p) for p in sel] for sel in selections]

        self.reload_image()

    def _zoom_image(self, event):
        if self.current_image is None:
            return

        if event.angleDelta().y() > 0:
            factor = self._ZOOM_STEP
            self._zoom += 1
        elif event.angleDelta().y() < 0:
            factor = 1 / self._ZOOM_STEP
            self._zoom -= 1
        else:
            return

        if self._zoom < self.MIN_ZOOM or self._zoom > self.MAX_ZOOM:
            return

        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Clicking an existing handle drags it; it must not start a new point.
            if not isinstance(self.itemAt(event.pos()), CornerHandle):
                scene_pos = self.mapToScene(event.pos())
                self.add_corner(Point(scene_pos.x(), scene_pos.y()))
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self._zoom_image(event)
        else:
            super().wheelEvent(event)