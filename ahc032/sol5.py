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


def diff_sum_row1(n: int, board: list[int], stamp: list[int], y: int, x: int) -> int:
    """スタンプを押した後に盤面全体の数値合計がどれだけ増えるかを計算する（y 行目だけ）"""
    diff = 0
    for dx in range(STAMP_SIZE):
        current_value = board[y * n + (x + dx)]
        next_value = (board[y * n + (x + dx)] + stamp[dx]) % MOD
        diff += next_value - current_value
    return diff


def diff_sum_col1(n: int, board: list[int], stamp: list[int], y: int, x: int) -> int:
    """スタンプを押した後に盤面全体の数値合計がどれだけ増えるかを計算する（x 列目だけ）"""
    diff = 0
    for dy in range(STAMP_SIZE):
        current_value = board[(y + dy) * n + x]
        next_value = (board[(y + dy) * n + x] + stamp[dy * STAMP_SIZE]) % MOD
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

    # 3 つのフェーズで解を作成する
    # フェーズ 1. y = 0..n-6 で y 行目を最大化するようにスタンプを押す (各行で最大 10 ターンまで使って良い)
    # フェーズ 2. x = 0..n-6 でフェーズ 1 で対象にしなかった x 列目を最大化するようにスタンプを押す (各列で最大 6 ターンまで使って良い)
    # フェーズ 3. y = n-6..n-1 x = n-6..n-1 で残りの部分を最大化するようにスタンプを押す (残りのターンを全て使って良い)

    # フェーズ 1
    beam_width = 100
    phase1_operations = ()
    phase1_diff = 0
    phase1_use_turn = 0
    for y in range(n - 6 + 1):
        best_operations = ()
        best_diff = 0
        best_board = tuple(board)
        best_use_turn = 0

        beam = [Node(board=tuple(board), operations=(), diff=0)]
        for i in range(10):
            candidate = []  # (diff, stamp_id, y, x, parent_node)
            for node in beam:
                for stamp_id, stamp in enumerate(stamps):
                    for x in range(n - (STAMP_SIZE - 1)):
                        diff = (
                            diff_sum_row1(n, list(node.board), stamp, y, x) + node.diff
                        )
                        candidate.append((diff, stamp_id, y, x, node))

            candidate.sort(key=lambda x: x[0], reverse=True)
            candidate = candidate[:beam_width]

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

            if next_beam[0].diff > best_diff:
                best_diff = next_beam[0].diff
                best_operations = next_beam[0].operations
                best_board = next_beam[0].board
                best_use_turn = i + 1

            beam = next_beam

        phase1_operations += best_operations
        phase1_diff += best_diff
        board = list(best_board)
        phase1_use_turn += best_use_turn

    # フェーズ 2

    beam_width = 50
    phase2_operations = ()
    phase2_diff = 0
    phase2_use_turn = 0
    for x in range(n - 6 + 1):
        best_operations = ()
        best_diff = 0
        best_board = tuple(board)
        best_use_turn = 0

        beam = [Node(board=tuple(board), operations=(), diff=0)]
        for i in range(6):
            candidate = []  # (diff, stamp_id, y, x, parent_node)
            for node in beam:
                for stamp_id, stamp in enumerate(stamps):
                    for y in range(n - 6 + 1, n - (STAMP_SIZE - 1)):
                        diff = (
                            diff_sum_col1(n, list(node.board), stamp, y, x) + node.diff
                        )
                        candidate.append((diff, stamp_id, y, x, node))

            candidate.sort(key=lambda x: x[0], reverse=True)
            candidate = candidate[:beam_width]

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

            if next_beam[0].diff > best_diff:
                best_diff = next_beam[0].diff
                best_operations = next_beam[0].operations
                best_board = next_beam[0].board
                best_use_turn = i + 1

            beam = next_beam

        phase2_operations += best_operations
        phase2_diff += best_diff
        board = list(best_board)
        phase2_use_turn += best_use_turn

    # フェーズ 3
    remaining_turn = k - phase1_use_turn - phase2_use_turn

    beam_width = 50
    phase3_operations = ()
    phase3_diff = 0
    phase3_use_turn = 0

    beam = [Node(board=tuple(board), operations=(), diff=0)]
    for i in range(remaining_turn):
        candidate = []  # (diff, stamp_id, y, x, parent_node)
        for node in beam:
            for stamp_id, stamp in enumerate(stamps):
                for y in range(n - 6 + 1, n - (STAMP_SIZE - 1)):
                    for x in range(n - 6 + 1, n - (STAMP_SIZE - 1)):
                        diff = diff_sum(n, list(node.board), stamp, y, x) + node.diff
                        candidate.append((diff, stamp_id, y, x, node))

        candidate.sort(key=lambda x: x[0], reverse=True)
        candidate = candidate[:beam_width]

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

        if next_beam[0].diff > best_diff:
            best_diff = next_beam[0].diff
            best_operations = next_beam[0].operations
            best_board = next_beam[0].board
            best_use_turn = i + 1

        beam = next_beam

    phase3_operations += best_operations
    phase3_diff += best_diff
    board = list(best_board)
    phase3_use_turn += best_use_turn

    # 結果出力
    operations = phase1_operations + phase2_operations + phase3_operations
    print(len(operations))
    for stamp_id, y, x in operations:
        print(stamp_id, y, x)

    print(f"initial sum: {initial_sum}", file=sys.stderr)
    print(f"final sum: {sum(board)}", file=sys.stderr)


if __name__ == "__main__":
    main()
