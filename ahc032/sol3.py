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


def get_next_state(
    n: int, board: tuple[int, ...], stamp: list[int], y: int, x: int
) -> tuple[tuple[int, ...], int]:
    """次の盤面と、その時の差分(diff)を同時に計算する（高速化のため一本化）"""
    next_board = list(board)
    diff = 0
    for i in range(STAMP_SIZE):
        for j in range(STAMP_SIZE):
            idx = (y + i) * n + (x + j)
            current_value = next_board[idx]
            next_value = (current_value + stamp[i * STAMP_SIZE + j]) % MOD
            next_board[idx] = next_value
            diff += next_value - current_value
    return tuple(next_board), diff


def next_nodes(n: int, node: Node, stamps: list[list[int]]) -> list[Node]:
    next_nodes = []
    for stamp_id, stamp in enumerate(stamps):
        for y in range(n - 2):
            for x in range(n - 2):
                # 盤面生成とスコア計算を同時に行う
                n_board, diff = get_next_state(n, node.board, stamp, y, x)

                next_node = Node(
                    board=n_board,
                    diff=node.diff + diff,
                    operations=node.operations + ((stamp_id, y, x),),
                )
                next_nodes.append(next_node)
    return next_nodes


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

    BEAM_WIDTH = 2

    best_operations = ()
    best_diff = 0

    beam = [Node(board=tuple(board), operations=(), diff=0)]

    for _ in range(k):
        next_beam = []
        for node in beam:
            next_beam.extend(next_nodes(n, node, stamps))

        # 安全策: もし遷移先が空ならループを抜ける
        if not next_beam:
            break

        # スコアが高い順にソートしてビーム幅に絞る
        next_beam.sort(key=lambda node: node.diff, reverse=True)
        next_beam = next_beam[:BEAM_WIDTH]

        # 暫定ベストの更新
        if next_beam[0].diff > best_diff:
            best_diff = next_beam[0].diff
            best_operations = next_beam[0].operations

        # 【修正】次のステップへビームを引き継ぐ
        beam = next_beam

    # 【修正】結果を出力する
    print(len(best_operations))
    for stamp_id, y, x in best_operations:
        print(stamp_id, y, x)

    print(f"initial sum: {initial_sum}", file=sys.stderr)
    print(f"best_diff: {best_diff}", file=sys.stderr)
    print(f"final sum: {initial_sum + best_diff}", file=sys.stderr)


if __name__ == "__main__":
    main()
