"""
ノート - 座標形式は(0, 0)が左上、(n-1, n-1)が右下で、(y, x)の順で表す
"""

from pprint import pprint
from typing import NamedTuple
from collections import deque
import random
import time


class SolveResult(NamedTuple):
    commands: list[list[str]]  # ロボットごとのコマンドのリスト
    signals: list[int]  # 一斉送信するコマンド番号のリスト


def to_idx(y: int, x: int, n: int) -> int:
    return y * n + x


def to_yx(idx: int, n: int) -> tuple[int, int]:
    return divmod(idx, n)


class PathManager:
    def __init__(
        self,
        n: int,
        v_walls: list[str],
        h_walls: list[str],
    ):
        self.n = n
        self.v_walls = v_walls
        self.h_walls = h_walls
        self._precalc()

    def _precalc(self):
        self.minimum_path = [[None] * (self.n * self.n) for _ in range(self.n * self.n)]

        # 壁の処理が大変なので予め隣接リストを構築する
        adj = [[] for _ in range(self.n * self.n)]
        for i in range(self.n * self.n):
            y, x = to_yx(i, self.n)
            if x > 0 and self.v_walls[y][x - 1] == "0":
                adj[i].append(i - 1)
            if x < self.n - 1 and self.v_walls[y][x] == "0":
                adj[i].append(i + 1)
            if y > 0 and self.h_walls[y - 1][x] == "0":
                adj[i].append(i - self.n)
            if y < self.n - 1 and self.h_walls[y][x] == "0":
                adj[i].append(i + self.n)

        # 各セルに対してBFSを行う
        # Queueには(現在のセル, 最初の一手, 距離)を入れる
        for start in range(self.n * self.n):
            first_candidates = []
            start_y, start_x = to_yx(start, self.n)
            if start_x > 0 and self.v_walls[start_y][start_x - 1] == "0":
                first_candidates.append((start - 1, "L", 1))
            if start_x < self.n - 1 and self.v_walls[start_y][start_x] == "0":
                first_candidates.append((start + 1, "R", 1))
            if start_y > 0 and self.h_walls[start_y - 1][start_x] == "0":
                first_candidates.append((start - self.n, "U", 1))
            if start_y < self.n - 1 and self.h_walls[start_y][start_x] == "0":
                first_candidates.append((start + self.n, "D", 1))
            queue = deque(first_candidates)
            visited = [False] * (self.n * self.n)

            while queue:
                current, first_command, dist = queue.popleft()
                if visited[current]:
                    continue
                visited[current] = True
                self.minimum_path[start][current] = (first_command, dist)

                for next_cell in adj[current]:
                    if not visited[next_cell]:
                        queue.append((next_cell, first_command, dist + 1))

    def get_path(self, start: int, goal: int) -> tuple[str, int]:
        # 到達不能は無いことが保証されている
        return self.minimum_path[start][goal]


class Simulator:
    def __init__(
        self,
        n: int,
        m: int,
        k: int,
        robot_positions: list[int],
        v_walls: list[str],
        h_walls: list[str],
        path_manager: PathManager,
    ):
        self.n = n
        self.m = m
        self.k = k
        self.initial_robot_positions = list(robot_positions)
        self.robot_positions = robot_positions
        self.path_manager = path_manager
        self.v_walls = v_walls
        self.h_walls = h_walls
        self._init_commands()

    def _init_commands(self):
        self.commands = [
            ["U", "D", "L", "R", "S", "S", "S", "S", "S", "S"]
            for _ in range(self.m)  # Sは数合わせなので無視
        ]  # ロボットごとのコマンドのリスト
        self.commands_to_signal = [
            {"U": 0, "D": 1, "L": 2, "R": 3} for _ in range(self.m)
        ]  # コマンドから信号へのマッピング

    def reset(self):
        self.robot_positions = list(self.initial_robot_positions)

    def shuffle_commands(self):
        # 乱択アルゴリズム用
        for robot_index in range(self.m):
            sub = self.commands[robot_index][
                :4
            ]  # 最初の4つのコマンドだけシャッフルする
            random.shuffle(sub)
            self.commands[robot_index][:4] = sub
            self.commands_to_signal[robot_index] = {
                command: signal
                for signal, command in enumerate(self.commands[robot_index])
            }

    def swap_commands_randomly(self, robot_index: int) -> tuple[int, int]:
        i, j = random.sample(range(4), 2)
        self.swap_commands(robot_index, i, j)
        return i, j

    def swap_commands(self, robot_index: int, i: int, j: int):
        self.commands[robot_index][i], self.commands[robot_index][j] = (
            self.commands[robot_index][j],
            self.commands[robot_index][i],
        )
        self.commands_to_signal[robot_index][self.commands[robot_index][i]] = i
        self.commands_to_signal[robot_index][self.commands[robot_index][j]] = j

    def solve(self) -> SolveResult:
        signals = []

        # all(visited)がTrueになるまで、ロボットを動かし続ける
        # 1. マスを順番に見ていき、未訪問マスがあればそこをtargetに設定する
        # 2. targetに一番近いロボットを選択する
        # 3. そのロボットがtargetと一致するまで、path_managerから最短経路を取得して動かす
        # 4. 1~3を繰り返す
        #
        # [追加]
        # マスを見る順番を蛇行させる
        visited = [False] * (self.n * self.n)
        for robot in self.robot_positions:
            visited[robot] = True

        for target_y in range(self.n):
            for target_x in (
                reversed(range(self.n)) if target_y % 2 == 0 else range(self.n)
            ):
                target = to_idx(target_y, target_x, self.n)
                if visited[target]:
                    continue

                closest_robot_index = self._find_closest_robot(target)
                while not visited[target]:
                    command, _ = self.path_manager.get_path(
                        self.robot_positions[closest_robot_index], target
                    )
                    signal = self._move_robot(closest_robot_index, command, visited)
                    signals.append(signal)

        return SolveResult(
            commands=[row[:] for row in self.commands], signals=list(signals)
        )

    def _find_closest_robot(self, target: int) -> int:
        # targetに一番近いロボットのインデックスを返す
        min_dist = float("inf")
        closest_robot_index = None
        for i, robot in enumerate(self.robot_positions):
            _, dist = self.path_manager.get_path(robot, target)
            if dist < min_dist:
                min_dist = dist
                closest_robot_index = i
        return closest_robot_index

    def _move_robot(self, robot_index: int, command: str, visited: list[bool]) -> int:
        signal = self.commands_to_signal[robot_index][command]
        # 全てのロボットが同じ信号を受け取るため、全てのロボットを同じコマンドで動かす
        for i in range(self.m):
            indivisual_command = self.commands[i][signal]
            # indivisual_commandに従ってロボットiを動かす
            self.robot_positions[i] = self._calc_next_position(
                self.robot_positions[i], indivisual_command
            )
            # 移動後の位置をvisitedに反映する
            visited[self.robot_positions[i]] = True
        return signal

    def _calc_next_position(self, current: int, command: str) -> int:
        # commandに従ってcurrentから移動した先のセルを返す
        y, x = to_yx(current, self.n)
        if command == "L" and x > 0 and self.v_walls[y][x - 1] == "0":
            return current - 1
        if command == "R" and x < self.n - 1 and self.v_walls[y][x] == "0":
            return current + 1
        if command == "U" and y > 0 and self.h_walls[y - 1][x] == "0":
            return current - self.n
        if command == "D" and y < self.n - 1 and self.h_walls[y][x] == "0":
            return current + self.n
        return current  # 移動できない場合は元の位置に留まる


def main():
    TIME_LIMIT = 1.4
    start_time = time.perf_counter()

    n, m, k = map(int, input().split())  # 盤面のサイズ（n x n)、ロボットの数、信号の数
    robot_positions = [
        to_idx(*map(int, input().split()), n) for _ in range(m)
    ]  # ロボットの初期位置
    v_walls = [input().strip() for _ in range(n)]  # 縦の壁の情報
    h_walls = [input().strip() for _ in range(n - 1)]  # 横の壁の情報

    path_manager = PathManager(n, v_walls, h_walls)

    simulator = Simulator(n, m, k, robot_positions, v_walls, h_walls, path_manager)

    best_result = simulator.solve()  # 最初の解を生成
    best_cost = len(best_result.signals)

    # # 乱択アルゴリズムで解を改善していく
    # iteration = 0
    # while True:
    #     if iteration % 32 == 0:
    #         elapsed_time = time.perf_counter() - start_time
    #         if elapsed_time > TIME_LIMIT:
    #             break
    #     iteration += 1

    #     simulator.reset()  # ロボットの位置を初期状態に戻す
    #     simulator.shuffle_commands()  # コマンドをシャッフルして新しい解を生成

    #     new_result = simulator.solve()
    #     new_cost = len(new_result.signals)
    #     # print(f"Iteration {iteration}: Cost = {new_cost}, Best Cost = {best_cost}")
    #     if new_cost < best_cost:
    #         best_result = new_result
    #         best_cost = new_cost

    # 山登りアルゴリズムで解を改善していく
    iteration = 0
    while True:
        if iteration % 32 == 0:
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time > TIME_LIMIT:
                break
        iteration += 1

        simulator.reset()  # ロボットの位置を初期状態に戻す

        # コマンドを少し変更して新しい解を生成
        robot_index = random.randint(0, m - 1)
        i, j = simulator.swap_commands_randomly(robot_index)

        new_result = simulator.solve()
        new_cost = len(new_result.signals)
        # print(f"Iteration {iteration}: Cost = {new_cost}, Best Cost = {best_cost}")
        if new_cost < best_cost:
            best_result = new_result
            best_cost = new_cost
        else:
            # コストが改善しなかったら変更を元に戻す
            simulator.swap_commands(robot_index, i, j)

    # 結果の出力
    for command in zip(*best_result.commands):
        print(" ".join(command))
    print("\n".join(map(str, best_result.signals)))


if __name__ == "__main__":
    main()
