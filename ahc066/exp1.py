"""
文字列から複数回出現する部分文字列を抽出する実験
"""

import sys
import time
from collections import Counter


def get_most_frequent_fixed_pattern(s: str, length: int) -> tuple[str, int]:
    """指定された長さ(length)の中で、最も登場回数が多い部分文字列とその回数を返す"""
    if len(s) < length or length <= 0:
        return "", 0

    counts = Counter()
    for i in range(len(s) - length + 1):
        substring = s[i : i + length]
        counts[substring] += 1

    # 最もカウントが多いものを1つ取得
    best_pattern, max_freq = counts.most_common(1)[0]
    return best_pattern, max_freq


def count_overlapping_free(s: str, pattern: str) -> int:
    """指定したパターンが、文字の重なり（重複）なしで何回登場するかを厳密に数える"""
    if not pattern:
        return 0

    count = 0
    i = 0
    while i <= len(s) - len(pattern):
        # パターンがマッチしたら、そのパターンの長さ分一気に進む（ワープする）
        if s[i : i + len(pattern)] == pattern:
            count += 1
            i += len(pattern)
        else:
            i += 1
    return count


def find_best_macro_pattern(
    s: str, min_len: int = 2, max_len: int = 8
) -> tuple[str, int]:
    """
    重複なしカウントをベースに、一番手数が浮く(Gainが最大の)部分文字列を探索する。

    Gain = 重複なし登場回数 * (文字数 - 1) - 2 (マクロ登録ペナルティ)
    """
    best_pattern = ""
    max_gain = 0

    # 候補を洗い出すために、まずは通常の切り出しで出現した文字列のリストを作る
    candidates = set()
    for length in range(min_len, max_len + 1):
        for i in range(len(s) - length + 1):
            candidates.add(s[i : i + length])

    # 各候補について、重なりなしの厳密な Gain を計算
    for pattern in candidates:
        freq = count_overlapping_free(s, pattern)

        # 得する手数（Gain）の計算
        gain = freq * (len(pattern) - 1) - 2

        if gain > max_gain:
            max_gain = gain
            best_pattern = pattern

    return best_pattern, max_gain


def main():
    input_data = sys.stdin.read().split(sep="\n")

    input_str = "".join(input_data[:-1])  # 最後の空行を除いて結合
    print(f"Input string length: {len(input_str)}")

    time_start = time.perf_counter()
    pattern_length = 10  # 部分文字列の長さを指定
    pattern, frequency = get_most_frequent_fixed_pattern(input_str, pattern_length)
    time_end = time.perf_counter()
    print(
        f"Most frequent pattern of length {pattern_length}: '{pattern}' (appears {frequency} times) - found in {time_end - time_start:.4f} seconds"
    )

    time_start = time.perf_counter()
    non_overlapping_count = count_overlapping_free(input_str, pattern)
    time_end = time.perf_counter()
    print(
        f"Non-overlapping occurrences of pattern '{pattern}': {non_overlapping_count}  - counted in {time_end - time_start:.4f} seconds"
    )

    time_start = time.perf_counter()
    best_pattern, max_gain = find_best_macro_pattern(input_str)
    time_end = time.perf_counter()
    print(
        f"Best macro pattern: '{best_pattern}' with gain {max_gain} - found in {time_end - time_start:.4f} seconds"
    )


if __name__ == "__main__":
    main()
