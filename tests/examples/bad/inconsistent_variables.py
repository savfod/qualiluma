"""This file describes finding best split in array."""


def calc_err(left: list[float], right: list[float]) -> float:
    """Calculate the error between two splits.
        The error is defined as sum lengths of parts covering intervals.

    Args
        left: The left split of the array.
        right: The right split of the array.

    Returns
        The calculated error.
    """

    err = (max(left) - min(left)) + (max(right) - min(right))
    return err


def find_best_split(arr: list[float]) -> int:
    """Calculate the best split point for the array.

    Args:
        arr: The input array of floats.

    Returns:
        int: The index of the best split point.
    """
    assert len(arr) > 1, "Array must have at least two elements"
    arr = sorted(arr)

    all_losses = [calc_err(arr[:i], arr[i:]) for i in range(1, len(arr))]
    best_split = all_losses.index(min(all_losses)) + 1
    return best_split
