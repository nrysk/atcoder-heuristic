"""
N x Nのグリッド上に配置された全ての段ボール箱を (0, 0) に運び出すヒューリスティック問題
段ボールは重ねる事ができ、重ねた段ボールの重さに依って下の段ボールの耐久力が減少する

操作：
- 1: 現在地の段ボールをスタックに積む
- 2: スタックの段ボールを現在地に置く
- U,D,L,R: 現在地から上下左右のいずれかに移動する
"""


def solve(
    n: int,
    w: list[list[int]],
    d: list[list[int]],
) -> list[str]:
    """
    重ねる操作はせず、左上から1つずつ段ボールを運び出す
    """

    operations = []

    # 高速化と副作用を避けるため、wとdは1次元配列に変換しておく
    w = [weight for row in w for weight in row]
    d = [durability for row in d for durability in row]

    for target_idx in range(1, n * n):
        y, x = divmod(target_idx, n)
        operations.extend(["D"] * y)
        operations.extend(["R"] * x)
        operations.append("1")
        operations.extend(["U"] * y)
        operations.extend(["L"] * x)

    return operations


def main():
    n = int(input())
    w = [list(map(int, input().split())) for _ in range(n)]
    d = [list(map(int, input().split())) for _ in range(n)]

    operations = solve(n, w, d)

    print("\n".join(operations))


if __name__ == "__main__":
    main()
