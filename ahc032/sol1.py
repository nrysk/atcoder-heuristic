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


def will_overflow(
    n: int,
    board: list[int],
    stamp: list[int],
    y: int,
    x: int,
) -> bool:
    for i in range(3):
        for j in range(3):
            if board[(y + i) * n + (x + j)] + stamp[i * 3 + j] >= MOD:
                return True
    return False


def search_position(
    n: int, board: list[int], stamp: list[int]
) -> tuple[int, int] | None:
    for y in range(n - 2):
        for x in range(n - 2):
            if not will_overflow(n, board, stamp, y, x):
                return (y, x)
    return None


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
    # スタンプの数値が大きい順に、盤面がオーバーフローしない位置を探して押す
    operations = []
    sorted_stamp_ids = sorted(range(m), key=lambda i: sum(stamps[i]), reverse=True)
    for _ in range(k):
        for stamp_id in sorted_stamp_ids:
            stamp = stamps[stamp_id]

            pos = search_position(n, board, stamp)
            if pos is not None:
                y, x = pos

                operations.append((stamp_id, y, x))
                apply_stamp(n, board, stamp, y, x)
                break

    print(len(operations))
    for stamp_id, y, x in operations:
        print(stamp_id, y, x)


if __name__ == "__main__":
    main()
