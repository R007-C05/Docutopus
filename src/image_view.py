# This Python file uses the following encoding: utf-8

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsPolygonItem
from PySide6.QtGui import QMouseEvent, QPixmap, QPen, QBrush, QPolygonF, QColor, QTransform
from PySide6.QtCore import Qt, QPointF
import math

class CornerHandle(QGraphicsEllipseItem):
    _FILL_COLOR = QColor(75, 97, 117)
    _BORDER_COLOR = QColor(82, 81, 92)
    def __init__(self, index, view, radius=10):
        super().__init__(-radius, -radius, radius*2, radius*2)

        self.index = index
        self.view = view

        self.setBrush(QBrush(self._FILL_COLOR))
        self.setPen(QPen(self._FILL_COLOR))

        self.setFlags(
            QGraphicsEllipseItem.ItemIsMovable |
            QGraphicsEllipseItem.ItemSendsGeometryChanges |
            QGraphicsEllipseItem.ItemIsSelectable
        )

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            self.view.handle_moved(self.index, self.pos())
        return super().itemChange(change, value)


class ImageView(QGraphicsView):
    MAX_ZOOM = 20
    MIN_ZOOM = -5
    _ZOOM_STEP = 1.1

    _SELECTION_COLOR = QColor(66, 238, 163)
    _MAX_CORNERS = 4
    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.selectionMode = False

        self._zoom = 0

        self.current_image = None
        self.corners = []
        self.marker_items = []
        self.polygon_item = None

    def _ordered_corners(self):
        if len(self.corners) < 3:
            return self.corners

        cx = sum(p.x() for p in self.corners) / len(self.corners)
        cy = sum(p.y() for p in self.corners) / len(self.corners)

        return sorted(
            self.corners,
            key=lambda p: math.atan2(p.y() - cy, p.x() - cx)
        )

    def fit_to_window(self):
        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        self._zoom = 0

    def toggle_selection_mode(self):
        if self.selectionMode:
            self.selectionMode = False
            self.reload_image()
            return
        self.selectionMode = True

        if len(self.corners) > 0:
            self.redraw_markers()

    def save_selection(self):
        if not self.selectionMode or len(self.corners) < self._MAX_CORNERS:
            return
        self.clear_markers()
        self.selectionMode = False

    def _reset_image(self, image):
        self.current_image = image
        self.scene.clear()
        self.scene.addPixmap(self.current_image)
        self.fit_to_window()


    def load_image_from_file(self, path):
        self._reset_image(QPixmap(path))

    def clear_selection(self):
        self.clear_markers()
        self.scene.removeItem(self.polygon_item)
        self.polygon_item = None
        self.corners.clear()


    def reload_image(self, pixmap=None):
        if pixmap:
            self.current_image = pixmap
        self.scene.clear()
        self.scene.addPixmap(self.current_image)

        self.marker_items.clear()
        self.polygon_item = None
        if not self.selectionMode and len(self.corners) == self._MAX_CORNERS:
            self._update_polygon()
            return
        if not self.selectionMode:
            self.corners.clear()
            return
        self.redraw_markers()


    def redraw_markers(self):
        new_corners = self.corners.copy()
        self.corners.clear()
        for corner in new_corners:
            self.add_corner(corner)


    def rotate_image(self, direction):
        if self.current_image is None:
            return
        transform = QTransform().rotate(direction*90)
        rotated = self.current_image.transformed(transform)
        w, h = self.current_image.width(), self.current_image.height()

        new_corners = []
        for point in self.corners:
            x, y = point.x(), point.y()
            if direction == 1:
                new_x = h - y
                new_y = x
            elif direction == -1:
                new_x = y
                new_y = w - x
            else:
                new_x, new_y = x, y
            new_corners.append(QPointF(new_x, new_y))

        self.corners = new_corners
        self.reload_image(rotated)

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

    def _update_polygon(self):
        if len(self.corners) < 2:
            return

        ordered = self._ordered_corners()
        poly = QPolygonF(ordered)
        if self.polygon_item is None:
            self.polygon_item = QGraphicsPolygonItem()
            self.polygon_item.setPen(QPen(self._SELECTION_COLOR, 2))

            fill = QColor(self._SELECTION_COLOR)
            fill.setAlpha(60)
            self.polygon_item.setBrush(QBrush(fill))
            self.scene.addItem(self.polygon_item)

        self.polygon_item.setPolygon(poly)

    def add_corner(self, pos: QPointF):
        if len(self.corners) >= self._MAX_CORNERS or not self.selectionMode:
            return
        self.corners.append(pos)
        w, h = self.current_image.width(), self.current_image.height()
        item = CornerHandle(len(self.corners) - 1, self, 20 * w/h)
        item.setPos(pos)
        self.scene.addItem(item)

        self.marker_items.append(item)
        self._update_polygon()

    def clear_markers(self):
        for item in self.marker_items:
            self.scene.removeItem(item)
        self.marker_items.clear()

    def handle_moved(self, index, new_pos):
       self.corners[index] = new_pos
       self._update_polygon()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.add_corner(scene_pos)
        super().mousePressEvent(event)


    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self._zoom_image(event)
        else:
            super().wheelEvent(event)