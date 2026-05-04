from typing import NamedTuple
from collections import deque
import random


class SolveResult(NamedTuple):
    commands: list[list[str]]  # ロボットごとのコマンドのリスト
    signals: list[int]  # 一斉送信するコマンド番号のリスト


def to_idx(x: int, y: int, n: int) -> int:
    return y * n + x


def to_yx(idx: int, n: int) -> tuple[int, int]:
    return divmod(idx, n)


def calc_next_position(
    current: int,
    command: str,
    n: int,
    v_walls: list[str],
    h_walls: list[str],
) -> int:
    y, x = to_yx(current, n)
    if command == "L" and x > 0 and v_walls[y][x - 1] == "0":
        return current - 1
    elif command == "R" and x < n - 1 and v_walls[y][x] == "0":
        return current + 1
    elif command == "U" and y > 0 and h_walls[y - 1][x] == "0":
        return current - n
    elif command == "D" and y < n - 1 and h_walls[y][x] == "0":
        return current + n
    return current  # 移動できない場合は現在位置のまま


def precalc_minimum_path(
    n: int,
    v_walls: list[str],
    h_walls: list[str],
) -> list[list[str]]:
    # 全てのセルから全てのセルへの最短経路として、次の一手と距離を計算しておく
    # 隠セルに対してBFSを行う
    # 計算量はO(n^4)だが、n=30程度なら十分に高速に動作するはず

    # 事前に隣接リストを構築する
    adj = [[] for _ in range(n * n)]
    for i in range(n * n):
        y, x = to_yx(i, n)
        # ラベルは逆向きにする（コマンドは移動先のセルから見た方向になるため）
        if x > 0 and v_walls[y][x - 1] == "0":
            adj[i].append((i - 1, "R"))  # 左
        if x < n - 1 and v_walls[y][x] == "0":
            adj[i].append((i + 1, "L"))  # 右
        if y > 0 and h_walls[y - 1][x] == "0":
            adj[i].append((i - n, "D"))  # 上
        if y < n - 1 and h_walls[y][x] == "0":
            adj[i].append((i + n, "U"))  # 下

    min_path = [[None] * (n * n) for _ in range(n * n)]
    for start in range(n * n):
        queue = deque([(start, 0)])
        min_path[start][start] = ""  # 自分自身へのパスは空文字列
        while queue:
            current, dist = queue.popleft()
            for next_cell, command in adj[current]:
                if min_path[next_cell][start] is None:  # 未訪問
                    min_path[next_cell][start] = (command, dist + 1)
                    queue.append((next_cell, dist + 1))

    return min_path


def solve(
    n: int,  # n x n のグリッドのサイズ
    m: int,  # ロボットの数
    k: int,  # ロボットに割り当て可能な移動を行う信号数
    robots: list[int],  # ロボットの初期位置 (インデックス形式)
    v_walls: list[str],  # 縦の壁の情報 (n x (n-1) のグリッド)
    h_walls: list[str],  # 横の壁の情報 ((n-1) x n のグリッド)
) -> SolveResult:
    # ここに解法を実装する
    min_paths = precalc_minimum_path(n, v_walls, h_walls)

    visited = [False] * (n * n)  # ロボットが訪れたことのあるセルを記録する
    for robot in robots:
        visited[robot] = True

    # まだ訪れていないセルを選択して、一番近いロボットを移動させる
    commands = [
        ["L", "R", "U", "D", "S", "S", "S", "S", "S", "S"] for _ in range(m)
    ]  # コマンドは任意の10個をセット可能だが、複雑な戦略を考えるのは難しいため、全てのコマンドを同じにする
    command_to_signal = {
        cmd: i for i, cmd in enumerate(commands[0])
    }  # コマンドを信号番号に変換するための辞書
    signals = []

    while True:
        # 訪れていないセルを探す
        unvisited_cells = [i for i in range(n * n) if not visited[i]]
        if not unvisited_cells:
            break  # 全てのセルを訪れたら終了

        # 最も近い未訪問セルを見つける（全てのセルが訪問可能であることが保証されているため、必ず見つかる）
        target = random.choice(unvisited_cells)
        min_dist = float("inf")
        closest_robot_idx = None
        for robot_idx, robot in enumerate(robots):
            if min_paths[robot][target] is not None:
                command, dist = min_paths[robot][target]
                if dist < min_dist:
                    min_dist = dist
                    closest_robot_idx = robot_idx

        # 最も近いロボットを移動させる
        while robots[closest_robot_idx] != target:
            command, _ = min_paths[robots[closest_robot_idx]][target]
            signals.append(command_to_signal[command])
            # ロボットを移動させる（全てのロボットが同じ動きをする）
            for i in range(m):
                if command in commands[i]:
                    # コマンドに対応する移動を行う
                    robots[i] = calc_next_position(
                        robots[i], command, n, v_walls, h_walls
                    )
                    visited[robots[i]] = True  # 移動後のセルを訪れたことにする

    return SolveResult(commands=commands, signals=signals)


def main():
    n, m, k = map(int, input().split())
    robots = [to_idx(*map(int, input().split()), n) for _ in range(m)]
    v_walls = [input() for _ in range(n)]
    h_walls = [input() for _ in range(n - 1)]

    result = solve(n, m, k, robots, v_walls, h_walls)

    # 結果を出力する
    # 転置する
    for command in zip(*result.commands):
        print(" ".join(command))
    print("\n".join(map(str, result.signals)))


if __name__ == "__main__":
    main()
