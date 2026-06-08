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
- H: 横方向の壁の配置 (縦方向の長さは N-1 であることに注意)
- V: 縦方向の壁の配置 (横方向の長さは N-1 であることに注意)

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


class LazyDistanceMap:
    """特定の位置と向きから、他の位置へ向かった時の最短距離（操作数）と到着時の向きを遅延して求めるクラス"""

    def __init__(self, n: int, h: list[str], v: list[str], macro_forward_count: int):
        self.n = n
        self.h = h
        self.v = v
        self.macro_forward_count = macro_forward_count
        # dist[n*n*4][n*n*4] の形式で取得できるようにする
        # 始めは空配列を要素とする長さ n*n*4 のリストを用意しておく
        # getが呼ばれた時に from_idx, from_dir に対応する全ての to_idx, to_dir について dist と prev_state, prev_op を計算して保存する
        self.dist = [[] for _ in range(n * n * 4)]
        self.prev_state = [[] for _ in range(n * n * 4)]
        self.prev_op = [[] for _ in range(n * n * 4)]

    def reset(self, macro_forward_count: int):
        """可能な操作が変わるため、全ての距離をリセットする"""
        self.macro_forward_count = macro_forward_count
        self.dist = [[] for _ in range(self.n * self.n * 4)]
        self.prev_state = [[] for _ in range(self.n * self.n * 4)]
        self.prev_op = [[] for _ in range(self.n * self.n * 4)]

    def _compute_bfs(self, from_idx: int, from_dir: int):
        from_state = self._encode_state(from_idx, from_dir)

        # まだ計算されていない場合は、BFSで全ての to_idx, to_dir について dist を計算して保存する
        self.dist[from_state] = [-1] * (self.n * self.n * 4)
        self.prev_state[from_state] = [-1] * (self.n * self.n * 4)
        self.prev_op[from_state] = [""] * (self.n * self.n * 4)
        queue = deque([(from_idx, from_dir)])
        self.dist[from_state][from_state] = 0

        while queue:
            idx, dir = queue.popleft()
            y, x = divmod(idx, self.n)

            # 前進
            ny, nx = self.forward(y, x, dir, 1)
            nidx = ny * self.n + nx
            # 既に訪れたことがない場合は、距離と向きを保存してキューに追加する
            next_state = self._encode_state(nidx, dir)
            if self.dist[from_state][next_state] == -1:
                self.dist[from_state][next_state] = (
                    self.dist[from_state][self._encode_state(idx, dir)] + 1
                )
                self.prev_state[from_state][next_state] = self._encode_state(idx, dir)
                self.prev_op[from_state][next_state] = "F"
                queue.append((nidx, dir))

            # マクロ前進
            ny, nx = self.forward(y, x, dir, self.macro_forward_count)
            nidx = ny * self.n + nx
            next_state = self._encode_state(nidx, dir)
            if self.dist[from_state][next_state] == -1:
                self.dist[from_state][next_state] = (
                    self.dist[from_state][self._encode_state(idx, dir)] + 1
                )
                self.prev_state[from_state][next_state] = self._encode_state(idx, dir)
                self.prev_op[from_state][next_state] = "P"
                queue.append((nidx, dir))

            # 左折
            ndir = (dir + 1) % 4
            next_state = self._encode_state(idx, ndir)
            if self.dist[from_state][next_state] == -1:
                self.dist[from_state][next_state] = (
                    self.dist[from_state][self._encode_state(idx, dir)] + 1
                )
                self.prev_state[from_state][next_state] = self._encode_state(idx, dir)
                self.prev_op[from_state][next_state] = "L"
                queue.append((idx, ndir))

            # 右折
            ndir = (dir + 3) % 4
            next_state = self._encode_state(idx, ndir)
            if self.dist[from_state][next_state] == -1:
                self.dist[from_state][next_state] = (
                    self.dist[from_state][self._encode_state(idx, dir)] + 1
                )
                self.prev_state[from_state][next_state] = self._encode_state(idx, dir)
                self.prev_op[from_state][next_state] = "R"
                queue.append((idx, ndir))

    def get(self, from_idx: int, from_dir: int, to_idx: int) -> tuple[int, int, int]:
        """from_idx, from_dir から to_idx へ向かった時の最短距離（操作数）と到着時の位置と向きを返す"""

        from_state = self._encode_state(from_idx, from_dir)

        # 未計算の場合は計算する
        if not self.dist[from_state]:
            self._compute_bfs(from_idx, from_dir)

        # 最も短い to_dir を探す
        min_dist = float("inf")
        min_dir = -1
        for to_dir in range(4):
            to_state = self._encode_state(to_idx, to_dir)
            if self.dist[from_state][to_state] != -1:
                if self.dist[from_state][to_state] < min_dist:
                    min_dist = self.dist[from_state][to_state]
                    min_dir = to_dir

        return min_dist, to_idx, min_dir

    def get_path(
        self, from_idx: int, from_dir: int, to_idx: int
    ) -> tuple[list[str], int, int]:
        """from_idx, from_dir から to_idx へ向かうための操作のリストと到着時の位置と向きを返す"""
        from_state = self._encode_state(from_idx, from_dir)

        # 未計算の場合は計算する
        if not self.dist[from_state]:
            self._compute_bfs(from_idx, from_dir)

        # to_idx に到達するための最も短い to_dir を探す
        min_dist = float("inf")
        min_dir = -1
        for to_dir in range(4):
            to_state = self._encode_state(to_idx, to_dir)
            if self.dist[from_state][to_state] != -1:
                if self.dist[from_state][to_state] < min_dist:
                    min_dist = self.dist[from_state][to_state]
                    min_dir = to_dir

        # to_state から from_state までの操作のリストを復元する
        path = []
        current_state = self._encode_state(to_idx, min_dir)
        while current_state != from_state:
            op = self.prev_op[from_state][current_state]
            path.append(op)
            current_state = self.prev_state[from_state][current_state]
        path.reverse()
        return path, to_idx, min_dir

    def forward(self, y: int, x: int, dir: int, count: int) -> tuple[int, int]:
        """
        前進操作を count 回繰り返したときの位置と向きを返す
        壁にぶつかる場合は、ぶつかったところで止まる
        """
        ny, nx = y, x
        for _ in range(count):
            if self._can_forward(ny, nx, dir):
                ny += DY[dir]
                nx += DX[dir]
            else:
                break
        return ny, nx

    def _can_forward(self, y: int, x: int, dir: int) -> bool:
        """y, x, dir から前進できるかどうかを返す"""
        ny, nx = y + DY[dir], x + DX[dir]
        if not (0 <= ny < self.n and 0 <= nx < self.n):
            return False
        if dir == 0:  # 上
            return self.h[ny][nx] == "0"
        elif dir == 1:  # 左
            return self.v[ny][nx] == "0"
        elif dir == 2:  # 下
            return self.h[y][x] == "0"
        else:  # 右
            return self.v[y][x] == "0"

    def _encode_state(self, idx: int, dir: int) -> int:
        """idx と dir から状態をエンコードする"""
        return idx * 4 + dir


class Simulator:
    """
    収納順序から最終的な操作コストを計算するクラス
    収納順序は木構造で管理され、ペア番号をノードとする
    ネストされた要素は、親ノードの運搬を一時的に中断して、子ノードのペアを運搬することを意味する
    """

    def __init__(
        self,
        n: int,
        m: int,
        t: int,
        distance_map: LazyDistanceMap,
        ball_idxs: list[int],
        basket_idxs: list[int],
        macro_forward_count: int,
    ):
        self.n = n
        self.m = m
        self.t = t
        self.distance_map = distance_map
        self.ball_idxs = ball_idxs
        self.basket_idxs = basket_idxs
        self.macro_forward_count = macro_forward_count
        self._init_start_idx_and_dir()
        self._init_order_by_greedy()

    def _init_start_idx_and_dir(self):
        """スタート位置と向きを初期化する"""
        start_y, start_x = self.distance_map.forward(
            0, 0, 3, self.macro_forward_count
        )  # マクロ前進の移動先を計算して保存する
        self.start_idx = start_y * self.n + start_x
        self.start_dir = 3  # 右向きでスタート

    def _init_order_by_greedy(self):
        """距離マップを使って、収納順序を貪欲に初期化する"""
        self.order = []

        current_idx = self.start_idx
        current_dir = self.start_dir

        remaining_pairs = set(range(self.m))

        while remaining_pairs:
            # 現在の位置から最も近いボールを探す
            min_dist = float("inf")
            next_pair = -1
            for pair in remaining_pairs:
                ball_idx = self.ball_idxs[pair]
                dist, _, _ = self.distance_map.get(current_idx, current_dir, ball_idx)
                if dist < min_dist:
                    min_dist = dist
                    next_pair = pair

            self.order.append(next_pair)
            remaining_pairs.remove(next_pair)

            # ボールの位置に移動する
            ball_idx = self.ball_idxs[next_pair]
            _, current_idx, current_dir = self.distance_map.get(
                current_idx, current_dir, ball_idx
            )

            # カゴの位置に移動する
            basket_idx = self.basket_idxs[next_pair]
            _, current_idx, current_dir = self.distance_map.get(
                current_idx, current_dir, basket_idx
            )

        self.score = self.evaluate()
        self.best_score = self.score
        self.best_order = list(self.order)

    def anneal(self, temperature: float):
        """
        焼きなまし法で収納順序を更新する
        - 2点をランダムに選んで、収納順序を入れ替える
        - 区間をランダムに選んで、収納順序を反転する
        """

        # 要素数は高々 40 なので丸ごとコピーする
        old_order = list(self.order)
        old_score = self.score

        p = random.random()
        if p < 0.3:  # Swap
            # 2点をランダムに選んで、収納順序を入れ替える
            i, j = random.sample(range(self.m), 2)
            self.order[i], self.order[j] = self.order[j], self.order[i]
        elif p < 0.7:  # Reverse
            # 区間をランダムに選んで、収納順序を反転する
            i, j = sorted(random.sample(range(self.m), 2))
            self.order[i : j + 1] = reversed(self.order[i : j + 1])
        else:  # Insert
            # 1点をランダムに選んで、そこからランダムな距離だけ移動させる
            i, j = random.sample(range(self.m), 2)
            pair = self.order.pop(i)
            self.order.insert(j, pair)

        new_score = self.evaluate()

        if random.random() < self._accept_probability(
            old_score, new_score, temperature
        ):
            self.score = new_score
            if self.score < self.best_score:
                self.best_score = self.score
                self.best_order = list(self.order)
        else:
            self.order = old_order
            self.score = old_score

    def _accept_probability(
        self, old_score: int, new_score: int, temperature: float
    ) -> float:
        """スコアの差と温度から、変更を受け入れる確率を計算する"""
        if new_score < old_score:
            return 1.0
        else:
            return math.exp((old_score - new_score) / temperature)

    def evaluate(self) -> int:
        """
        現在の収納順序に対するスコアを計算する
        T ターン以内に収納できなかった場合のスコアは、T * (収納できなかったペアの数) とする
        """
        score = (
            self.macro_forward_count + 2 + self.m * 2
        )  # マクロ前進のコスト + 各ペアのボールを取るコストと入れるコスト

        current_idx = self.start_idx
        current_dir = self.start_dir

        for i, pair in enumerate(self.order):
            ball_idx = self.ball_idxs[pair]
            basket_idx = self.basket_idxs[pair]

            # 現在の位置からボールの位置に移動するためのコストを加算する
            dist, current_idx, current_dir = self.distance_map.get(
                current_idx, current_dir, ball_idx
            )
            score += dist
            # 現在の位置からカゴの位置に移動するためのコストを加算する
            dist, current_idx, current_dir = self.distance_map.get(
                current_idx, current_dir, basket_idx
            )
            score += dist

            if score > self.t:
                # T ターンを超えた場合は、収納できなかったペアの数に応じたペナルティを加算する
                score = (self.m - i) * self.t
                break

            # 現在の位置と向きを更新する
            current_idx = basket_idx

        return score

    def decode_operations(self) -> list[str]:
        operations = (
            ["M"] + ["F"] * self.macro_forward_count + ["M"]
        )  # マクロ登録の操作

        current_idx = self.start_idx
        current_dir = self.start_dir

        for pair in self.best_order:
            ball_idx = self.ball_idxs[pair]
            basket_idx = self.basket_idxs[pair]

            # 現在の位置からボールの位置に移動するための操作を追加する
            path, _, current_dir = self.distance_map.get_path(
                current_idx, current_dir, ball_idx
            )
            operations.extend(path)
            operations.append("S")  # ボールを取る操作

            # ボールの位置からカゴの位置に移動するための操作を追加する
            path, _, current_dir = self.distance_map.get_path(
                ball_idx, current_dir, basket_idx
            )
            operations.extend(path)
            operations.append("S")  # ボールを入れる操作

            # 現在の位置と向きを更新する
            current_idx = basket_idx

        return operations[: self.t]  # 操作が T を超える場合は切り捨てる


def solve(
    n: int,
    m: int,
    t: int,
    distance_map: LazyDistanceMap,
    ball_idxs: list[int],
    basket_idxs: list[int],
    macro_forward_count: int,
) -> list[str]:
    """
    焼きなまし法により、収納する順番を決定する
    最後に operations が長さ T を超えた場合は切り捨てる
    マクロは、forward 操作を macro_forward_count 回繰り返す操作を登録するものとする
    """

    MAX_TEMPERATURE = 10.0
    MIN_TEMPERATURE = 0.1

    distance_map.reset(macro_forward_count)

    operations = []

    simulator = Simulator(
        n,
        m,
        t,
        distance_map=distance_map,
        ball_idxs=ball_idxs,
        basket_idxs=basket_idxs,
        macro_forward_count=macro_forward_count,
    )
    start_time = time.perf_counter()
    TIME_LIMIT = 0.8  # 秒
    itr = 0
    while True:
        if itr % 100 == 0:
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time > TIME_LIMIT:
                break
            temperature = MAX_TEMPERATURE * (
                1 - elapsed_time / TIME_LIMIT
            ) + MIN_TEMPERATURE * (elapsed_time / TIME_LIMIT)
            temperature = max(1e-2, temperature)  # 温度の下限を設定する

            if itr % 1000 == 0:
                print(
                    f"Iteration: {itr}, Time: {elapsed_time:.2f}s, Temperature: {temperature:.2f}, Score: {simulator.score}, Best Score: {simulator.best_score}",
                    file=sys.stderr,
                )

        simulator.anneal(temperature)

        itr += 1

    operations.extend(simulator.decode_operations())
    return operations[:t]


def main():
    n, m, t = map(int, input().split())
    v = [input() for _ in range(n)]
    h = [input() for _ in range(n - 1)]
    ball_idxs = []
    basket_idxs = []
    for _ in range(m):
        by, bx, cy, cx = map(int, input().split())
        ball_idxs.append(by * n + bx)
        basket_idxs.append(cy * n + cx)

    best_count = 3
    best_greedy_score = float("inf")

    # distance_map を使い回しながら高速に吟味
    distance_map = LazyDistanceMap(n, h, v, macro_forward_count=3)

    for count in range(3, 13):
        distance_map.reset(count)
        sim = Simulator(n, m, t, distance_map, ball_idxs, basket_idxs, count)
        if sim.score < best_greedy_score:
            best_greedy_score = sim.score
            best_count = count

    # 2. 最も優秀だったマクロ歩数で、本番の焼きなましを実行する
    distance_map.reset(best_count)
    best_operations = solve(
        n, m, t, distance_map, ball_idxs, basket_idxs, macro_forward_count=best_count
    )

    print(
        f"Best greedy score: {best_greedy_score} with macro_forward_count: {best_count}",
        file=sys.stderr,
    )

    print("\n".join(best_operations))


if __name__ == "__main__":
    main()
