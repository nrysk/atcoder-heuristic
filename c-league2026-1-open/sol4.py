"""
N x N のグリッド上にランダムに散りばめられた 1 から M-1 までの番号がついたフラッグを順番に回収するヒューリスティック問題

操作：
- U, D, L, R: 上下左右に移動
- P: 床を磨く（磨いた床は滑って移動する）
"""

import random
import sys
from collections import deque
import time
from typing import NamedTuple


class ShortestPathResult(NamedTuple):
    path: tuple[str, ...]  # 目的地までに通過する座標のリスト（開始点は含まない）
    actions: tuple[str, ...]  # 操作のリスト（移動方向を表す文字列のリスト）


class MoveResult(NamedTuple):
    next_idx: int  # 移動後の座標
    flag_captured: bool  # 移動中にフラッグを回収したかどうか


def move(
    n: int,
    current_idx: int,
    dx: int,
    dy: int,
    polished: list[bool],
    target_flag_idx: int,
) -> MoveResult:
    """
    current_idx から dx, dy 方向に移動する
    移動先が磨かれた床であれば、さらに同じ方向に移動する
    移動中か移動先に target_flag_idx があれば True を返す
    """

    flag_captured = False

    while True:
        y, x = divmod(current_idx, n)
        ny, nx = y + dy, x + dx
        if not (0 <= ny < n and 0 <= nx < n):
            break  # グリッドの外に出る

        next_idx = ny * n + nx
        current_idx = next_idx
        if current_idx == target_flag_idx:
            flag_captured = True
        if not polished[current_idx]:
            break  # 磨かれていない床に到達したら止まる

    return MoveResult(next_idx=current_idx, flag_captured=flag_captured)


def count_polished_neighbors(n: int, idx: int, polished: list[bool]) -> int:
    """idx の周囲 4 マスのうち、磨かれているマスの数を数える"""
    count = 0
    y, x = divmod(idx, n)
    if y > 0 and polished[(y - 1) * n + x]:
        count += 1
    if y < n - 1 and polished[(y + 1) * n + x]:
        count += 1
    if x > 0 and polished[y * n + (x - 1)]:
        count += 1
    if x < n - 1 and polished[y * n + (x + 1)]:
        count += 1
    return count


def find_shortest_path(
    n: int,
    start_idx: int,
    target_flag_idx: int,
    polished: list[bool],
) -> ShortestPathResult:
    """BFS で最短経路を見つける"""
    DIRECTIONS = [(-1, 0, "U"), (1, 0, "D"), (0, -1, "L"), (0, 1, "R")]
    queue = deque([(start_idx, [], [])])
    visited = [False] * (n * n)
    visited[start_idx] = True

    while queue:
        current_idx, path, actions = queue.popleft()

        for dy, dx, op in DIRECTIONS:
            move_result = move(n, current_idx, dx, dy, polished, target_flag_idx)
            if move_result.next_idx == current_idx:
                continue  # 移動できない場合はスキップ

            # フラッグを回収できる経路が見つかった
            if move_result.flag_captured:
                return ShortestPathResult(
                    path=tuple(path + [move_result.next_idx]),
                    actions=tuple(actions + [op]),
                )

            if visited[move_result.next_idx]:
                continue  # すでに訪れた座標はスキップ

            visited[move_result.next_idx] = True
            queue.append(
                (move_result.next_idx, path + [move_result.next_idx], actions + [op])
            )

    # 経路は必ず存在するはずなので、ここには到達しない
    assert False, "Path not found"


def solve(
    n: int,
    m: int,
    start_idx: int,
    flag_idxs: list[int],
    max_polish_turns: int,
    polish_probability: float = 1.0,
) -> list[str]:

    # 磨くべき床のパターン
    wanted_polished_patterns = [False] * (n * n)
    for y in range(1, n - 1):
        for x in range(1, n - 1):
            wanted_polished_patterns[y * n + x] = True
    wanted_polished_patterns[8 * n + 9] = False
    wanted_polished_patterns[10 * n + 8] = False
    wanted_polished_patterns[11 * n + 10] = False
    wanted_polished_patterns[9 * n + 11] = False

    current_idx = start_idx
    polished = [False] * (n * n)
    operations = []

    # result = find_shortest_path(n, current_idx, flag_idxs[0], polished)
    # operations.extend(result.actions)
    # current_idx = result.path[-1]

    for i, target_flag_idx in enumerate(flag_idxs):
        result = find_shortest_path(n, current_idx, target_flag_idx, polished)

        # for idx, op in zip(result.path, result.actions):
        for j in range(len(result.path)):
            idx = result.path[j]
            op = result.actions[j]
            operations.append(op)
            if (
                wanted_polished_patterns[idx]
                and random.random() < polish_probability
                and i < max_polish_turns
            ):
                polished[idx] = True
                operations.append("P")

        current_idx = result.path[-1]

    return operations


def main():
    TIME_LIMIT = 0.8  # 秒
    time_start = time.perf_counter()

    n, m = map(int, input().split())
    start_y, start_x = map(int, input().split())
    start_idx = start_y * n + start_x
    flag_idxs = []
    for _ in range(m - 1):
        y, x = map(int, input().split())
        flag_idxs.append(y * n + x)

    # 最適な磨きターンを見つける
    best_operations = solve(n, m, start_idx, flag_idxs, max_polish_turns=10)

    best_max_polish_turns = 0

    for max_polish_turns in range(20, m - 20):
        operations = solve(n, m, start_idx, flag_idxs, max_polish_turns)
        if len(operations) < len(best_operations):
            best_operations = operations
            best_max_polish_turns = max_polish_turns

    itr = 0
    while True:
        itr += 1
        if itr % 32 == 0:
            current_time = time.perf_counter()
            if current_time - time_start > TIME_LIMIT:
                break

        operations = solve(
            n, m, start_idx, flag_idxs, best_max_polish_turns, polish_probability=0.7
        )
        if len(operations) < len(best_operations):
            best_operations = operations
            print(f"New best: {len(best_operations)} operations", file=sys.stderr)

    print(
        f"Total iterations: {itr}, Best max polish turns: {best_max_polish_turns}",
        file=sys.stderr,
    )

    print("\n".join(best_operations))


if __name__ == "__main__":
    main()
