"""Merge sort, used to order candidate links by installation cost before
Kruskal's algorithm runs.

The assignment explicitly calls for a sorting algorithm as a first step for
Kruskal's Algorithm; we implement merge sort from scratch (rather than
relying on ``list.sort``) to demonstrate the O(E log E) divide-and-conquer
routine itself.
"""

from __future__ import annotations

from typing import Callable, List, TypeVar

T = TypeVar("T")


def merge_sort(items: List[T], key: Callable[[T], float]) -> List[T]:
    """Return a new list sorted ascending by ``key`` using merge sort.

    Stable, O(n log n) worst case, O(n) extra space.
    """
    if len(items) <= 1:
        return list(items)

    mid = len(items) // 2
    left = merge_sort(items[:mid], key)
    right = merge_sort(items[mid:], key)
    return _merge(left, right, key)


def _merge(left: List[T], right: List[T], key: Callable[[T], float]) -> List[T]:
    merged: List[T] = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged
