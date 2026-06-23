#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <queue>
#include <chrono>
#include <random>
#include <cmath>

using namespace std;

// 問題の制約定数
const int N = 20;
const int M = 50;
const int K = 10;
const int INF = 1e9;
const int MAX_SWITCHES = 25;

struct Gate
{
    int d, i, j, g;
};

struct Switch
{
    int p, q, s;
};

char grid[N][N];
int horizontal_gates[N][N];
int vertical_gates[N][N];
int switch_type[N][N];

int di[] = {-1, 1, 0, 0};
int dj[] = {0, 0, -1, 1};

mt19937 rng(42);

bool is_gate_open(int g, int mask)
{
    int k = g / 2;
    int is_odd = g % 2;
    int active = (mask >> k) & 1;
    return is_odd ? (active == 1) : (active == 0);
}

// ★ 追加：扉を置ける場所かどうかの厳格なチェック（壁抜けバグ防止）
bool can_place_gate(int d, int i, int j)
{
    if (d == 0)
    {
        if (i < 0 || i >= N - 1 || j < 0 || j >= N)
            return false;
        if (grid[i][j] == '#' || grid[i + 1][j] == '#')
            return false; // 障害物には絶対に接させない
        if (horizontal_gates[i][j] != -1)
            return false;
    }
    else
    {
        if (i < 0 || i >= N || j < 0 || j >= N - 1)
            return false;
        if (grid[i][j] == '#' || grid[i][j + 1] == '#')
            return false;
        if (vertical_gates[i][j] != -1)
            return false;
    }
    return true;
}

// ★ 追加：スイッチを置ける場所かどうかのチェック
bool can_place_switch(int i, int j)
{
    if (i < 0 || i >= N || j < 0 || j >= N)
        return false;
    if (grid[i][j] == '#')
        return false;
    if (switch_type[i][j] != -1)
        return false;
    return true;
}

// 運営のルールに基づく得点計算関数
long long calculate_true_score(int T)
{
    if (T == -1)
        return 1;
    return round(1000000.0 * log2((double)T / (double)N));
}

// マクログラフによる最短手数 (T) の計算関数
int evaluate()
{
    vector<int> check_pos;
    check_pos.push_back(0);         // (0,0)
    check_pos.push_back(N * N - 1); // (N-1, N-1)

    for (int i = 0; i < N; ++i)
    {
        for (int j = 0; j < N; ++j)
        {
            if (switch_type[i][j] != -1)
                check_pos.push_back(i * N + j);
            if (horizontal_gates[i][j] != -1)
            {
                check_pos.push_back(i * N + j);
                check_pos.push_back((i + 1) * N + j);
            }
            if (vertical_gates[i][j] != -1)
            {
                check_pos.push_back(i * N + j);
                check_pos.push_back(i * N + (j + 1));
            }
        }
    }

    sort(check_pos.begin(), check_pos.end());
    check_pos.erase(unique(check_pos.begin(), check_pos.end()), check_pos.end());

    int P = check_pos.size();
    vector<int> pos_to_id(N * N, -1);
    for (int i = 0; i < P; ++i)
        pos_to_id[check_pos[i]] = i;

    // BFSによる部屋内の距離計算
    vector<vector<pair<int, int>>> adj(P);
    for (int u = 0; u < P; ++u)
    {
        int si = check_pos[u] / N;
        int sj = check_pos[u] % N;

        vector<vector<int>> d(N, vector<int>(N, INF));
        queue<pair<int, int>> q;
        d[si][sj] = 0;
        q.push({si, sj});

        while (!q.empty())
        {
            auto [ci, cj] = q.front();
            q.pop();

            int cid = pos_to_id[ci * N + cj];
            if (cid != -1 && cid != u)
            {
                adj[u].push_back({cid, d[ci][cj]});
            }

            for (int dir = 0; dir < 4; ++dir)
            {
                int ni = ci + di[dir];
                int nj = cj + dj[dir];

                if (ni < 0 || ni >= N || nj < 0 || nj >= N)
                    continue;
                if (grid[ni][nj] == '#')
                    continue;

                bool has_gate = false;
                if (dir == 0 && horizontal_gates[ni][nj] != -1)
                    has_gate = true;
                if (dir == 1 && horizontal_gates[ci][cj] != -1)
                    has_gate = true;
                if (dir == 2 && vertical_gates[ni][nj] != -1)
                    has_gate = true;
                if (dir == 3 && vertical_gates[ci][cj] != -1)
                    has_gate = true;

                if (has_gate)
                    continue;

                if (d[ni][nj] == INF)
                {
                    d[ni][nj] = d[ci][cj] + 1;
                    q.push({ni, nj});
                }
            }
        }
    }

    // ダイクストラ法
    int num_states = 1 << K;
    vector<vector<int>> dist(P, vector<int>(num_states, INF));
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> pq;

    int start_id = pos_to_id[0];
    int goal_id = pos_to_id[N * N - 1];

    dist[start_id][0] = 0;
    pq.push({0, start_id * num_states + 0});

    while (!pq.empty())
    {
        auto [d, state] = pq.top();
        pq.pop();

        int u = state / num_states;
        int mask = state % num_states;

        if (d > dist[u][mask])
            continue;
        if (u == goal_id)
            return d; // ゴール到達で即終了

        int ui = check_pos[u] / N;
        int uj = check_pos[u] % N;

        // 遷移1: スイッチを押す
        if (switch_type[ui][uj] != -1)
        {
            int s = switch_type[ui][uj];
            int next_mask = mask ^ (1 << s);
            if (d + 1 < dist[u][next_mask])
            {
                dist[u][next_mask] = d + 1;
                pq.push({d + 1, u * num_states + next_mask});
            }
        }

        // 遷移2: 歩行移動
        for (auto &edge : adj[u])
        {
            int v = edge.first;
            int cost = edge.second;
            if (d + cost < dist[v][mask])
            {
                dist[v][mask] = d + cost;
                pq.push({d + cost, v * num_states + mask});
            }
        }

        // 遷移3: 扉を通る
        for (int dir = 0; dir < 4; ++dir)
        {
            int ni = ui + di[dir];
            int nj = uj + dj[dir];
            if (ni < 0 || ni >= N || nj < 0 || nj >= N)
                continue;
            if (grid[ni][nj] == '#')
                continue; // ★ 二重の壁抜け防止措置

            int gate_g = -1;
            if (dir == 0 && horizontal_gates[ni][nj] != -1)
                gate_g = horizontal_gates[ni][nj];
            if (dir == 1 && horizontal_gates[ui][uj] != -1)
                gate_g = horizontal_gates[ui][uj];
            if (dir == 2 && vertical_gates[ni][nj] != -1)
                gate_g = vertical_gates[ni][nj];
            if (dir == 3 && vertical_gates[ui][uj] != -1)
                gate_g = vertical_gates[ui][uj];

            if (gate_g != -1 && is_gate_open(gate_g, mask))
            {
                int v = pos_to_id[ni * N + nj];
                if (v != -1 && d + 1 < dist[v][mask])
                {
                    dist[v][mask] = d + 1;
                    pq.push({d + 1, v * num_states + mask});
                }
            }
        }
    }

    return -1; // ゴールに到達不能
}

int main()
{
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int dummy_N, dummy_M, dummy_K;
    if (!(cin >> dummy_N >> dummy_M >> dummy_K))
        return 0;

    for (int i = 0; i < N; ++i)
    {
        for (int j = 0; j < N; ++j)
        {
            cin >> grid[i][j];
            horizontal_gates[i][j] = -1;
            vertical_gates[i][j] = -1;
            switch_type[i][j] = -1;
        }
    }

    vector<Gate> gates;
    vector<Switch> switches;

    // ★ 初期解は完全に「空（から）」の状態から始める（到達不能によるスタックを防止）
    int initial_T = evaluate();
    long long current_score = calculate_true_score(initial_T);
    long long best_score = current_score;

    vector<Gate> best_gates = gates;
    vector<Switch> best_switches = switches;

    auto start_time = chrono::steady_clock::now();
    double time_limit = 1800.0;
    double start_temp = 50000.0;
    double end_temp = 100.0;
    double elapsed = 0.0;

    uniform_real_distribution<double> prob(0.0, 1.0);
    int iterations = 0;

    while (true)
    {
        if (iterations % 16 == 0)
        {
            auto now = chrono::steady_clock::now();
            elapsed = chrono::duration_cast<chrono::milliseconds>(now - start_time).count();
            if (elapsed > time_limit)
                break;
        }
        iterations++;

        if (iterations % 1000 == 0)
        {
            cerr << "Iteration: " << iterations << " | Best Score: " << best_score << " | Current Temp: " << start_temp + (end_temp - start_temp) * (elapsed / time_limit) << endl;
        }

        double temp = start_temp + (end_temp - start_temp) * (elapsed / time_limit);
        int op = rng() % 7;

        Gate removed_gate = {0, 0, 0, 0};
        Switch removed_switch = {0, 0, 0};
        int old_val = -1;
        int d = -1, i = -1, j = -1, g = -1, si = -1, sj = -1, k = -1, idx = -1;

        if (op == 0)
        {
            if (gates.size() >= M)
                continue;
            d = rng() % 2;
            i = rng() % N;
            j = rng() % N;
            g = rng() % (2 * K);
            if (!can_place_gate(d, i, j))
                continue;
            if (d == 0)
                horizontal_gates[i][j] = g;
            else
                vertical_gates[i][j] = g;
            gates.push_back({d, i, j, g});
        }
        else if (op == 1)
        {
            if (gates.empty())
                continue;
            idx = rng() % gates.size();
            removed_gate = gates[idx];
            if (removed_gate.d == 0)
                horizontal_gates[removed_gate.i][removed_gate.j] = -1;
            else
                vertical_gates[removed_gate.i][removed_gate.j] = -1;
            gates.erase(gates.begin() + idx);
        }
        else if (op == 2)
        {
            if (gates.empty())
                continue;
            idx = rng() % gates.size();
            old_val = gates[idx].g;
            g = rng() % (2 * K);
            if (old_val == g)
                continue;
            gates[idx].g = g;
            if (gates[idx].d == 0)
                horizontal_gates[gates[idx].i][gates[idx].j] = g;
            else
                vertical_gates[gates[idx].i][gates[idx].j] = g;
        }
        else if (op == 3)
        {
            if (switches.size() >= MAX_SWITCHES)
                continue;
            i = rng() % N;
            j = rng() % N;
            k = rng() % K;
            if (!can_place_switch(i, j))
                continue;
            switch_type[i][j] = k;
            switches.push_back({i, j, k});
        }
        else if (op == 4)
        {
            if (switches.empty())
                continue;
            idx = rng() % switches.size();
            removed_switch = switches[idx];
            switch_type[removed_switch.p][removed_switch.q] = -1;
            switches.erase(switches.begin() + idx);
        }
        else if (op == 5)
        {
            if (switches.empty())
                continue;
            idx = rng() % switches.size();
            old_val = switches[idx].s;
            k = rng() % K;
            if (old_val == k)
                continue;
            switches[idx].s = k;
            switch_type[switches[idx].p][switches[idx].q] = k;
        }
        else if (op == 6)
        {
            if (gates.size() >= M || switches.size() >= MAX_SWITCHES)
                continue;
            k = rng() % K;
            g = 2 * k + 1;
            d = rng() % 2;
            i = rng() % N;
            j = rng() % N;
            if (!can_place_gate(d, i, j))
                continue;

            si = rng() % N;
            sj = rng() % N;
            if (!can_place_switch(si, sj))
                continue;

            if (d == 0)
                horizontal_gates[i][j] = g;
            else
                vertical_gates[i][j] = g;
            gates.push_back({d, i, j, g});
            switch_type[si][sj] = k;
            switches.push_back({si, sj, k});
        }

        bool accept = false;
        long long eval_score = -1;
        int new_T = evaluate();

        // ★ 変更：到達不能（-1）になった場合は、確率計算すらさせずに「絶対に」却下する
        if (new_T != -1)
        {
            eval_score = calculate_true_score(new_T);
            double delta = (double)(eval_score - current_score);

            if (delta >= 0)
            {
                accept = true;
            }
            else
            {
                if (prob(rng) < exp(delta / temp))
                    accept = true;
            }
        }

        if (accept)
        {
            current_score = eval_score;
            if (eval_score > best_score)
            {
                best_score = eval_score;
                best_gates = gates;
                best_switches = switches;
            }
        }
        else
        {
            // ロールバック
            if (op == 0)
            {
                if (d == 0)
                    horizontal_gates[i][j] = -1;
                else
                    vertical_gates[i][j] = -1;
                gates.pop_back();
            }
            else if (op == 1)
            {
                if (removed_gate.d == 0)
                    horizontal_gates[removed_gate.i][removed_gate.j] = removed_gate.g;
                else
                    vertical_gates[removed_gate.i][removed_gate.j] = removed_gate.g;
                gates.insert(gates.begin() + idx, removed_gate);
            }
            else if (op == 2)
            {
                gates[idx].g = old_val;
                if (gates[idx].d == 0)
                    horizontal_gates[gates[idx].i][gates[idx].j] = old_val;
                else
                    vertical_gates[gates[idx].i][gates[idx].j] = old_val;
            }
            else if (op == 3)
            {
                switch_type[i][j] = -1;
                switches.pop_back();
            }
            else if (op == 4)
            {
                switch_type[removed_switch.p][removed_switch.q] = removed_switch.s;
                switches.insert(switches.begin() + idx, removed_switch);
            }
            else if (op == 5)
            {
                switches[idx].s = old_val;
                switch_type[switches[idx].p][switches[idx].q] = old_val;
            }
            else if (op == 6)
            {
                if (d == 0)
                    horizontal_gates[i][j] = -1;
                else
                    vertical_gates[i][j] = -1;
                gates.pop_back();
                switch_type[si][sj] = -1;
                switches.pop_back();
            }
        }
    }

    cerr << "--- Finished ---" << endl;
    cerr << "Total Iterations: " << iterations << endl;
    cerr << "Final Best Score: " << best_score << endl;

    cout << best_gates.size() << "\n";
    for (const auto &g : best_gates)
        cout << g.d << " " << g.i << " " << g.j << " " << g.g << "\n";
    cout << best_switches.size() << "\n";
    for (const auto &s : best_switches)
        cout << s.p << " " << s.q << " " << s.s << "\n";

    return 0;
}