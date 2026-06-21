import math
import sys
import random
import time


def copy_list(from_list: list[int], to_list: list[int]):
    for i in range(len(from_list)):
        to_list[i] = from_list[i]


class Solver:
    def __init__(self, n: int, h: list[int]):
        self.n = n
        self.initial_h = h
        self.h = list(h)
        self.initial_zero_count = sum(h[i] == 0 for i in range(n * n))
        self.zero_count = self.initial_zero_count

    def solve(self):
        """
        焼きなまし法で巡回経路を最適化する
        マスが正の値の場合は全て積む
        マスが負の値の場合は、積んでいる土砂を降ろす
        """

        MIN_TEMP = 0.01
        MAX_TEMP = 100
        TIME_LIMIT = 1.7
        time_start = time.time()

        best_route = [i for i in range(self.n * self.n)]
        best_cost = self._evaluate_route(best_route)
        current_route = list(best_route)
        current_cost = best_cost

        itr = 0
        temp = MAX_TEMP
        while True:
            itr += 1
            if itr % 2000 == 0:
                elapsed_time = time.time() - time_start
                if elapsed_time > TIME_LIMIT:
                    break
                progress = elapsed_time / TIME_LIMIT
                temp = MAX_TEMP + (MIN_TEMP - MAX_TEMP) * progress

            # Swap, Reverse, or Shift
            new_route = list(current_route)
            if random.random() < 0.2:
                i, j = random.sample(range(self.n * self.n), 2)
                new_route[i], new_route[j] = new_route[j], new_route[i]
            elif random.random() < 0.5:
                i, j = sorted(random.sample(range(self.n * self.n), 2))
                new_route[i : j + 1] = reversed(new_route[i : j + 1])
            else:
                i, j = sorted(random.sample(range(self.n * self.n), 2))
                new_route = new_route[:i] + new_route[j + 1 :] + new_route[i : j + 1]

            new_cost = self._evaluate_route(new_route)
            delta = new_cost - current_cost

            if delta < 0 or random.random() < math.exp(-delta / temp):
                current_route = new_route
                current_cost = new_cost

                if current_cost < best_cost:
                    print(
                        f"ITR: {itr}, BEST COST: {best_cost} -> {current_cost}",
                        file=sys.stderr,
                    )
                    copy_list(current_route, best_route)
                    best_cost = current_cost

        print(f"TOTAL ITR: {itr}, BEST COST: {best_cost}", file=sys.stderr)

        operations = self._decode_route(best_route)
        return operations

    def _evaluate_route(self, route: list[int]) -> int:
        """
        与えられた巡回経路の評価値を計算する
        積み降ろし量：コストに加算
        移動：100 + 積んでいる量
        """

        self._reset()

        current_load = 0
        cost = 0
        current_pos = 0
        for next_pos in route:
            cy, cx = divmod(current_pos, self.n)
            ny, nx = divmod(next_pos, self.n)
            move_cost = (100 + current_load) * (abs(cy - ny) + abs(cx - nx))
            cost += move_cost

            if self.h[next_pos] > 0:
                cost += self.h[next_pos]
                current_load += self.h[next_pos]
                self.h[next_pos] = 0
                self.zero_count -= 1
            elif self.h[next_pos] < 0:
                if self.h[next_pos] + current_load >= 0:
                    cost += -self.h[next_pos]
                    current_load += self.h[next_pos]
                    self.h[next_pos] = 0
                    self.zero_count -= 1
                elif self.h[next_pos] + current_load < 0:
                    cost += current_load
                    self.h[next_pos] += current_load
                    current_load = 0

            current_pos = next_pos

            if self.zero_count == self.n * self.n:
                break

        return cost + (
            self.zero_count * 1000000
        )  # すべてのマスを0にできなかった場合は大きなペナルティ

    def _decode_route(self, route: list[int]) -> list[str]:
        """
        与えられた巡回経路を操作列に変換する
        """

        self._reset()

        operations = []
        current_load = 0
        current_pos = 0
        for next_pos in route:
            move = self._calc_move(current_pos, next_pos)
            operations.extend(move)

            if self.h[next_pos] > 0:
                operations.append(f"+{self.h[next_pos]}")
                current_load += self.h[next_pos]
                self.h[next_pos] = 0
                self.zero_count -= 1
            elif self.h[next_pos] < 0:
                if self.h[next_pos] + current_load >= 0:
                    operations.append(f"-{-self.h[next_pos]}")
                    current_load += self.h[next_pos]
                    self.h[next_pos] = 0
                    self.zero_count -= 1
                elif current_load != 0 and self.h[next_pos] + current_load < 0:
                    operations.append(f"-{current_load}")
                    self.h[next_pos] += current_load
                    current_load = 0

            current_pos = next_pos

        return operations

    def _reset(self):
        self.zero_count = self.initial_zero_count
        for i in range(self.n * self.n):
            self.h[i] = self.initial_h[i]

    def _calc_move(self, from_pos: int, to_pos: int) -> list[str]:
        from_y, from_x = divmod(from_pos, self.n)
        to_y, to_x = divmod(to_pos, self.n)
        return (
            ["U"] * (from_y - to_y)
            + ["D"] * (to_y - from_y)
            + ["L"] * (from_x - to_x)
            + ["R"] * (to_x - from_x)
        )


def main():
    n = int(input())
    h = []
    for _ in range(n):
        h.extend(list(map(int, input().split())))

    solver = Solver(n, h)
    operations = solver.solve()

    print("\n".join(operations))


if __name__ == "__main__":
    main()
