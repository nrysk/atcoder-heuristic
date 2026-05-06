"""
BeamSearchを用いた解法
"""

import sys
import time
import random
from typing import NamedTuple


class State(NamedTuple):
    last_chest_index: int
    sum_actions: int
    estimated_score: int  # これまでの行動数 + 宝箱の合計HP
    parent: "State | None"


def solve(n: int, h: list[int], c: list[int], a: list[list[int]]) -> State:
    pass


def main():

    n = int(input())  # 宝箱の個数
    h = list(map(int, input().split()))  # 宝箱のHP 宝箱iを壊せば武器iが手に入る
    c = list(map(int, input().split()))  # 武器の耐久値
    a = [
        list(map(int, input().split())) for _ in range(n)
    ]  # 武器iで宝箱jを攻撃したときのダメージ 武器=-1で攻撃力1の素手

    print("\n".join(f"{w} {b}" for w, b in best_result))


if __name__ == "__main__":
    main()
