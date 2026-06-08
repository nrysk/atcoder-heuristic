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

"""

from collections import deque
import math
import random
import sys
import time

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
        queue = deque([(from_idx, from_dir)])
        from_state = self._encode_state(from_idx, from_dir)
        self.dist[from_state][from_state] = 0
        self.visited_token += 1

        while queue:
            idx, dir = queue.popleft()
            y, x = divmod(idx, self.n)
            current_state = self._encode_state(idx, dir)

            # 前進
            ny, nx = self.forward(y, x, dir, 1)
            nidx = ny * self.n + nx
            next_state = self._encode_state(nidx, dir)
            if self.visited[next_state] != self.visited_token:
                self.visited[next_state] = self.visited_token
                self.dist[from_state][next_state] = (
                    self.dist[from_state][current_state] + 1
                )
                self.prev_state[from_state][next_state] = current_state
                self.prev_op[from_state][next_state] = "F"
                queue.append((nidx, dir))

            # 左折
            ndir = (dir + 1) % 4
            next_state = self._encode_state(idx, ndir)
            if self.visited[next_state] != self.visited_token:
                self.visited[next_state] = self.visited_token
                self.dist[from_state][next_state] = (
                    self.dist[from_state][current_state] + 1
                )
                self.prev_state[from_state][next_state] = current_state
                self.prev_op[from_state][next_state] = "L"
                queue.append((idx, ndir))

            # 右折
            ndir = (dir + 3) % 4
            next_state = self._encode_state(idx, ndir)
            if self.visited[next_state] != self.visited_token:
                self.visited[next_state] = self.visited_token
                self.dist[from_state][next_state] = (
                    self.dist[from_state][current_state] + 1
                )
                self.prev_state[from_state][next_state] = current_state
                self.prev_op[from_state][next_state] = "R"
                queue.append((idx, ndir))

            # マクロ再生
            next_state = self.macro_next_state[current_state]
            if self.visited[next_state] != self.visited_token:
                self.visited[next_state] = self.visited_token
                self.dist[from_state][next_state] = (
                    self.dist[from_state][current_state] + 1
                )
                self.prev_state[from_state][next_state] = current_state
                self.prev_op[from_state][next_state] = "P"
                queue.append(divmod(next_state, 4))

    def get(self, from_idx: int, from_dir: int, to_idx: int) -> tuple[int, int, int]:
        """from_idx と from_dir から to_idx への最短距離と到着時の位置と向きを返す"""

        # バージョンが古い場合は BFS を計算し直す
        from_state = self._encode_state(from_idx, from_dir)
        if self.version_table[from_state] != self.current_version:
            self._compute_bfs(from_idx, from_dir)
            self.version_table[from_state] = self.current_version

        # 全ての to_dir で dist[from_state][to_state] を見て、最短距離のものを採用する
        best_dist = math.inf
        best_dir = -1
        for to_dir in range(4):
            to_state = self._encode_state(to_idx, to_dir)
            if self.dist[from_state][to_state] < best_dist:
                best_dist = self.dist[from_state][to_state]
                best_dir = to_dir

        return best_dist, to_idx, best_dir

    def get_path(
        self, from_idx: int, from_dir: int, to_idx: int
    ) -> tuple[list[str], int, int, int]: # (path, to_idx, to_dir, turn)
        """from_idx と from_dir から to_idx への最短経路を操作列で返す"""

        _, _, to_dir = self.get(from_idx, from_dir, to_idx)

        from_state = self._encode_state(from_idx, from_dir)
        current_state = self._encode_state(to_idx, to_dir)
        current_turn = 0
        macro_length = len(self.macro)
        path = []
        while current_state != from_state:
            op = self.prev_op[from_state][current_state]
            path.append(op)
            current_state = self.prev_state[from_state][current_state]
            if op == "P":
                current_turn += macro_length
            else:
                current_turn += 1
        path.reverse()
        return path, to_idx, to_dir, current_turn

    def _encode_state(self, idx: int, dir: int) -> int:
        """位置 idx と向き dir から状態をエンコードする"""
        return idx * 4 + dir


class Solver:
    FIRST_OPERATIONS_CANDIDATES = ["", "L", "R"]

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

        self.num_walls = sum(row.count("1") for row in v) + sum(row.count("1") for row in h)

        # 最初は空のマクロを登録しておく
        self.distance_table = LazyDistanceTable(
            n, m, t, v, h, ball_idxs, basket_idxs, ""
        )

    def solve(self) -> list[str]:
        """複数のマクロで問題を解き、最終的に最もスコアの高い解を返す"""

        TIME_LIMIT = 1.5  # 秒
        time_start = time.time()

        best_operations, best_score = self._solve(
            ""
        )  # 最初はマクロなしで解いてみる
        print(f"Initial score without macro: {best_score}", file=sys.stderr)

        # ランダムにマクロを生成して試す
        itr = 0
        while True:
            if itr % 16 == 0:
                elapsed = time.time() - time_start
                if elapsed > TIME_LIMIT:
                    break
            itr += 1

            macro = self._gen_macro()
            operations, score = self._solve(macro)
            if score < best_score:
                print(
                    f"Iteration {itr}: New best score {score} with macro {macro}",
                    file=sys.stderr,
                )
                best_score = score
                best_operations = operations

        print(f"Total iterations: {itr}", file=sys.stderr)

        return best_operations

    def _gen_macro(self) -> str:
        macro_length = random.randint(3, 22)
        macro = random.choice("FLR") +  "F" * (macro_length - 3) + random.choice("FLR")
        # macro = "F" * (macro_length - 2) + random.choice("FLR")
        i = random.randint(1, macro_length - 1)
        macro = macro[:i] + random.choice("FLR") + macro[i:]
        if self.num_walls > 30:
            j = random.randint(1, macro_length - 1)
            macro = macro[:j] + random.choice("FLR") + macro[j:]
        if random.random() < 0.5:
            macro += macro[-1]
        
        return macro
    


    def _solve(self, macro: str) -> tuple[list[str], int]:
        """与えられたマクロを使って問題を解く。返り値は操作列"""
        self.distance_table.reset_macro(macro)

        best_operations = None
        best_score = float("inf")

        for first_operations in self.FIRST_OPERATIONS_CANDIDATES:
            # 最初の操作列を試す。これもマクロに含める
            operations = (
                [op for op in first_operations] + ["M"] + [op for op in macro] + ["M"]
            )
            current_y, current_x, current_dir = self.distance_table.play_operations(
                0, 0, 3, first_operations
            )
            current_y, current_x, current_dir = self.distance_table.play_macro(
                current_y, current_x, current_dir
            )
            current_turn = len(operations)

            # 貪欲法で解く。毎回、最も近いボールを取りに行き、次に最も近いカゴに入れに行く、を繰り返す

            current_idx = current_y * self.n + current_x

            remaining_balls = set(range(self.m))

            while remaining_balls:
                # 最も近いボールを探す
                best_ball = -1
                best_ball_dist = math.inf
                for ball in remaining_balls:
                    dist, _, _ = self.distance_table.get(
                        current_idx, current_dir, self.ball_idxs[ball]
                    )
                    if dist < best_ball_dist:
                        best_ball_dist = dist
                        best_ball = ball

                # 最も近いボールを取りに行く
                path, current_idx, current_dir, turn = self.distance_table.get_path(
                    current_idx, current_dir, self.ball_idxs[best_ball]
                )
                operations.extend(path)
                operations.append("S")  # ボールを取る
                current_turn += turn + 1

                # 対応するカゴに入れに行く
                path, current_idx, current_dir, turn = self.distance_table.get_path(
                    current_idx, current_dir, self.basket_idxs[best_ball]
                )
                operations.extend(path)
                operations.append("S")  # ボールを入れる
                current_turn += turn + 1

                if current_turn > self.t:
                    score = (len(remaining_balls)) * self.t
                    break

                remaining_balls.remove(best_ball)

            else: # while が正常に終了した場合
                score = len(operations)

            if score < best_score:
                best_score = score
                best_operations = operations

        return best_operations, best_score


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

    solver = Solver(n, m, t, v, h, ball_idxs, basket_idxs)
    operations = solver.solve()
    print(f"Score: {len(operations)}", file=sys.stderr)
    print("".join(operations))


if __name__ == "__main__":
    main()
