"""
N x N の盤面の数値合計を最大化する問題
各マスには [0, MOD) の整数が入る
M個の 3 x 3 のスタンプが与えられる
スタンプを押すと、対応する数値が盤面のマスに加算される
スタンプは重ねて押すことができる
スタンプを押す回数の合計は K 回以下でなければならない
オーバーフローに注意する必要がある
"""

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
        for _ in range(3):
            stamp.extend(map(int, input().split()))
        stamps.append(stamp)

    # 貪欲法
    # 盤面全体で一番合計値が大きくなる押し方を探して押す
    operations = []
    for _ in range(k):
        best_diff = 0
        best_stamp_id = -1
        best_y = -1
        best_x = -1
        for stamp_id, stamp in enumerate(stamps):
            for y in range(n - 2):
                for x in range(n - 2):
                    diff = diff_sum(n, board, stamp, y, x)
                    if diff > best_diff:
                        best_diff = diff
                        best_stamp_id = stamp_id
                        best_y = y
                        best_x = x

        if best_diff == 0:
            break

        operations.append((best_stamp_id, best_y, best_x))
        apply_stamp(n, board, stamps[best_stamp_id], best_y, best_x)

    print(len(operations))
    for stamp_id, y, x in operations:
        print(stamp_id, y, x)


if __name__ == "__main__":
    main()
