#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <queue>
#include <chrono>
#include <random>
#include <cmath>

using namespace std;

const int N = 20;
const int M = 50;
const int K = 10;
const int INF = 1e9;
const int MAX_SWITCHES = 25;

// 壁専用のゲート型と、ギミックに使えるスイッチの最大数
const int WALL_GATE_TYPE = 19; // k=9の閉じた扉
const int MAX_GIMMICK_GATES = 32;
const int MAX_WALL_GATES = M - MAX_GIMMICK_GATES; // 35個
const int AVAILABLE_SWITCH_TYPES = 9;             // k=0~8 をギミックに使用

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

bool can_place_gate(int d, int i, int j)
{
    if (d == 0)
    {
        if (i < 0 || i >= N - 1 || j < 0 || j >= N)
            return false;
        if (grid[i][j] == '#' || grid[i + 1][j] == '#')
            return false;
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

long long calculate_true_score(int T)
{
    if (T == -1)
        return 1;
    return round(1000000.0 * log2((double)T / (double)N));
}

// 評価関数
int evaluate()
{
    vector<int> check_pos;
    check_pos.push_back(0);
    check_pos.push_back(N * N - 1);

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

    int num_states = 1 << AVAILABLE_SWITCH_TYPES;
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
            return d;

        int ui = check_pos[u] / N;
        int uj = check_pos[u] % N;

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

        for (int dir = 0; dir < 4; ++dir)
        {
            int ni = ui + di[dir];
            int nj = uj + dj[dir];
            if (ni < 0 || ni >= N || nj < 0 || nj >= N)
                continue;
            if (grid[ni][nj] == '#')
                continue;

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

    return -1;
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

    vector<Gate> gimmick_gates;
    vector<Gate> wall_gates;
    vector<Switch> switches;

    int initial_T = evaluate();
    long long current_score = calculate_true_score(initial_T);
    long long best_score = current_score;

    vector<Gate> best_gimmick_gates = gimmick_gates;
    vector<Gate> best_wall_gates = wall_gates;
    vector<Switch> best_switches = switches;

    // --- 【フェーズ1】 焼きなまし（1800ms） ---
    auto sa_start_time = chrono::steady_clock::now();
    double sa_time_limit = 1800.0;
    double start_temp = 50000.0;
    double end_temp = 100.0;
    double elapsed = 0.0;

    uniform_real_distribution<double> prob(0.0, 1.0);
    int sa_iterations = 0;

    while (true)
    {
        if (sa_iterations % 16 == 0)
        {
            auto now = chrono::steady_clock::now();
            elapsed = chrono::duration_cast<chrono::milliseconds>(now - sa_start_time).count();
            if (elapsed > sa_time_limit)
                break;
        }
        sa_iterations++;

        if (sa_iterations % 1000 == 0)
        {
            cerr << "SA Iteration: " << sa_iterations << " | Best Score: " << best_score << " | Current Temp: " << start_temp + (end_temp - start_temp) * (elapsed / sa_time_limit) << endl;
        }

        double temp = start_temp + (end_temp - start_temp) * (elapsed / sa_time_limit);

        // SAは0〜8の操作（スイッチ移動を含まない）に集中
        int op = rng() % 9;

        Gate removed_gate = {0, 0, 0, 0};
        Switch removed_switch = {0, 0, 0};
        int old_val = -1;
        int d = -1, i = -1, j = -1, g = -1, si = -1, sj = -1, k = -1, idx = -1;

        if (op == 0)
        {
            if (wall_gates.size() >= MAX_WALL_GATES)
                continue;
            d = rng() % 2;
            i = rng() % N;
            j = rng() % N;
            if (!can_place_gate(d, i, j))
                continue;
            g = WALL_GATE_TYPE;
            if (d == 0)
                horizontal_gates[i][j] = g;
            else
                vertical_gates[i][j] = g;
            wall_gates.push_back({d, i, j, g});
        }
        else if (op == 1)
        {
            if (wall_gates.empty())
                continue;
            idx = rng() % wall_gates.size();
            removed_gate = wall_gates[idx];
            if (removed_gate.d == 0)
                horizontal_gates[removed_gate.i][removed_gate.j] = -1;
            else
                vertical_gates[removed_gate.i][removed_gate.j] = -1;
            wall_gates.erase(wall_gates.begin() + idx);
        }
        else if (op == 2)
        {
            if (gimmick_gates.size() >= MAX_GIMMICK_GATES)
                continue;
            d = rng() % 2;
            i = rng() % N;
            j = rng() % N;
            g = rng() % (2 * AVAILABLE_SWITCH_TYPES);
            if (!can_place_gate(d, i, j))
                continue;
            if (d == 0)
                horizontal_gates[i][j] = g;
            else
                vertical_gates[i][j] = g;
            gimmick_gates.push_back({d, i, j, g});
        }
        else if (op == 3)
        {
            if (gimmick_gates.empty())
                continue;
            idx = rng() % gimmick_gates.size();
            removed_gate = gimmick_gates[idx];
            if (removed_gate.d == 0)
                horizontal_gates[removed_gate.i][removed_gate.j] = -1;
            else
                vertical_gates[removed_gate.i][removed_gate.j] = -1;
            gimmick_gates.erase(gimmick_gates.begin() + idx);
        }
        else if (op == 4)
        {
            if (gimmick_gates.empty())
                continue;
            idx = rng() % gimmick_gates.size();
            old_val = gimmick_gates[idx].g;
            g = rng() % (2 * AVAILABLE_SWITCH_TYPES);
            if (old_val == g)
                continue;
            gimmick_gates[idx].g = g;
            if (gimmick_gates[idx].d == 0)
                horizontal_gates[gimmick_gates[idx].i][gimmick_gates[idx].j] = g;
            else
                vertical_gates[gimmick_gates[idx].i][gimmick_gates[idx].j] = g;
        }
        else if (op == 5)
        {
            if (switches.size() >= MAX_SWITCHES)
                continue;
            i = rng() % N;
            j = rng() % N;
            k = rng() % AVAILABLE_SWITCH_TYPES;
            if (!can_place_switch(i, j))
                continue;
            switch_type[i][j] = k;
            switches.push_back({i, j, k});
        }
        else if (op == 6)
        {
            if (switches.empty())
                continue;
            idx = rng() % switches.size();
            removed_switch = switches[idx];
            switch_type[removed_switch.p][removed_switch.q] = -1;
            switches.erase(switches.begin() + idx);
        }
        else if (op == 7)
        {
            if (switches.empty())
                continue;
            idx = rng() % switches.size();
            old_val = switches[idx].s;
            k = rng() % AVAILABLE_SWITCH_TYPES;
            if (old_val == k)
                continue;
            switches[idx].s = k;
            switch_type[switches[idx].p][switches[idx].q] = k;
        }
        else if (op == 8)
        {
            if (gimmick_gates.size() >= MAX_GIMMICK_GATES || switches.size() >= MAX_SWITCHES)
                continue;
            k = rng() % AVAILABLE_SWITCH_TYPES;
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
            gimmick_gates.push_back({d, i, j, g});
            switch_type[si][sj] = k;
            switches.push_back({si, sj, k});
        }

        bool accept = false;
        long long eval_score = -1;
        int new_T = evaluate();

        if (new_T != -1)
        {
            eval_score = calculate_true_score(new_T);
            double delta = (double)(eval_score - current_score);

            if (delta >= 0)
                accept = true;
            else if (prob(rng) < exp(delta / temp))
                accept = true;
        }

        if (accept)
        {
            current_score = eval_score;
            if (eval_score > best_score)
            {
                best_score = eval_score;
                best_gimmick_gates = gimmick_gates;
                best_wall_gates = wall_gates;
                best_switches = switches;
            }
        }
        else
        {
            if (op == 0)
            {
                if (d == 0)
                    horizontal_gates[i][j] = -1;
                else
                    vertical_gates[i][j] = -1;
                wall_gates.pop_back();
            }
            else if (op == 1)
            {
                if (removed_gate.d == 0)
                    horizontal_gates[removed_gate.i][removed_gate.j] = removed_gate.g;
                else
                    vertical_gates[removed_gate.i][removed_gate.j] = removed_gate.g;
                wall_gates.insert(wall_gates.begin() + idx, removed_gate);
            }
            else if (op == 2)
            {
                if (d == 0)
                    horizontal_gates[i][j] = -1;
                else
                    vertical_gates[i][j] = -1;
                gimmick_gates.pop_back();
            }
            else if (op == 3)
            {
                if (removed_gate.d == 0)
                    horizontal_gates[removed_gate.i][removed_gate.j] = removed_gate.g;
                else
                    vertical_gates[removed_gate.i][removed_gate.j] = removed_gate.g;
                gimmick_gates.insert(gimmick_gates.begin() + idx, removed_gate);
            }
            else if (op == 4)
            {
                gimmick_gates[idx].g = old_val;
                if (gimmick_gates[idx].d == 0)
                    horizontal_gates[gimmick_gates[idx].i][gimmick_gates[idx].j] = old_val;
                else
                    vertical_gates[gimmick_gates[idx].i][gimmick_gates[idx].j] = old_val;
            }
            else if (op == 5)
            {
                switch_type[i][j] = -1;
                switches.pop_back();
            }
            else if (op == 6)
            {
                switch_type[removed_switch.p][removed_switch.q] = removed_switch.s;
                switches.insert(switches.begin() + idx, removed_switch);
            }
            else if (op == 7)
            {
                switches[idx].s = old_val;
                switch_type[switches[idx].p][switches[idx].q] = old_val;
            }
            else if (op == 8)
            {
                if (d == 0)
                    horizontal_gates[i][j] = -1;
                else
                    vertical_gates[i][j] = -1;
                gimmick_gates.pop_back();
                switch_type[si][sj] = -1;
                switches.pop_back();
            }
        }
    }
    cerr << "--- SA Finished ---" << endl;

    // --- 【フェーズ2】 スイッチ移動専用・山登り法（100ms） ---
    // まず盤面をベスト状態にリセット
    gimmick_gates = best_gimmick_gates;
    wall_gates = best_wall_gates;
    switches = best_switches;
    current_score = best_score;

    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j)
        {
            horizontal_gates[i][j] = -1;
            vertical_gates[i][j] = -1;
            switch_type[i][j] = -1;
        }
    for (auto &g : gimmick_gates)
    {
        if (g.d == 0)
            horizontal_gates[g.i][g.j] = g.g;
        else
            vertical_gates[g.i][g.j] = g.g;
    }
    for (auto &g : wall_gates)
    {
        if (g.d == 0)
            horizontal_gates[g.i][g.j] = g.g;
        else
            vertical_gates[g.i][g.j] = g.g;
    }
    for (auto &s : switches)
    {
        switch_type[s.p][s.q] = s.s;
    }

    cerr << "--- Starting Switch Hill Climbing (100ms) ---" << endl;
    auto hc_start_time = chrono::steady_clock::now();
    double hc_time_limit = 100.0;
    int hc_iterations = 0;

    while (true)
    {
        if (hc_iterations % 16 == 0)
        {
            auto now = chrono::steady_clock::now();
            if (chrono::duration_cast<chrono::milliseconds>(now - hc_start_time).count() > hc_time_limit)
                break;
        }
        hc_iterations++;

        if (switches.empty())
            break;
        int idx = rng() % switches.size();
        int old_i = switches[idx].p;
        int old_j = switches[idx].q;

        int dir = rng() % 4;
        int new_i = old_i + di[dir];
        int new_j = old_j + dj[dir];

        if (!can_place_switch(new_i, new_j))
            continue;

        // スイッチを1マス移動
        switch_type[old_i][old_j] = -1;
        switch_type[new_i][new_j] = switches[idx].s;
        switches[idx].p = new_i;
        switches[idx].q = new_j;

        int new_T = evaluate();
        bool accept = false;

        if (new_T != -1)
        {
            long long eval_score = calculate_true_score(new_T);
            // 山登りなので、スコアが同値以上なら採用（平坦な場所も歩き回って袋小路を探す）
            if (eval_score >= current_score)
            {
                accept = true;
                current_score = eval_score;
                if (eval_score > best_score)
                {
                    best_score = eval_score;
                    best_switches = switches; // スイッチ位置のみ更新
                }
            }
        }

        if (!accept)
        {
            // ロールバック
            switch_type[new_i][new_j] = -1;
            switch_type[old_i][old_j] = switches[idx].s;
            switches[idx].p = old_i;
            switches[idx].q = old_j;
        }
    }

    cerr << "--- HC Finished ---" << endl;
    cerr << "HC Iterations: " << hc_iterations << endl;
    cerr << "Final Best Score: " << best_score << endl;

    // 出力
    cout << best_gimmick_gates.size() + best_wall_gates.size() << "\n";
    for (const auto &g : best_gimmick_gates)
        cout << g.d << " " << g.i << " " << g.j << " " << g.g << "\n";
    for (const auto &g : best_wall_gates)
        cout << g.d << " " << g.i << " " << g.j << " " << g.g << "\n";

    cout << best_switches.size() << "\n";
    for (const auto &s : best_switches)
        cout << s.p << " " << s.q << " " << s.s << "\n";

    return 0;
}