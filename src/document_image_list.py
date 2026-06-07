# This Python file uses the following encoding: utf-8
from document_image import DocumentImage
from typing import List

class DocumentImageList:
    def __init__(self):
        self._list : List[DocumentImage] = []
        self._cursor : int = -1

    def clear(self) -> None:
        self._cursor = -1
        self._list.clear()

    def next(self) -> DocumentImage | None:
        if self._cursor == len(self._list) - 1 or self._cursor == -1:
            return None
        self._cursor += 1
        return self._list[self._cursor]

    def empty(self) -> bool:
        return self._cursor == -1 or not self._list

    def previous(self) -> DocumentImage | None:
        if self._cursor == 0 or self._cursor == -1:
            return None
        self._cursor -= 1
        return self._list[self._cursor]

    def append(self, img: DocumentImage) -> None:
        self._list.append(img)
        self._cursor = len(self._list) - 1

    def remove(self) -> DocumentImage | None:
        if self._cursor == -1:
            return None
        self._list.pop(self._cursor)
        self._cursor = min(len(self._list) - 1, self._cursor)
        if self._cursor != -1:
            return self._list[self._cursor]
        return None

    def move_up(self) -> None:
        if len(self._list) < 2:
            return
        if self._cursor > 0:
            self._list[self._cursor - 1], self._list[self._cursor] = self._list[self._cursor], self._list[self._cursor - 1]
            self._cursor -= 1

    def move_down(self) -> None:
        if len(self._list) < 2:
            return
        if self._cursor < len(self._list) - 1:
            self._list[self._cursor + 1], self._list[self._cursor] = self._list[self._cursor], self._list[self._cursor + 1]
            self._cursor += 1

    def __iter__(self):
        for document_image in self._list:
            yield document_image
