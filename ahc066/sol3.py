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

    def get(self, from_idx: int, from_dir: int, to_idx: int) -> tuple[int, int]:
        """from_idx, from_dir から to_idx へ向かった時の最短距離（操作数）と到着時の向きを返す"""

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
        return min_dist, min_dir

    def get_path(
        self, from_idx: int, from_dir: int, to_idx: int
    ) -> tuple[list[str], int]:
        """from_idx, from_dir から to_idx へ向かうための操作のリストと到着時の向きを返す"""
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
        return path, min_dir

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
        start_idx: int,
        distance_map: LazyDistanceMap,
        ball_idxs: list[int],
        basket_idxs: list[int],
        macro_forward_count: int,
    ):
        self.n = n
        self.m = m
        self.t = t
        self.distance_map = distance_map
        self.start_idx = start_idx
        self.ball_idxs = ball_idxs
        self.basket_idxs = basket_idxs
        self.macro_forward_count = macro_forward_count
        self._init_order_by_greedy()

    def _init_order_by_greedy(
        self,
    ):
        """
        貪欲法で収納順序を初期化する
        木構造は self.next_sibling と self.first_child の配列で管理する
        具体的な operations は保存せず、あくまでも収納順序からわかる距離の合計をスコアとする
        """

        # m番目はルートノードとするため、m+1の長さの配列を用意する
        self.next_sibling = [-1] * (self.m + 1)
        self.first_child = [-1] * (self.m + 1)

        # 書き換えるべき target_node を決めるための変数
        # これを使って、next_sibling を更新する
        target_node = self.m

        remaining_pairs = set(range(self.m))

        current_idx = self.start_idx
        current_dir = 3  # 右向きでスタート
        while remaining_pairs:
            # 現在地点から最も近いボールを探す
            min_dist = float("inf")
            target_pair = -1
            for pair in remaining_pairs:
                dist, dir = self.distance_map.get(
                    current_idx, current_dir, self.ball_idxs[pair]
                )
                if dist < min_dist:
                    min_dist = dist
                    current_dir = dir
                    target_pair = pair

            if target_pair == -1:
                assert False, "There should be at least one remaining pair"

            # target_node の兄弟ノードとして target_pair を追加する
            self.next_sibling[target_node] = target_pair
            target_node = target_pair

            # 現在の位置と向きを更新する
            dist, current_dir = self.distance_map.get(
                current_idx, current_dir, self.basket_idxs[target_pair]
            )
            current_idx = self.basket_idxs[target_pair]

            # 処理したペアを残りのペアから削除する
            remaining_pairs.remove(target_pair)

        self.score = self.evaluate_score()
        self.best_score = self.score
        self.best_next_sibling = list(self.next_sibling)
        self.best_first_child = list(self.first_child)

    def anneal(self, temperature: float):
        """
        焼きなまし法で収納順序を改善する
        具体的には、ランダムに選んだペアを、木構造の別の場所に移動する
        """

        move_type = random.choice(["swap", "grow", "flatten"])
        if move_type == "swap":
            node1, node2 = random.sample(range(self.m), 2)
            self.swap_node_numbers(node1, node2)
            new_score = self.evaluate_score()
            # 最小化問題は new - old
            delta = new_score - self.score
            if delta < 0:
                self.best_score = new_score
                self.best_next_sibling = list(self.next_sibling)
                self.best_first_child = list(self.first_child)

            if delta < 0 or random.random() < math.exp(-delta / temperature):
                self.score = new_score
            else:
                # スコアが悪化した場合は、元に戻す
                self.swap_node_numbers(node1, node2)
        elif move_type == "grow":
            node = random.randint(0, self.m - 1)
            if self.next_sibling[node] != -1:
                self.grow_node(node)
                new_score = self.evaluate_score()
                # 最小化問題は new - old
                delta = new_score - self.score
                if delta < 0:
                    self.best_score = new_score
                    self.best_next_sibling = list(self.next_sibling)
                    self.best_first_child = list(self.first_child)
                if delta < 0 or random.random() < math.exp(-delta / temperature):
                    self.score = new_score
                else:
                    # スコアが悪化した場合は、元に戻す
                    self.flatten_node(node)
        else:  # flatten
            node = random.randint(0, self.m - 1)
            if self.first_child[node] != -1:
                self.flatten_node(node)
                new_score = self.evaluate_score()
                # 最小化問題は new - old
                delta = new_score - self.score
                if delta < 0:
                    self.best_score = new_score
                    self.best_next_sibling = list(self.next_sibling)
                    self.best_first_child = list(self.first_child)
                if delta < 0 or random.random() < math.exp(-delta / temperature):
                    self.score = new_score
                else:
                    # スコアが悪化した場合は、元に戻す
                    self.grow_node(node)

    def swap_node_numbers(self, node1: int, node2: int):
        """
        木構造は変化させず、node1 と node2 の番号を入れ替える
        """

        self.next_sibling[node1], self.next_sibling[node2] = (
            self.next_sibling[node2],
            self.next_sibling[node1],
        )
        self.first_child[node1], self.first_child[node2] = (
            self.first_child[node2],
            self.first_child[node1],
        )
        for i in range(self.m + 1):
            if self.next_sibling[i] == node1:
                self.next_sibling[i] = node2
            elif self.next_sibling[i] == node2:
                self.next_sibling[i] = node1

            if self.first_child[i] == node1:
                self.first_child[i] = node2
            elif self.first_child[i] == node2:
                self.first_child[i] = node1

    def grow_node(self, node: int):
        """
        node の兄弟(sibling)を、node の子(child)の先頭へ押し込む操作
        (next_sibling[node] が存在する場合のみ呼び出される)
        """
        sib = self.next_sibling[node]
        if sib == -1:
            return

        # 💡 安全のためにポインタを一時変数にすべて退避させる
        old_node_sib_sib = self.next_sibling[sib]
        old_node_child = self.first_child[node]

        # 💡 1行ずつ確実に繋ぎ替える (循環が絶対に起きない)
        self.next_sibling[node] = (
            old_node_sib_sib  # 兄弟のさらに兄弟を、自分の新しい兄弟にする
        )
        self.first_child[node] = sib  # 元の兄弟を、自分の最初の子にする
        self.next_sibling[sib] = (
            old_node_child  # 元の兄弟の次の兄弟に、元々の子を繋げる
        )

    def flatten_node(self, node: int):
        """
        node の子(child)の先頭を、node の兄弟(sibling)の先頭へ引っ張り出す操作
        (first_child[node] が存在する場合のみ呼び出される)
        """
        child = self.first_child[node]
        if child == -1:
            return

        # 💡 安全のためにポインタを一時変数にすべて退避させる
        old_node_child_sib = self.next_sibling[child]
        old_node_sib = self.next_sibling[node]

        # 💡 1行ずつ確実に繋ぎ替える
        self.first_child[node] = (
            old_node_child_sib  # 子の兄弟を、自分の新しい最初の子にする
        )
        self.next_sibling[node] = child  # 元の最初の子を、自分の新しい兄弟にする
        self.next_sibling[child] = (
            old_node_sib  # その子の次の兄弟に、元々の兄弟を繋げる
        )

    def evaluate_score(self) -> int:
        """
        現在の収納順序のスコアを計算する
        スコアは、収納順序に従って全てのペアを収納するための操作数の合計とする
        """

        target_node = self.next_sibling[self.m]
        current_idx = self.start_idx
        current_dir = 3  # 右向きでスタート

        score, _, _ = self._evaluate_score(target_node, current_idx, current_dir)
        return score + 2 + self.macro_forward_count

    def _evaluate_score(
        self, target_node: int, current_idx: int, current_dir: int
    ) -> tuple[int, int, int]:  # (score, current_idx, current_dir)
        """
        target_node を起点に収納順序のスコアを計算する
        sibling は while で辿り、child は再帰的に呼び出す
        """

        score = 0

        while target_node != -1:
            ball_idx = self.ball_idxs[target_node]
            basket_idx = self.basket_idxs[target_node]

            # まずはボールを取るための操作数を加算する
            dist, current_dir = self.distance_map.get(
                current_idx, current_dir, ball_idx
            )
            current_idx = ball_idx
            score += dist + 1  # ボールを取る操作も加算する

            # child がいる場合は寄り道をして、先に child を処理する
            if self.first_child[target_node] != -1:
                _score, current_idx, current_dir = self._evaluate_score(
                    self.first_child[target_node], current_idx, current_dir
                )
                score += _score
                # ボールの入換を行ったため、ball_idxs[first_child[target_node]] の位置に移動していることに注意する
                # ボールを拾いに行く
                dist, current_dir = self.distance_map.get(
                    current_idx,
                    current_dir,
                    self.ball_idxs[self.first_child[target_node]],
                )
                current_idx = self.ball_idxs[self.first_child[target_node]]
                score += dist + 1  # ボールを取る操作も加算する

            # カゴに入れるための操作数を加算する
            dist, current_dir = self.distance_map.get(
                current_idx, current_dir, basket_idx
            )
            current_idx = basket_idx
            score += dist + 1  # ボールを入れる操作も加算する

            # 次のノードに移動する
            target_node = self.next_sibling[target_node]

        return score, current_idx, current_dir

    def decode_operations(self) -> list[str]:
        """
        現在の収納順序に従って、実際の操作のリストを生成する
        """
        target_node = self.best_next_sibling[self.m]
        current_idx = self.start_idx
        current_dir = 3  # 右向きでスタート

        operations, _, _ = self._decode_operations(
            target_node, current_idx, current_dir
        )
        operations = ["M"] + ["F"] * self.macro_forward_count + ["M"] + operations
        return operations[: self.t]  # T ターン以内に収まるように切り捨てる

    def _decode_operations(
        self, target_node: int, current_idx: int, current_dir: int
    ) -> tuple[list[str], int, int]:  # (operations, current_idx, current_dir)
        """
        target_node を起点に収納順序の操作のリストを生成する
        sibling は while で辿り、child は再帰的に呼び出す
        """

        operations = []

        while target_node != -1:
            ball_idx = self.ball_idxs[target_node]
            basket_idx = self.basket_idxs[target_node]

            # まずはボールを取るための操作を追加する
            path_to_ball, current_dir = self.distance_map.get_path(
                current_idx, current_dir, ball_idx
            )
            operations.extend(path_to_ball)
            operations.append("S")  # ボールを取る操作
            current_idx = ball_idx

            # child がいる場合は寄り道をして、先に child を処理する
            if self.best_first_child[target_node] != -1:
                child_operations, current_idx, current_dir = self._decode_operations(
                    self.best_first_child[target_node], current_idx, current_dir
                )
                operations.extend(child_operations)
                # ボールの入換を行ったため、ball_idxs[first_child[target_node]] の位置に移動していることに注意する
                # ボールを拾いに行く
                path_to_ball, current_dir = self.distance_map.get_path(
                    current_idx,
                    current_dir,
                    self.ball_idxs[self.best_first_child[target_node]],
                )
                operations.extend(path_to_ball)
                operations.append("S")  # ボールを取る操作
                current_idx = self.ball_idxs[self.best_first_child[target_node]]

            # カゴに入れるための操作を追加する
            path_to_basket, current_dir = self.distance_map.get_path(
                current_idx, current_dir, basket_idx
            )
            operations.extend(path_to_basket)
            operations.append("S")  # ボールを入れる操作
            current_idx = basket_idx

            # 次のノードに移動する
            target_node = self.best_next_sibling[target_node]

        return operations, current_idx, current_dir


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

    MAX_TEMPERATURE = 1000.0
    MIN_TEMPERATURE = -100

    distance_map.reset(macro_forward_count)

    operations = []

    # マクロを登録する
    current_y, current_x = distance_map.forward(
        0, 0, 3, macro_forward_count
    )  # マクロ前進の移動先を計算して保存する

    # 現在の位置と向きを保存する
    start_idx = current_y * n + current_x

    simulator = Simulator(
        n,
        m,
        t,
        start_idx=start_idx,
        distance_map=distance_map,
        ball_idxs=ball_idxs,
        basket_idxs=basket_idxs,
        macro_forward_count=macro_forward_count,
    )
    start_time = time.perf_counter()
    TIME_LIMIT = 1  # 秒
    itr = 0
    while True:
        if itr % 100 == 0:
            print(
                f"itr: {itr}, score: {simulator.score}, elapsed_time: {time.perf_counter() - start_time:.2f} sec",
                file=sys.stderr,
            )
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time > TIME_LIMIT:
                break
            temperature = MAX_TEMPERATURE * (
                1 - elapsed_time / TIME_LIMIT
            ) + MIN_TEMPERATURE * (elapsed_time / TIME_LIMIT)
            temperature = max(1e-2, temperature)  # 温度の下限を設定する

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

    MACRO_FORWARD_COUNT = 8
    distance_map = LazyDistanceMap(n, h, v, macro_forward_count=MACRO_FORWARD_COUNT)
    best_operations = solve(
        n,
        m,
        t,
        distance_map,
        ball_idxs,
        basket_idxs,
        macro_forward_count=MACRO_FORWARD_COUNT,
    )

    print("\n".join(best_operations))


if __name__ == "__main__":
    main()
