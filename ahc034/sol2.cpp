#include <iostream>
#include <vector>
#include <cmath>
#include <random>
#include <chrono>
#include <algorithm>
#include <string>

using namespace std;

// 元のコードの copy_list を再現
void copy_list(const vector<int>& from_list, vector<int>& to_list) {
    for (size_t i = 0; i < from_list.size(); ++i) {
        to_list[i] = from_list[i];
    }
}

class Solver {
private:
    int n;
    vector<int> initial_h;
    vector<int> h;
    int initial_zero_count;
    int zero_count;
    mt19937 rng; // 高速な乱数生成器

    void _reset() {
        zero_count = initial_zero_count;
        for (int i = 0; i < n * n; ++i) {
            h[i] = initial_h[i];
        }
    }

    // 経路の評価関数
    long long _evaluate_route(const vector<int>& route) {
        _reset();
        long long current_load = 0;
        long long cost = 0;
        int current_pos = 0;

        for (int next_pos : route) {
            int cy = current_pos / n;
            int cx = current_pos % n;
            int ny = next_pos / n;
            int nx = next_pos % n;

            long long move_cost = (100 + current_load) * (abs(cy - ny) + abs(cx - nx));
            cost += move_cost;

            if (h[next_pos] > 0) {
                cost += h[next_pos];
                current_load += h[next_pos];
                h[next_pos] = 0;
                zero_count--;
            } else if (h[next_pos] < 0) {
                if (h[next_pos] + current_load >= 0) {
                    cost += -h[next_pos];
                    current_load += h[next_pos];
                    h[next_pos] = 0;
                    zero_count--;
                } else if (h[next_pos] + current_load < 0) {
                    cost += current_load;
                    h[next_pos] += current_load;
                    current_load = 0;
                }
            }

            current_pos = next_pos;

            if (zero_count == n * n) {
                break;
            }
        }

        return cost + (static_cast<long long>(zero_count) * 1000000);
    }

    vector<string> _calc_move(int from_pos, int to_pos) {
        int from_y = from_pos / n;
        int from_x = from_pos % n;
        int to_y = to_pos / n;
        int to_x = to_pos % n;

        vector<string> move_ops;
        if (from_y > to_y) move_ops.insert(move_ops.end(), from_y - to_y, "U");
        if (to_y > from_y) move_ops.insert(move_ops.end(), to_y - from_y, "D");
        if (from_x > to_x) move_ops.insert(move_ops.end(), from_x - to_x, "L");
        if (to_x > from_x) move_ops.insert(move_ops.end(), to_x - from_x, "R");
        return move_ops;
    }

    // 最終的な操作列へのデコード
    vector<string> _decode_route(const vector<int>& route) {
        _reset();
        vector<string> operations;
        long long current_load = 0;
        int current_pos = 0;

        for (int next_pos : route) {
            vector<string> move = _calc_move(current_pos, next_pos);
            operations.insert(operations.end(), move.begin(), move.end());

            if (h[next_pos] > 0) {
                operations.push_back("+" + to_string(h[next_pos]));
                current_load += h[next_pos];
                h[next_pos] = 0;
                zero_count--;
            } else if (h[next_pos] < 0) {
                if (h[next_pos] + current_load >= 0) {
                    operations.push_back("-" + to_string(-h[next_pos]));
                    current_load += h[next_pos];
                    h[next_pos] = 0;
                    zero_count--;
                } else if (current_load != 0 && h[next_pos] + current_load < 0) {
                    operations.push_back("-" + to_string(current_load));
                    h[next_pos] += current_load;
                    current_load = 0;
                }
            }

            current_pos = next_pos;
        }

        return operations;
    }

public:
    Solver(int n, const vector<int>& h_in) : n(n), initial_h(h_in), h(h_in), rng(1337) {
        initial_zero_count = 0;
        for (int i = 0; i < n * n; ++i) {
            if (h_in[i] == 0) initial_zero_count++;
        }
        zero_count = initial_zero_count;
    }

    vector<string> solve() {
        double MIN_TEMP = 0.01;
        double MAX_TEMP = 100.0;
        double TIME_LIMIT = 1.7;

        // 高精度な時間計測
        auto time_start = chrono::high_resolution_clock::now();

        vector<int> best_route(n * n);
        for (int i = 0; i < n * n; ++i) best_route[i] = i;

        long long best_cost = _evaluate_route(best_route);
        vector<int> current_route = best_route;
        long long current_cost = best_cost;

        long long itr = 0;
        double temp = MAX_TEMP;

        uniform_real_distribution<double> dist_01(0.0, 1.0);
        uniform_int_distribution<int> dist_idx(0, n * n - 1);

        while (true) {
            itr++;
            if (itr % 2000 == 0) {
                auto time_now = chrono::high_resolution_clock::now();
                double elapsed_time = chrono::duration<double>(time_now - time_start).count();
                if (elapsed_time > TIME_LIMIT) {
                    break;
                }
                double progress = elapsed_time / TIME_LIMIT;
                temp = MAX_TEMP + (MIN_TEMP - MAX_TEMP) * progress;
            }

            vector<int> new_route = current_route;
            double r = dist_01(rng);

            if (r < 0.2) {
                // Swap
                int i = dist_idx(rng);
                int j = dist_idx(rng);
                while (i == j) j = dist_idx(rng);
                swap(new_route[i], new_route[j]);
            } else if (r < 0.5) {
                // Reverse
                int i = dist_idx(rng);
                int j = dist_idx(rng);
                while (i == j) j = dist_idx(rng);
                if (i > j) swap(i, j);
                reverse(new_route.begin() + i, new_route.begin() + j + 1);
            } else {
                // Shift (Or-opt風の区間移動。修正されたPython版に準拠)
                int i = dist_idx(rng);
                int j = dist_idx(rng);
                while (i == j) j = dist_idx(rng);
                if (i > j) swap(i, j);

                vector<int> next_route;
                next_route.reserve(n * n);
                // new_route[:i]
                for (int k = 0; k < i; ++k) next_route.push_back(current_route[k]);
                // new_route[j+1:]
                for (int k = j + 1; k < n * n; ++k) next_route.push_back(current_route[k]);
                // new_route[i:j+1]
                for (int k = i; k <= j; ++k) next_route.push_back(current_route[k]);
                
                new_route = move(next_route);
            }

            long long new_cost = _evaluate_route(new_route);
            long long delta = new_cost - current_cost;

            if (delta < 0 || dist_01(rng) < exp(-delta / temp)) {
                current_route = new_route;
                current_cost = new_cost;

                if (current_cost < best_cost) {
                    cerr << "ITR: " << itr << ", BEST COST: " << best_cost << " -> " << current_cost << "\n";
                    copy_list(current_route, best_route);
                    best_cost = current_cost;
                }
            }
        }

        cerr << "TOTAL ITR: " << itr << ", BEST COST: " << best_cost << "\n";

        return _decode_route(best_route);
    }
};

int main() {
    // 入出力の高速化
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int n;
    if (!(cin >> n)) return 0;

    vector<int> h(n * n);
    for (int i = 0; i < n * n; ++i) {
        cin >> h[i];
    }

    Solver solver(n, h);
    vector<string> operations = solver.solve();

    for (const string& op : operations) {
        cout << op << "\n";
    }

    return 0;
}