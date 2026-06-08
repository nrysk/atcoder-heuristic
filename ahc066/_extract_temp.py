"""
N x N のグリッド上に散りばめられた M 個のボールとカゴのペアを、T ターン以内にできるだけ多く収納する問題
プレイヤーは右向きで (0, 0) からスタートし、最大 1 つのボールを持って、前進・左折・右折・入換のいずれかの行動を T ターン以内に繰り返すことができる
マスの間にはランダムで壁が配置される
全てのマス間で到達可能であることが保証されている
マクロは1つまで登録でき、登録したマクロは何度でも使用できる

入力
- N: グリッドのサイズ
- M: ボールとカゴのペアの数
- T: ターン数
- V: 縦方向の壁の配置 (横方向の長さは N-1 であることに注意)
- H: 横方向の壁の配置 (縦方向の長さは N-1 であることに注意)

制約
- 10 <= N <= 20
- N / 2 <= M <= 2 * N
- 1 <= T <= 2 * N^2 * M

操作
- F: 前進
- L: 左折
- R: 右折
- S: 入換 (手持ちと現在のマスにあるボールを入れ替える、片方が空の場合もある)
- M: マクロ登録開始・終了
- P: マクロ実行



このスクリプトは、入力と最適なマクロのペアをデータ分析するためのもの
n, m, num_walls, macro, score を CSV 形式で出力する
問題を解くためのスクリプトでは無い
"""

from abc import ABC
from collections import deque
import math
import random
import sys
import time
import csv

# 上、左、下、右の順で定義する
# (idx+1)%4 で左折、(idx+3)%4 で右折
DX = [0, -1, 0, 1]
DY = [-1, 0, 1, 0]


class LazyDistanceTable:
    def __init__(
        self,
        n: int,
        m: int,
        t: int,
        v: list[str],
        h: list[str],
        ball_idxs: list[int],
        basket_idxs: list[int],
        macro: str,
    ):
        self.n = n
        self.m = m
        self.t = t
        self._precalc_wall_dist(v, h)
        self.ball_idxs = ball_idxs
        self.basket_idxs = basket_idxs
        self.macro = macro

        # 距離や経路を保存するためのテーブル
        self.dist = [[-1] * n * n * 4 for _ in range(n * n * 4)]
        self.turn = [[-1] * n * n * 4 for _ in range(n * n * 4)]
        self.prev_state = [[-1] * n * n * 4 for _ in range(n * n * 4)]
        self.prev_op = [[""] * n * n * 4 for _ in range(n * n * 4)]
        self.current_version = 0  # テーブルのバージョン管理用の変数
        self.version_table = (
            [-1] * (n * n * 4)
        )  # 各 from_state について、最新のmacroのバージョンで計算済みかどうかを管理するテーブル
        self.visited_token = 0  # これが visited テーブルの現在のバージョンを表すトークン。BFS のたびにインクリメントして、古いバージョンの訪問管理を無効化する
        self.visited = [-1] * (n * n * 4)  # BFS の訪問管理用のテーブル

        # マクロの遷移を保存するテーブル
        self.macro_next_state = [-1] * (n * n * 4)
        self._precalc_macro_transition()

    def _precalc_wall_dist(self, v: list[str], h: list[str]) -> list[list[int]]:
        """全ての位置と向きから何マス先に壁があるかを4方向について計算する"""
        # wall_dist[from_idx][dir] = from_idx から dir 方向に進んだときの最初の壁の位置
        wall_dist = [[-1] * 4 for _ in range(self.n * self.n)]

        # 上方向
        for y in range(self.n):
            for x in range(self.n):
                idx = y * self.n + x
                if y == 0 or h[y - 1][x] == "1":
                    wall_dist[idx][0] = 0
                else:
                    wall_dist[idx][0] = wall_dist[idx - self.n][0] + 1
        # 左方向
        for y in range(self.n):
            for x in range(self.n):
                idx = y * self.n + x
                if x == 0 or v[y][x - 1] == "1":
                    wall_dist[idx][1] = 0
                else:
                    wall_dist[idx][1] = wall_dist[idx - 1][1] + 1
        # 下方向
        for y in reversed(range(self.n)):
            for x in range(self.n):
                idx = y * self.n + x
                if y == self.n - 1 or h[y][x] == "1":
                    wall_dist[idx][2] = 0
                else:
                    wall_dist[idx][2] = wall_dist[idx + self.n][2] + 1
        # 右方向
        for y in range(self.n):
            for x in reversed(range(self.n)):
                idx = y * self.n + x
                if x == self.n - 1 or v[y][x] == "1":
                    wall_dist[idx][3] = 0
                else:
                    wall_dist[idx][3] = wall_dist[idx + 1][3] + 1
        self.wall_dist = wall_dist

    def reset_macro(self, macro: str):
        """マクロを更新したときに呼び出す。テーブルのバージョンを更新して、古いバージョンの計算結果を無効化する"""
        self.macro = macro
        self.current_version += 1
        self._precalc_macro_transition()

    def _precalc_macro_transition(self):
        """全ての位置と向きからマクロを実行したときの遷移先を計算して保存する"""
        for idx in range(self.n * self.n):
            y, x = divmod(idx, self.n)
            for dir in range(4):
                next_y, next_x, next_dir = self.play_macro(y, x, dir)
                self.macro_next_state[idx * 4 + dir] = self._encode_state(
                    next_y * self.n + next_x, next_dir
                )

    def forward(self, y: int, x: int, dir: int, times: int) -> tuple[int, int]:
        """from_idx から dir 方向に times マス進んだときの位置を返す"""
        from_idx = y * self.n + x
        dist = min(times, self.wall_dist[from_idx][dir])
        return y + DY[dir] * dist, x + DX[dir] * dist

    def play_macro(self, y: int, x: int, dir: int) -> tuple[int, int, int]:
        """マクロを実行したときの位置と向きを返す"""
        # F, L, R のみからなるマクロを想定している
        for op in self.macro:
            if op == "F":
                y, x = self.forward(y, x, dir, 1)
            elif op == "L":
                dir = (dir + 1) % 4
            elif op == "R":
                dir = (dir + 3) % 4
        return y, x, dir

    def play_operations(
        self, y: int, x: int, dir: int, operations: str
    ) -> tuple[int, int, int]:
        """操作列を実行したときの位置と向きを返す"""
        for op in operations:
            if op == "F":
                y, x = self.forward(y, x, dir, 1)
            elif op == "L":
                dir = (dir + 1) % 4
            elif op == "R":
                dir = (dir + 3) % 4
            elif op == "P":
                y, x, dir = self.play_macro(y, x, dir)
        return y, x, dir

    def _compute_bfs(self, from_idx: int, from_dir: int):
        """from_idx と from_dir をスタートとしたときの、全ての to_idx と to_dir への最短距離と経路を計算してテーブルに保存する"""
        macro_length = len(self.macro)

        queue = deque([(from_idx, from_dir)])
        from_state = self._encode_state(from_idx, from_dir)
        self.dist[from_state][from_state] = 0
        self.turn[from_state][from_state] = 0
        self.visited_token += 1

        while queue:
            idx, dir = queue.popleft()
            y, x = divmod(idx, self.n)
            current_state = self._encode_state(idx, dir)

            nexts = []  # (op, next_state, turn) のリスト

            # 前進
            ny, nx = self.forward(y, x, dir, 1)
            nidx = ny * self.n + nx
            nexts.append(("F", self._encode_state(nidx, dir), 1))

            # 左折
            ndir = (dir + 1) % 4
            nexts.append(("L", self._encode_state(idx, ndir), 1))

            # 右折
            ndir = (dir + 3) % 4
            nexts.append(("R", self._encode_state(idx, ndir), 1))

            # マクロ再生
            nexts.append(("P", self.macro_next_state[current_state], macro_length))

            for op, next_state, turn in nexts:
                if self.visited[next_state] != self.visited_token:
                    self.visited[next_state] = self.visited_token
                    self.dist[from_state][next_state] = (
                        self.dist[from_state][current_state] + 1
                    )
                    self.turn[from_state][next_state] = (
                        self.turn[from_state][current_state] + turn
                    )
                    self.prev_state[from_state][next_state] = current_state
                    self.prev_op[from_state][next_state] = op
                    queue.append(divmod(next_state, 4))

    def get(
        self,
        from_idx: int,
        from_dir: int,
        to_idx: int,
    ) -> tuple[int, int, int, int]:  # (dist, turn, to_idx, to_dir)
        """from_idx と from_dir から to_idx への最短距離と到着時の位置と向きを返す"""

        # バージョンが古い場合は BFS を計算し直す
        from_state = self._encode_state(from_idx, from_dir)
        if self.version_table[from_state] != self.current_version:
            self._compute_bfs(from_idx, from_dir)
            self.version_table[from_state] = self.current_version

        # 全ての to_dir で dist[from_state][to_state] を見て、最短距離のものを採用する
        best_dist = math.inf
        best_dir = -1
        best_turn = -1
        for to_dir in range(4):
            to_state = self._encode_state(to_idx, to_dir)
            if self.dist[from_state][to_state] < best_dist:
                best_dist = self.dist[from_state][to_state]
                best_turn = self.turn[from_state][to_state]
                best_dir = to_dir

        return best_dist, best_turn, to_idx, best_dir

    def get_path(
        self, from_idx: int, from_dir: int, to_idx: int
    ) -> tuple[list[str], int, int]:  # (path, to_idx, to_dir)
        """from_idx と from_dir から to_idx への最短経路を操作列で返す"""

        _, _, _, to_dir = self.get(from_idx, from_dir, to_idx)

        from_state = self._encode_state(from_idx, from_dir)
        current_state = self._encode_state(to_idx, to_dir)
        path = []
        while current_state != from_state:
            op = self.prev_op[from_state][current_state]
            path.append(op)
            current_state = self.prev_state[from_state][current_state]
        path.reverse()

        return path, to_idx, to_dir

    def _encode_state(self, idx: int, dir: int) -> int:
        """位置 idx と向き dir から状態をエンコードする"""
        return idx * 4 + dir


class Simulator(ABC):
    def _initialize_route_by_greedy(
        self, first_operations: str, macro: str
    ) -> tuple[list[int], int]:
        current_y, current_x, current_dir = self.distance_table.play_operations(
            0, 0, 3, first_operations
        )
        current_y, current_x, current_dir = self.distance_table.play_macro(
            current_y, current_x, current_dir
        )
        current_idx = current_y * self.n + current_x
        current_score = len(first_operations) + len(macro) + 2
        current_turn = current_score
        remaining_balls = set(range(self.m))

        route = []
        while remaining_balls:
            best_ball = -1
            best_ball_dist = math.inf
            for ball in remaining_balls:
                dist, turn, _, _ = self.distance_table.get(
                    current_idx, current_dir, self.ball_idxs[ball]
                )
                if dist < best_ball_dist:
                    best_ball_dist = dist
                    best_ball = ball

            # ボールを取りに行く
            dist, turn, current_idx, current_dir = self.distance_table.get(
                current_idx, current_dir, self.ball_idxs[best_ball]
            )
            current_score += dist + 1
            current_turn += turn + 1

            # 対応するカゴに入れに行く
            dist, turn, current_idx, current_dir = self.distance_table.get(
                current_idx, current_dir, self.basket_idxs[best_ball]
            )
            current_score += dist + 1
            current_turn += turn + 1

            if current_turn > self.t:
                current_score = (len(remaining_balls)) * self.t
                break

            route.append(best_ball)
            remaining_balls.remove(best_ball)

        # route は全てのボールを含んでいる必要があるので、残りのボールは適当に追加しておく
        for ball in remaining_balls:
            route.append(ball)

        return route, current_score

    def _evaluate_route(
        self, first_operations: str, macro: str, route: list[int]
    ) -> int:
        current_y, current_x, current_dir = self.distance_table.play_operations(
            0, 0, 3, first_operations
        )
        current_y, current_x, current_dir = self.distance_table.play_macro(
            current_y, current_x, current_dir
        )
        current_idx = current_y * self.n + current_x
        current_score = len(first_operations) + len(macro) + 2
        current_turn = current_score

        for i, ball in enumerate(route):
            # ボールを取りに行く
            dist, turn, current_idx, current_dir = self.distance_table.get(
                current_idx, current_dir, self.ball_idxs[ball]
            )
            current_score += dist + 1
            current_turn += turn + 1

            # 対応するカゴに入れに行く
            dist, turn, current_idx, current_dir = self.distance_table.get(
                current_idx, current_dir, self.basket_idxs[ball]
            )
            current_score += dist + 1
            current_turn += turn + 1

            if current_turn > self.t:
                current_score = (self.m - i) * self.t
                break

        return current_score


class AnnealSimulator(Simulator):
    FIRST_OPERATIONS_CANDIDATES = ["", "L", "R", "RR"]

    # 💡 書き換え・調整がしやすいように、焼きなましのパラメータをクラス上部に配置
    STEPS = 1000
    MIN_TEMPERATURE = 0.1

    def __init__(
        self,
        n: int,
        m: int,
        t: int,
        ball_idxs: list[int],
        basket_idxs: list[int],
        distance_table: LazyDistanceTable,
    ):
        self.n = n
        self.m = m
        self.t = t
        self.ball_idxs = ball_idxs
        self.basket_idxs = basket_idxs
        self.distance_table = distance_table

    def evaluate(self, macro: str, max_temperature: float) -> int:
        """マクロの評価関数。初動は固定して、収集順序を焼きなまし法で最適化して、そのときのスコアを返す"""
        if self.distance_table.macro != macro:
            self.distance_table.reset_macro(macro)

        best_score = math.inf

        for first_operations in self.FIRST_OPERATIONS_CANDIDATES:
            current_route, current_score = self._initialize_route_by_greedy(
                first_operations, macro
            )

            if current_score < best_score:
                best_score = current_score

            for step in range(self.STEPS):
                # 温度の線形冷却
                fraction = step / self.STEPS
                temp = (
                    max_temperature
                    + (self.MIN_TEMPERATURE - max_temperature) * fraction
                )

                # 近傍操作（swap, 2opt, insert）をランダムに選抜
                mode = random.random()
                i, j = random.sample(range(self.m), 2)

                next_route = list(current_route)
                if mode < 0.34:
                    # ① swap: 2マスの純粋入れ替え
                    next_route[i], next_route[j] = next_route[j], next_route[i]
                elif mode < 0.68:
                    # ② 2opt (reverse): 指定区間の順序反転
                    if i > j:
                        i, j = j, i
                    next_route[i : j + 1] = reversed(next_route[i : j + 1])
                else:
                    # ③ insert: 1つのボールを引っこ抜いて別の位置へ挿入
                    ball = next_route.pop(i)
                    next_route.insert(j, ball)

                # 💡 あなたの「current_turn」と「len(operations)」の複雑なスコア仕様を100%完全再現して評価
                next_score = self._evaluate_route(first_operations, macro, next_route)

                # 受理判定（最小化問題として判定）
                delta = next_score - current_score
                if delta < 0 or (
                    temp > 0 and random.random() < math.exp(-delta / temp)
                ):
                    current_route = next_route
                    current_score = next_score

                    if current_score < best_score:
                        best_score = current_score

        return best_score


class DataGenerator:
    def __init__(
        self,
        n: int,
        m: int,
        t: int,
        v: list[str],
        h: list[str],
        ball_idxs: list[int],
        basket_idxs: list[int],
    ):
        self.n = n
        self.m = m
        self.t = t
        self.v = v
        self.h = h
        self.ball_idxs = ball_idxs
        self.basket_idxs = basket_idxs

        self.num_h_walls = sum(row.count("1") for row in h)
        self.num_v_walls = sum(row.count("1") for row in v)

        # 最初は空のマクロを登録しておく
        self.distance_table = LazyDistanceTable(
            n, m, t, v, h, ball_idxs, basket_idxs, ""
        )

    def generate(self) -> list[str]:
        """複数のマクロで問題を解き、最終的に最もスコアの高い解を返す"""

        simulator = AnnealSimulator(
            self.n,
            self.m,
            self.t,
            self.ball_idxs,
            self.basket_idxs,
            self.distance_table,
        )

        # 網羅的に探すのではなく、ランダム生成した100個のマクロで評価する
        macro_set = set()
        while len(macro_set) < 100:
            num_forward = random.randint(5, 20)
            num_turn = random.randint(0, 4)
            ends_look_back = random.choice([False, True])
            macros = self.gen_macros(num_forward, num_turn, ends_look_back)

            for macro in macros:
                if macro not in macro_set:
                    macro_set.add(macro)
                    for max_temperature in [
                        0.2,
                        0.3,
                        0.4,
                        0.5,
                        0.6,
                        0.7,
                        0.8,
                        0.9,
                        1.0,
                        1.1,
                        1.2,
                        1.3,
                        1.4,
                        1.5,
                    ]:
                        score = simulator.evaluate(
                            macro, max_temperature=max_temperature
                        )
                        print(
                            f'{self.n},{self.m},{self.num_h_walls},{self.num_v_walls},"{macro}",{score},{num_forward},{num_turn},{ends_look_back},{max_temperature}',
                            file=sys.stdout,
                        )

    def gen_macros(
        self, num_forward: int, num_turn: int, ends_look_back: bool
    ) -> list[str]:
        macros = []
        for _ in range(2):
            points = [i for i in range(num_forward)]
            random.shuffle(points)
            points = points[:num_turn]

            macro = ["F"] * num_forward
            for p in points:
                macro[p] = random.choice(["LF", "RF"])
            if ends_look_back:
                macro.extend(["R", "R"])
            macros.append("".join(macro))
        return macros


def main():
    input = sys.stdin.readline
    n, m, t = map(int, input().split())
    v = [input().strip() for _ in range(n)]
    h = [input().strip() for _ in range(n - 1)]
    ball_idxs = []
    basket_idxs = []
    for _ in range(m):
        by, bx, cy, cx = map(int, input().split())
        ball_idxs.append(by * n + bx)
        basket_idxs.append(cy * n + cx)

    data_generator = DataGenerator(n, m, t, v, h, ball_idxs, basket_idxs)
    data_generator.generate()


if __name__ == "__main__":
    main()
