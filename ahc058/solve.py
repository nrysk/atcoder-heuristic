"""
りんごの拡大再生産ゲームのヒューリスティック問題

固定値
- n = 10
- l = 4
- t = 500
- k = 1
"""

import sys
from dataclasses import dataclass
import random
import itertools
import time


@dataclass(slots=True)
class MachineColumn:
    column_index: int
    powers: list[int]  # powers[level]
    counts: list[int]  # counts[level]


class Simulator:
    def __init__(
        self,
        initial_apples: int,
        total_columns: int,
        total_levels: int,
        total_turns: int,
        base_costs: list[int],  # base_costs[level * total_columns + column_index]
        productivities: list[
            int
        ],  # productivities[column_index] (これはレベル0限定で使うもの)
    ):
        self.initial_apples = initial_apples
        self.total_columns = total_columns
        self.total_levels = total_levels
        self.total_turns = total_turns
        self.base_costs = base_costs
        self.productivities = productivities

    def _initialize_environment(self):
        self.apple = self.initial_apples
        self.machine_columns = [
            MachineColumn(
                column_index=i,
                powers=[0] * self.total_levels,
                counts=[1] * self.total_levels,
            )
            for i in range(self.total_columns)
        ]

    def simulate(self):
        self._initialize_environment()

        actions = []

        target_level = 0
        for turn in range(self.total_turns - 100):
            if turn % 10 == 10 - 1:
                progress = turn / (self.total_turns - 100)
                weights = [
                    max(0.01, 1 - abs(0 - 3 * progress) / 3),
                    max(0.01, 1 - abs(1 - 3 * progress) / 3),
                    max(0.01, 1 - abs(2 - 3 * progress) / 3),
                    max(0.01, 1 - abs(3 - 3 * progress) / 3),
                ]
                target_level = random.choices(range(self.total_levels), weights)[0]

            action = self._select_action(target_level)
            actions.append(action)

            self._step()

        actions.extend([None] * (self.total_turns - len(actions)))

        return actions

    def _select_action(self, target_level: int):
        if target_level == -1:
            return None

        # target_levelの中で、良い順にソートして、強化するマシンを決める
        # level = 0の時は、productivities[index] * counts[1] * (powers[1]+1)を見て、強化するマシンを決める
        # level > 0の時は、productivities[index] * powers[0] * ... * powers[level-1]を見て、強化するマシンを決める
        # そもそも0なら生産性がないので除外する

        scores = [self.productivities[i] for i in range(self.total_columns)]
        for machine_column in self.machine_columns:
            if target_level == 0:
                scores[machine_column.column_index] *= machine_column.counts[1] * (
                    machine_column.powers[1] + 1
                )
            for level in range(1, target_level + 1):
                scores[machine_column.column_index] *= machine_column.powers[level - 1]

        candidates = filter(
            lambda mc: scores[mc.column_index] > 0, self.machine_columns
        )

        candidates = sorted(
            candidates, key=lambda mc: scores[mc.column_index], reverse=True
        )
        if target_level > 0:
            candidates = candidates[:1]

        action = None
        for machine_column in candidates:
            cost = self.base_costs[
                target_level * self.total_columns + machine_column.column_index
            ] * (machine_column.powers[target_level] + 1)
            if self.apple >= cost:
                self.apple -= cost
                machine_column.powers[target_level] += 1

                action = (target_level, machine_column.column_index)

                break

        return action

    def _step(self):

        # アクション後の処理
        for machine_column in self.machine_columns:
            # level = 0 のときはりんごを生産する
            self.apple += (
                self.productivities[machine_column.column_index]
                * machine_column.counts[0]
                * machine_column.powers[0]
            )
            for level in range(1, self.total_levels):
                # level > 0 のときは、前のレベルのマシンを生産する
                machine_column.counts[level - 1] += (
                    machine_column.counts[level] * machine_column.powers[level]
                )


def main():
    TIME_LIMIT = 0.6
    time_start = time.perf_counter()

    n, l, t, k = map(int, input().split())
    a = list(map(int, input().split()))
    # c = [list(map(int, input().split())) for _ in range(l)]
    c = [list(map(int, input().split())) for _ in range(l)]
    c = list(itertools.chain.from_iterable(c))

    simulator = Simulator(
        initial_apples=k,
        total_columns=n,
        total_levels=l,
        total_turns=t,
        base_costs=c,
        productivities=a,
    )
    best_actions = simulator.simulate()
    best_score = simulator.apple

    iterations = 0
    while True:
        iterations += 1
        if iterations % 32 == 0:
            time_elapsed = time.perf_counter() - time_start
            if time_elapsed > TIME_LIMIT:
                break

        actions = simulator.simulate()
        score = simulator.apple
        if score > best_score:
            best_score = score
            best_actions = actions
            print(f"New best score: {best_score}", file=sys.stderr)

    print(
        "\n".join(
            f"{action[0]} {action[1]}" if action else "-1" for action in best_actions
        )
    )


if __name__ == "__main__":
    main()
