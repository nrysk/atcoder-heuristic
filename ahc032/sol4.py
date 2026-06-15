"""
N x N の盤面の数値合計を最大化する問題
各マスには [0, MOD) の整数が入る
M 個の 3 x 3 のスタンプが与えられる
スタンプを押すと、対応する数値が盤面のマスに加算される
スタンプは重ねて押すことができる
スタンプを押す回数の合計は K 回以下でなければならない
オーバーフローに注意する必要がある
"""

import sys
from typing import NamedTuple


class Node(NamedTuple):
    board: tuple[int, ...]
    diff: int = 0
    operations: tuple[tuple[int, int, int], ...] = ()  # (stamp_id, y, x)


MOD = 998244353
STAMP_SIZE = 3


def diff_sum(
    n: int,
    board: list[int],
    stamp: list[int],
    y: int,
    x: int,
) -> int:
    """スタンプを押した後に盤面全体の数値合計がどれだけ増えるかを計算する"""
    diff = 0
    for dy in range(STAMP_SIZE):
        for dx in range(STAMP_SIZE):
            current_value = board[(y + dy) * n + (x + dx)]
            next_value = (
                board[(y + dy) * n + (x + dx)] + stamp[dy * STAMP_SIZE + dx]
            ) % MOD
            diff += next_value - current_value
    return diff


def apply_stamp(
    n: int,
    board: list[int],
    stamp: list[int],
    y: int,
    x: int,
):
    for i in range(3):
        for j in range(3):
            board[(y + i) * n + (x + j)] += stamp[i * 3 + j]
            board[(y + i) * n + (x + j)] %= MOD


def main():
    n, m, k = map(int, input().split())
    board = []
    for _ in range(n):
        board.extend(map(int, input().split()))
    stamps = []
    for _ in range(m):
        stamp = []
        for _ in range(STAMP_SIZE):
            stamp.extend(map(int, input().split()))
        stamps.append(stamp)

    initial_sum = sum(board)

    BEAM_WIDTH = 20

    best_operations = ()
    best_diff = 0

    beam = [Node(board=tuple(board), operations=(), diff=0)]

    for _ in range(k):
        candidate = []  # (diff, stamp_id, y, x, parent_node)
        for node in beam:
            for stamp_id, stamp in enumerate(stamps):
                for i in range((n - (STAMP_SIZE - 1)) * (n - (STAMP_SIZE - 1))):
                    y, x = divmod(i, n - (STAMP_SIZE - 1))

                    # 盤面生成は行わず、差分(diff)だけを計算する
                    diff = diff_sum(n, list(node.board), stamp, y, x) + node.diff
                    candidate.append((diff, stamp_id, y, x, node))

        # diff が高い順にソートしてビーム幅に絞る
        candidate.sort(key=lambda x: x[0], reverse=True)
        candidate = candidate[:BEAM_WIDTH]

        # candidate から次のビームを生成する
        next_beam = []
        for diff, stamp_id, y, x, parent_node in candidate:
            next_board = list(parent_node.board)
            apply_stamp(n, next_board, stamps[stamp_id], y, x)
            next_node = Node(
                board=tuple(next_board),
                diff=diff,
                operations=parent_node.operations + ((stamp_id, y, x),),
            )
            next_beam.append(next_node)

        # 暫定ベストの更新
        if next_beam[0].diff > best_diff:
            best_diff = next_beam[0].diff
            best_operations = next_beam[0].operations

        # 【修正】次のステップへビームを引き継ぐ
        beam = next_beam

    # 結果出力
    print(len(best_operations))
    for stamp_id, y, x in best_operations:
        print(stamp_id, y, x)

    print(f"initial sum: {initial_sum}", file=sys.stderr)
    print(f"best_diff: {best_diff}", file=sys.stderr)
    print(f"final sum: {initial_sum + best_diff}", file=sys.stderr)


if __name__ == "__main__":
    main()
