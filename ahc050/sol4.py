"""
座標は (y, x) で y * n + x で表す
"""

# 4 方向 (上、左、下、右)
import random
import sys


DY = [-1, 0, 1, 0]
DX = [0, -1, 0, 1]


class Solver:
    def __init__(
        self,
        n: int,
        m: int,
        is_wall_at: list[int],
    ):
        self.n = n
        self.m = m
        self.is_wall_at = list(is_wall_at)

        self._init_dist_to_wall()
        self._init_probability()

    def _init_dist_to_wall(self):
        """dist_to_wall[dir][y * n + x] := (y, x) から dir 方向に壁までの距離を初期化する"""
        self.dist_to_wall = [[-1] * self.n * self.n for _ in range(4)]

        # 上方向と左方向
        for y in range(self.n):
            for x in range(self.n):
                if self.is_wall_at[y * self.n + x]:
                    continue

                if y == 0 or self.is_wall_at[(y - 1) * self.n + x]:
                    self.dist_to_wall[0][y * self.n + x] = 0
                else:
                    self.dist_to_wall[0][y * self.n + x] = (
                        self.dist_to_wall[0][(y - 1) * self.n + x] + 1
                    )
                if x == 0 or self.is_wall_at[y * self.n + (x - 1)]:
                    self.dist_to_wall[1][y * self.n + x] = 0
                else:
                    self.dist_to_wall[1][y * self.n + x] = (
                        self.dist_to_wall[1][y * self.n + (x - 1)] + 1
                    )

        # 下方向と右方向
        for y in reversed(range(self.n)):
            for x in reversed(range(self.n)):
                if self.is_wall_at[y * self.n + x]:
                    continue

                if y == self.n - 1 or self.is_wall_at[(y + 1) * self.n + x]:
                    self.dist_to_wall[2][y * self.n + x] = 0
                else:
                    self.dist_to_wall[2][y * self.n + x] = (
                        self.dist_to_wall[2][(y + 1) * self.n + x] + 1
                    )
                if x == self.n - 1 or self.is_wall_at[y * self.n + (x + 1)]:
                    self.dist_to_wall[3][y * self.n + x] = 0
                else:
                    self.dist_to_wall[3][y * self.n + x] = (
                        self.dist_to_wall[3][y * self.n + (x + 1)] + 1
                    )

    def _put_wall(self, pos: int):
        """pos に壁を配置し、dist_to_wall を更新する"""
        self.is_wall_at[pos] = 1

        for dir in range(4):
            y, x = divmod(pos, self.n)
            dist = 0
            while True:
                # dist_to_wall[dir] を更新するには、 dir と逆方向に見ていく必要がある
                y -= DY[dir]
                x -= DX[dir]
                if y < 0 or y >= self.n or x < 0 or x >= self.n:
                    break
                if self.is_wall_at[y * self.n + x]:
                    break

                self.dist_to_wall[dir][y * self.n + x] = dist
                dist += 1

    def _init_probability(self):
        # リストの初期化とGC対策のために、2 つのリストを交互に使用する
        self.current_probabilities_index = 0
        self.probabilities = [[1] * self.n * self.n for _ in range(2)]

    def _update_probability(self):
        """1 ステップ分の確率遷移を行う"""
        next_probabilities_index = 1 - self.current_probabilities_index
        for pos in range(self.n * self.n):
            self.probabilities[next_probabilities_index][pos] = 0

        for pos in range(self.n * self.n):
            if self.is_wall_at[pos]:
                continue

            y, x = divmod(pos, self.n)
            quarter_probability = (
                self.probabilities[self.current_probabilities_index][pos] / 4
            )
            for dir in range(4):
                dist = self.dist_to_wall[dir][pos]

                ny = y + DY[dir] * dist
                nx = x + DX[dir] * dist
                npos = ny * self.n + nx
                self.probabilities[next_probabilities_index][npos] += (
                    quarter_probability
                )

        self.current_probabilities_index = next_probabilities_index

    def solve(self) -> list[int]:
        """各ステップで最も確率が低いマスに壁を配置する貪欲法で解く"""
        THRESHOLD = 1e-15
        WALL_PROBABILITY = 1e-12
        operations = []
        score = 0
        score_per_step = self.n * self.n - self.m

        for _ in range(self.n * self.n - self.m):
            self._update_probability()

            min_probability = float("inf")
            for pos in range(self.n * self.n):
                if self.is_wall_at[pos]:
                    continue

                probability = self.probabilities[self.current_probabilities_index][pos]
                if probability < min_probability:
                    min_probability = probability

            candidate_positions = []
            for pos in range(self.n * self.n):
                if self.is_wall_at[pos]:
                    continue

                if (
                    self.probabilities[self.current_probabilities_index][pos]
                    <= min_probability + THRESHOLD
                ):
                    candidate_positions.append(pos)

            # 隣接マスの確率の合計が最も高いマスを選ぶ
            pos = -1
            max_adjacent_probability_sum = -1
            for candidate_pos in candidate_positions:
                y, x = divmod(candidate_pos, self.n)
                adjacent_probability_sum = 0
                for dir in range(4):
                    ny = y + DY[dir]
                    nx = x + DX[dir]
                    if 0 <= ny < self.n and 0 <= nx < self.n:
                        if self.is_wall_at[ny * self.n + nx]:
                            adjacent_probability_sum += WALL_PROBABILITY
                        else:
                            adjacent_pos = ny * self.n + nx
                            adjacent_probability_sum += self.probabilities[
                                self.current_probabilities_index
                            ][adjacent_pos]

                if adjacent_probability_sum > max_adjacent_probability_sum:
                    max_adjacent_probability_sum = adjacent_probability_sum
                    pos = candidate_pos

            score_per_step -= min_probability
            score += score_per_step
            self._put_wall(pos)
            operations.append(pos)

        return operations, score / (self.n * self.n - self.m)


def main():
    n, m = map(int, input().split())
    is_wall_at = [1 if c == "#" else 0 for _ in range(n) for c in input()]
    solver = Solver(n, m, is_wall_at)

    operations, score = solver.solve()
    print(round(score * 1e6 / (n * n - m - 1)), file=sys.stderr)

    for pos in operations:
        y, x = divmod(pos, n)
        print(y, x)


if __name__ == "__main__":
    main()
