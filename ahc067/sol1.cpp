#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <queue>
#include <chrono>
#include <random>

using namespace std;

// 問題の制約定数
const int N = 20;
const int M = 50;
const int K = 10;
const int INF = 1e9;
const int MAX_SWITCHES = 25; // 探索を高速に保つためのスイッチ設置数の上限

struct Gate
{
    int d, i, j, g;
};

struct Switch
{
    int p, q, s;
};

// グリッドと配置情報
char grid[N][N];
int horizontal_gates[N][N]; // (i, j) と (i+1, j) の間の扉の型 (-1は無し)
int vertical_gates[N][N];   // (i, j) と (i, j+1) の間の扉の型 (-1は無し)
int switch_type[N][N];      // マス (i, j) にあるスイッチの種類 (-1は無し)

// 方向ベクトル
int di[] = {-1, 1, 0, 0};
int dj[] = {0, 0, -1, 1};

mt19937 rng(42);

// 扉が開いているかどうかの判定
bool is_gate_open(int g, int mask)
{
    int k = g / 2;
    int is_odd = g % 2;
    int active = (mask >> k) & 1;
    return is_odd ? (active == 1) : (active == 0);
}

// アプローチA: マクログラフを構築して勇者の最短手数を評価する関数
int evaluate()
{
    // 1. 重要地点（チェックポイント）の列挙
    vector<int> checkpoints;
    checkpoints.push_back(0);         // スタート (0,0)
    checkpoints.push_back(N * N - 1); // ゴール (N-1, N-1)

    for (int i = 0; i < N; ++i)
    {
        for (int j = 0; j < N; ++j)
        {
            if (switch_type[i][j] != -1)
            {
                checkpoints.push_back(i * N + j);
            }
            if (horizontal_gates[i][j] != -1)
            {
                checkpoints.push_back(i * N + j);
                checkpoints.push_back((i + 1) * N + j);
            }
            if (vertical_gates[i][j] != -1)
            {
                checkpoints.push_back(i * N + j);
                checkpoints.push_back(i * N + (j + 1));
            }
        }
    }

    sort(checkpoints.begin(), checkpoints.end());
    checkpoints.erase(unique(checkpoints.begin(), checkpoints.end()), checkpoints.end());

    int P = checkpoints.size();
    vector<int> pos_to_id(N * N, -1);
    for (int i = 0; i < P; ++i)
    {
        pos_to_id[checkpoints[i]] = i;
    }

    // 2. 地続きの隣接チェックポイント間の最短距離をBFSで計算（扉は通らない）
    vector<vector<pair<int, int>>> adj_macro(P);
    for (int u = 0; u < P; ++u)
    {
        int start_pos = checkpoints[u];
        int si = start_pos / N, sj = start_pos % N;

        vector<vector<int>> d(N, vector<int>(N, INF));
        queue<pair<int, int>> q;
        d[si][sj] = 0;
        q.push({si, sj});

        while (!q.empty())
        {
            auto [cur_i, cur_j] = q.front();
            q.pop();

            int cur_pos = cur_i * N + cur_j;
            int cur_id = pos_to_id[cur_pos];

            // 他のチェックポイントに到達したら、その先への探索は打ち切る（縮約高速化）
            if (cur_id != -1 && cur_id != u)
            {
                adj_macro[u].push_back({cur_id, d[cur_i][cur_j]});
                continue;
            }

            for (int dir = 0; dir < 4; ++dir)
            {
                int ni = cur_i + di[dir];
                int nj = cur_j + dj[dir];

                if (ni < 0 || ni >= N || nj < 0 || nj >= N)
                    continue;
                if (grid[ni][nj] == '#')
                    continue;

                // 扉による遮断チェック（地続き移動では扉を一切通れない）
                bool has_gate = false;
                if (dir == 0 && horizontal_gates[ni][nj] != -1)
                    has_gate = true;
                if (dir == 1 && horizontal_gates[cur_i][cur_j] != -1)
                    has_gate = true;
                if (dir == 2 && vertical_gates[ni][nj] != -1)
                    has_gate = true;
                if (dir == 3 && vertical_gates[cur_i][cur_j] != -1)
                    has_gate = true;

                if (has_gate)
                    continue;

                if (d[ni][nj] == INF)
                {
                    d[ni][nj] = d[cur_i][cur_j] + 1;
                    q.push({ni, nj});
                }
            }
        }
    }

    // 3. 縮約されたマクログラフ上でのダイクストラ法
    int num_states = 1 << K; // 1024通り
    vector<vector<int>> dist_macro(P, vector<int>(num_states, INF));
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> pq;

    int start_id = pos_to_id[0];
    int goal_id = pos_to_id[N * N - 1];

    dist_macro[start_id][0] = 0;
    pq.push({0, start_id * num_states + 0});

    while (!pq.empty())
    {
        auto [d, state] = pq.top();
        pq.pop();

        int u = state / num_states;
        int mask = state % num_states;

        if (d > dist_macro[u][mask])
            continue;

        // 遷移A: 同じ部屋（地続き）の隣接チェックポイントへの移動
        for (auto &edge : adj_macro[u])
        {
            int v = edge.first;
            int cost = edge.second;
            if (d + cost < dist_macro[v][mask])
            {
                dist_macro[v][mask] = d + cost;
                pq.push({d + cost, v * num_states + mask});
            }
        }

        int u_pos = checkpoints[u];
        int ui = u_pos / N, uj = u_pos % N;

        // 遷移B: 現在のマスにあるスイッチを押す
        if (switch_type[ui][uj] != -1)
        {
            int s = switch_type[ui][uj];
            int next_mask = mask ^ (1 << s);
            if (d + 1 < dist_macro[u][next_mask])
            {
                dist_macro[u][next_mask] = d + 1;
                pq.push({d + 1, u * num_states + next_mask});
            }
        }

        // 遷移C: 隣接する扉をまたいで別の部屋へ移動
        for (int dir = 0; dir < 4; ++dir)
        {
            int ni = ui + di[dir];
            int nj = uj + dj[dir];
            if (ni < 0 || ni >= N || nj < 0 || nj >= N)
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
                if (v != -1 && d + 1 < dist_macro[v][mask])
                {
                    dist_macro[v][mask] = d + 1;
                    pq.push({d + 1, v * num_states + mask});
                }
            }
        }
    }

    // すべてのスイッチ状態におけるゴールへの最短手数の最小値を返す
    int min_total_cost = INF;
    for (int mask = 0; mask < num_states; ++mask)
    {
        min_total_cost = min(min_total_cost, dist_macro[goal_id][mask]);
    }

    return (min_total_cost == INF) ? -1 : min_total_cost;
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
    int best_score = evaluate();

    // 【追加】初期解としてあらかじめいくつかランダムな場所にギミックのペアを無理やりねじ込む
    for (int k = 0; k < K; ++k)
    {
        int g = 2 * k + 1; // 初期状態：閉
        int d = rng() % 2;
        int i = rng() % N, j = rng() % N;
        int si = rng() % N, sj = rng() % N;

        if (d == 0 && (i >= N - 1 || j >= N))
            continue;
        if (d == 1 && (i >= N || j >= N - 1))
            continue;
        if (grid[si][sj] == '#' || (si == 0 && sj == 0))
            continue;

        if (d == 0 && horizontal_gates[i][j] == -1)
            horizontal_gates[i][j] = g;
        else if (d == 1 && vertical_gates[i][j] == -1)
            vertical_gates[i][j] = g;
        else
            continue;

        if (switch_type[si][sj] == -1)
            switch_type[si][sj] = k;
        else
        {
            if (d == 0)
                horizontal_gates[i][j] = -1;
            else
                vertical_gates[i][j] = -1;
            continue;
        }
        gates.push_back({d, i, j, g});
        switches.push_back({si, sj, k});
    }

    best_score = evaluate();
    vector<Gate> best_gates = gates;
    vector<Switch> best_switches = switches;

    auto start_time = chrono::steady_clock::now();
    int iterations = 0;

    while (true)
    {
        if (iterations % 16 == 0)
        {
            auto now = chrono::steady_clock::now();
            double elapsed = chrono::duration_cast<chrono::milliseconds>(now - start_time).count();
            if (elapsed > 2400.0)
                break; // 2.4秒でタイムアウト
        }
        iterations++;

        // 【修正】opの選択肢を0〜6の7つに拡張
        int op = rng() % 7;

        if (op == 0)
        { // 扉の追加
            if (gates.size() >= M)
                continue;
            int d = rng() % 2;
            int i = rng() % N;
            int j = rng() % N;
            int g = rng() % (2 * K);

            if (d == 0 && (i >= N - 1 || j >= N))
                continue;
            if (d == 1 && (i >= N || j >= N - 1))
                continue;
            if (d == 0 && horizontal_gates[i][j] != -1)
                continue;
            if (d == 1 && vertical_gates[i][j] != -1)
                continue;

            if (d == 0)
                horizontal_gates[i][j] = g;
            else
                vertical_gates[i][j] = g;
            gates.push_back({d, i, j, g});

            int score = evaluate();
            if (score > best_score)
            {
                best_score = score;
                best_gates = gates;
                best_switches = switches;
            }
            else
            {
                if (d == 0)
                    horizontal_gates[i][j] = -1;
                else
                    vertical_gates[i][j] = -1;
                gates.pop_back();
            }
        }
        else if (op == 1)
        { // 扉の削除
            if (gates.empty())
                continue;
            int idx = rng() % gates.size();
            Gate removed = gates[idx];

            if (removed.d == 0)
                horizontal_gates[removed.i][removed.j] = -1;
            else
                vertical_gates[removed.i][removed.j] = -1;
            gates.erase(gates.begin() + idx);

            int score = evaluate();
            if (score > best_score)
            {
                best_score = score;
                best_gates = gates;
                best_switches = switches;
            }
            else
            {
                if (removed.d == 0)
                    horizontal_gates[removed.i][removed.j] = removed.g;
                else
                    vertical_gates[removed.i][removed.j] = removed.g;
                gates.insert(gates.begin() + idx, removed);
            }
        }
        else if (op == 2)
        { // 扉の型変更
            if (gates.empty())
                continue;
            int idx = rng() % gates.size();
            int old_g = gates[idx].g;
            int new_g = rng() % (2 * K);
            if (old_g == new_g)
                continue;

            gates[idx].g = new_g;
            if (gates[idx].d == 0)
                horizontal_gates[gates[idx].i][gates[idx].j] = new_g;
            else
                vertical_gates[gates[idx].i][gates[idx].j] = new_g;

            int score = evaluate();
            if (score > best_score)
            {
                best_score = score;
                best_gates = gates;
                best_switches = switches;
            }
            else
            {
                gates[idx].g = old_g;
                if (gates[idx].d == 0)
                    horizontal_gates[gates[idx].i][gates[idx].j] = old_g;
                else
                    vertical_gates[gates[idx].i][gates[idx].j] = old_g;
            }
        }
        else if (op == 3)
        { // スイッチの追加
            if (switches.size() >= MAX_SWITCHES)
                continue;
            int i = rng() % N;
            int j = rng() % N;
            int s = rng() % K;
            if (grid[i][j] == '#' || switch_type[i][j] != -1)
                continue;

            switch_type[i][j] = s;
            switches.push_back({i, j, s});

            int score = evaluate();
            if (score > best_score)
            {
                best_score = score;
                best_gates = gates;
                best_switches = switches;
            }
            else
            {
                switch_type[i][j] = -1;
                switches.pop_back();
            }
        }
        else if (op == 4)
        { // スイッチの削除
            if (switches.empty())
                continue;
            int idx = rng() % switches.size();
            Switch removed = switches[idx];

            switch_type[removed.p][removed.q] = -1;
            switches.erase(switches.begin() + idx);

            int score = evaluate();
            if (score > best_score)
            {
                best_score = score;
                best_gates = gates;
                best_switches = switches;
            }
            else
            {
                switch_type[removed.p][removed.q] = removed.s;
                switches.insert(switches.begin() + idx, removed);
            }
        }
        else if (op == 5)
        { // スイッチの種類変更
            if (switches.empty())
                continue;
            int idx = rng() % switches.size();
            int old_s = switches[idx].s;
            int new_s = rng() % K;
            if (old_s == new_s)
                continue;

            switches[idx].s = new_s;
            switch_type[switches[idx].p][switches[idx].q] = new_s;

            int score = evaluate();
            if (score > best_score)
            {
                best_score = score;
                best_gates = gates;
                best_switches = switches;
            }
            else
            {
                switches[idx].s = old_s;
                switch_type[switches[idx].p][switches[idx].q] = old_s;
            }
        }
        else if (op == 6)
        { // 【新設】ギミックセット（閉じた扉 ＋ 対応する種類のスイッチ）の同時追加
            if (gates.size() >= M || switches.size() >= MAX_SWITCHES)
                continue;

            int k = rng() % K;
            int g = 2 * k + 1; // 初期状態で閉じた扉

            int d = rng() % 2;
            int i = rng() % N;
            int j = rng() % N;
            if (d == 0 && (i >= N - 1 || j >= N))
                continue;
            if (d == 1 && (i >= N || j >= N - 1))
                continue;
            if (d == 0 && horizontal_gates[i][j] != -1)
                continue;
            if (d == 1 && vertical_gates[i][j] != -1)
                continue;

            int si = rng() % N;
            int sj = rng() % N;
            if (grid[si][sj] == '#' || switch_type[si][sj] != -1 || (si == 0 && sj == 0))
                continue;

            // 同時配置
            if (d == 0)
                horizontal_gates[i][j] = g;
            else
                vertical_gates[i][j] = g;
            gates.push_back({d, i, j, g});

            switch_type[si][sj] = k;
            switches.push_back({si, sj, k});

            int score = evaluate();
            if (score > best_score)
            {
                best_score = score;
                best_gates = gates;
                best_switches = switches;
            }
            else
            { // どちらか片方でもダメなら両方ロールバック
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

    cout << best_gates.size() << "\n";
    for (const auto &g : best_gates)
    {
        cout << g.d << " " << g.i << " " << g.j << " " << g.g << "\n";
    }

    cout << best_switches.size() << "\n";
    for (const auto &s : best_switches)
    {
        cout << s.p << " " << s.q << " " << s.s << "\n";
    }

    return 0;
}