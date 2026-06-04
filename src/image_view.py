# This Python file uses the following encoding: utf-8

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsPolygonItem
from PySide6.QtGui import QMouseEvent, QPixmap, QPen, QBrush, QPolygonF, QColor
from PySide6.QtCore import Qt, QPointF


class CornerHandle(QGraphicsEllipseItem):
    _MARKER_COLOR = QColor(75, 97, 117)
    def __init__(self, index, view, radius=10):
        super().__init__(-radius, -radius, radius*2, radius*2)

        self.index = index
        self.view = view

        self.setBrush(QBrush(self._MARKER_COLOR))
        self.setPen(QPen(Qt.black))

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

        self._zoom = 0

        self.current_image = None
        self.corners = []
        self.marker_items = []
        self.polygon_item = None


    def fit_to_window(self):
        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        self._zoom = 0

    def _reset_image(self, image):
        self.current_image = image
        self.scene.clear()
        self.scene.addPixmap(self.current_image)
        self.fit_to_window()


    def load_image_from_file(self, path):
        self._reset_image(QPixmap(path))

    def reload_image(self, pixmap):
        self.current_image = pixmap
        self.scene.clear()
        self.scene.addPixmap(self.current_image)

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

        poly = QPolygonF(self.corners)

        if self.polygon_item is None:
            self.polygon_item = QGraphicsPolygonItem()
            self.polygon_item.setPen(QPen(self._SELECTION_COLOR, 2))

            fill = QColor(self._SELECTION_COLOR)
            fill.setAlpha(60)
            self.polygon_item.setBrush(QBrush(fill))
            self.scene.addItem(self.polygon_item)

        self.polygon_item.setPolygon(poly)

    def add_corner(self, pos: QPointF):
        if len(self.corners) >= self._MAX_CORNERS:
            return

        self.corners.append(pos)

        item = CornerHandle(len(self.corners) - 1, self)
        item.setPos(pos)
        self.scene.addItem(item)

        self.marker_items.append(item)
        self._update_polygon()

    def handle_moved(self, index, new_pos):
       self.corners[index] = new_pos
       self._update_polygon()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.add_corner(scene_pos)
            return
        super().mousePressEvent(event)


    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self._zoom_image(event)
        else:
            super().wheelEvent(event)