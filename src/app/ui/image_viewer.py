from PySide6.QtWidgets import QDialog, QVBoxLayout, QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter


class _ZoomPanView(QGraphicsView):
    """拡大縮小・ドラッグ移動に対応した QGraphicsView。"""

    def __init__(self, scene: QGraphicsScene, parent=None) -> None:
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._last_mouse_pos = None

    def wheelEvent(self, event) -> None:
        """マウスホイールで拡大/縮小する。"""
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event) -> None:
        """左ボタン押下でドラッグ開始。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """ドラッグ中は画像を移動させる（パン）。"""
        if self._last_mouse_pos is not None:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """左ボタン離してドラッグ終了。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)


class ImageViewer(QDialog):
    """原本画像を表示するためのビューアウィンドウ。

    - マウスホイールで拡大/縮小
    - マウスドラッグで画像の移動（パン）
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("原本画像ビューア")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._scene = QGraphicsScene(self)
        self._view = _ZoomPanView(self._scene, self)
        layout.addWidget(self._view)

    def load_image(self, image_bytes: bytes) -> None:
        """画像バイナリを読み込んで表示する。既存の画像があれば更新。"""
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)
        if pixmap.isNull():
            return

        self._scene.clear()
        self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(pixmap.rect().toRectF())
        self._view.resetTransform()
        self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
