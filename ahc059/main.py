"""
N x Nのグリッド上に配置された数字カードをなるべく多く除去する問題

条件：
    - 同じ数字のカードは2枚ずつ存在する
    - 初期位置はグリッドの左上 (0, 0)

可能な操作：
    - U,D,L,R: 現在位置から上下左右のいずれかに移動する。（これが移動回数Kにカウントされる）
    - Z: 現在位置にあるカードを山札の一番上に置く。もし、山札の一番上にあるカードと同じ数字であれば、両方とも除去される。
    - X: 現在位置が空ならば、山札の一番上にあるカードを置くことができる。

得点（移動回数K,盤面と山札に残ったカード数X）：
    - (X=0) N^2 + 2N^3 - K
    - (X>0) N^2 - X
    - 全て除外する方が点数は高い

"""


def solve1(
    n: int,
    a: list[list[int]],
) -> str:
    """まずは、左上から順番に除外していく"""

    # 数字の位置の辞書を作る
    a_map = [[] for _ in range(n * n // 2)]
    for y in range(n):
        for x in range(n):
            a_map[a[y][x]].append((x, y))

    ans = ""
    removed = [False] * (n * n // 2)
    cur_x, cur_y = 0, 0
    for i in range(n * n):
        y, x = divmod(i, n)

        # すでに除外されているカードはスキップ
        if removed[a[y][x]]:
            continue

        # カードを除外するために
        # 1. 現在位置からカードの位置(x, y)まで移動する
        # 2. カードを山札の一番上に置く
        # 3. 対応するカードの位置まで移動する
        # 4. カードを山札の一番上に置く
        # 5. そのカードの数字を除外済みにする
        ans += (
            "U" * (cur_y - y)
            + "D" * (y - cur_y)
            + "L" * (cur_x - x)
            + "R" * (x - cur_x)
        )
        ans += "Z"
        cur_x, cur_y = x, y
        x2, y2 = a_map[a[y][x]][1]
        ans += (
            "U" * (cur_y - y2)
            + "D" * (y2 - cur_y)
            + "L" * (cur_x - x2)
            + "R" * (x2 - cur_x)
        )
        ans += "Z"
        cur_x, cur_y = x2, y2
        removed[a[y][x]] = True

    return ans


def solve2(
    n: int,
    a: list[list[int]],
) -> str:
    """
    1. 全ての数字を1枚ずつ山札に積んでいく
    2. 山札の一番上の数字の位置に移動して除外していく
    """

    # 数字の位置の辞書を作る
    a_map = [[] for _ in range(n * n // 2)]
    for y in range(n):
        for x in range(n):
            a_map[a[y][x]].append((x, y))

    ans = ""
    stack = []
    is_empty = [[False] * n for _ in range(n)]  # その位置にカードが置いてあるかどうか
    stacked = [False] * (n * n // 2)  # その数字のカードが山札に積まれているかどうか
    cur_x, cur_y = 0, 0

    # 全ての数字を1枚ずつ山札に積んでいく
    for y in range(n):
        x_range = range(n) if y % 2 == 0 else reversed(range(n))
        for x in x_range:
            if stacked[a[y][x]]:
                continue

            ans += (
                "U" * (cur_y - y)
                + "D" * (y - cur_y)
                + "L" * (cur_x - x)
                + "R" * (x - cur_x)
            )
            ans += "Z"
            stack.append(a[y][x])
            stacked[a[y][x]] = True
            is_empty[y][x] = True
            cur_x, cur_y = x, y

    # 山札の一番上の数字の位置に移動して除外していく
    while stack:
        num = stack.pop()
        x, y = a_map[num][0]
        if is_empty[y][x]:
            x, y = a_map[num][1]
        ans += (
            "U" * (cur_y - y)
            + "D" * (y - cur_y)
            + "L" * (cur_x - x)
            + "R" * (x - cur_x)
        )
        ans += "Z"
        cur_x, cur_y = x, y

    return ans


def solve3(
    n: int,
    a: list[list[int]],
) -> str:
    pass


def main():
    n = int(input())
    a = [list(map(int, input().split())) for _ in range(n)]

    ans = solve2(n, a)
    print("\n".join(ans))


if __name__ == "__main__":
    main()
