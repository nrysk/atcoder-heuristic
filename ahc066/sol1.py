"""
N x N のグリッド上に散りばめられた M 個のボールとカゴのペアを、T ターン以内にできるだけ多く収納する問題
プレイヤーは右向きで (0, 0) からスタートし、最大 1 つのボールを持って、前進・左折・右折・入換のいずれかの行動を T ターン以内に繰り返すことができる
マスの間にはランダムで壁が配置される
全てのマス間で到達可能であることが保証されている

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

"""

from collections import deque
import random
import time

# 上、左、下、右の順で定義する
# (idx+1)%4 で左折、(idx+3)%4 で右折
DX = [0, -1, 0, 1]
DY = [-1, 0, 1, 0]


class LazyDistanceMap:
    """特定の位置と向きから、他の位置へ向かった時の最短距離（操作数）と到着時の向きを遅延して求めるクラス"""

    def __init__(self, n: int, h: list[str], v: list[str]):
        self.n = n
        self.h = h
        self.v = v
        # dist[n*n*4][n*n*4] の形式で取得できるようにする
        # 始めは空配列を要素とする長さ n*n*4 のリストを用意しておく
        # getが呼ばれた時に from_idx, from_dir に対応する全ての to_idx, to_dir について dist と prev_state, prev_op を計算して保存する
        self.dist = [[] for _ in range(n * n * 4)]
        self.prev_state = [[] for _ in range(n * n * 4)]
        self.prev_op = [[] for _ in range(n * n * 4)]

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
            ny, nx = y + DY[dir], x + DX[dir]
            if self.can_forward(y, x, dir):
                nidx = ny * self.n + nx
                # 既に訪れたことがない場合は、距離と向きを保存してキューに追加する
                next_state = self._encode_state(nidx, dir)
                if self.dist[from_state][next_state] == -1:
                    self.dist[from_state][next_state] = (
                        self.dist[from_state][self._encode_state(idx, dir)] + 1
                    )
                    self.prev_state[from_state][next_state] = self._encode_state(
                        idx, dir
                    )
                    self.prev_op[from_state][next_state] = "F"
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

    def can_forward(self, y: int, x: int, dir: int) -> bool:
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


def solve(
    n: int,
    m: int,
    t: int,
    distance_map: LazyDistanceMap,
    ball_idxs: list[int],
    basket_idxs: list[int],
) -> list[str]:
    """
    貪欲に現在地点から最も近いボールを取って、対応するカゴに入れる操作を繰り返す
    最後に operations が長さ T を超えた場合は切り捨てる
    """

    operations = []
    current_idx = 0
    current_dir = 3  # 右向きでスタート

    remaining_pairs = set(range(m))

    while remaining_pairs and len(operations) < t:
        # 現在地点から最も近いボールを探す
        min_dist = float("inf")
        target_pair = -1
        for pair in remaining_pairs:
            dist, _ = distance_map.get(current_idx, current_dir, ball_idxs[pair])
            if dist < min_dist:
                min_dist = dist
                target_pair = pair

        if target_pair == -1:
            break

        # 最も近いボールを取るための操作を取得して追加する
        path_to_ball, current_dir = distance_map.get_path(
            current_idx, current_dir, ball_idxs[target_pair]
        )
        operations.extend(path_to_ball)
        operations.append("S")  # ボールを取る操作

        # カゴに入れるための操作を取得して追加する
        path_to_basket, current_dir = distance_map.get_path(
            ball_idxs[target_pair],
            current_dir,
            basket_idxs[target_pair],
        )
        operations.extend(path_to_basket)
        operations.append("S")  # ボールを入れる操作

        # 現在の位置と向きを更新する
        current_idx = basket_idxs[target_pair]

        # 処理したペアを残りのペアから削除する
        remaining_pairs.remove(target_pair)

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
    distance_map = LazyDistanceMap(n, h, v)

    operations = solve(n, m, t, distance_map, ball_idxs, basket_idxs)

    print("\n".join(operations))


if __name__ == "__main__":
    main()
