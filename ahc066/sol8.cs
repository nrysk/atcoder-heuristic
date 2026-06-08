// ルール
// 座標は全て y * width + x で表す

using System;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Text;




int[] nmt = Console.ReadLine()!.Split().Select(int.Parse).ToArray();
int n = nmt[0];
int m = nmt[1];
int t = nmt[2];
var v = new List<string>();
for (int i = 0; i < n; i++) v.Add(Console.ReadLine()!);
var h = new List<string>();
for (int i = 0; i < n - 1; i++) h.Add(Console.ReadLine()!);
int[] ballPositions = new int[m];
int[] basketPositions = new int[m];
Console.Error.WriteLine($"n: {n}, m: {m}, t: {t}");
for (int i = 0; i < m; i++)
{
    int[] line = Console.ReadLine()!.Split().Select(int.Parse).ToArray();
    ballPositions[i] = line[0] * n + line[1];
    basketPositions[i] = line[2] * n + line[3];
}

var solver = new Solver(n, m, t, v, h, ballPositions, basketPositions);
var bestOperations = solver.Solve();
Console.Error.WriteLine(bestOperations.Count);
Console.WriteLine(string.Join("", bestOperations));


public static class Dir
{
    public const int Up = 0;
    public const int Left = 1;
    public const int Down = 2;
    public const int Right = 3;
}

public class FastArray2D<T>
{
    private readonly T[] _data;
    private readonly int _size1;

    public FastArray2D(int size0, int size1)
    {
        _data = new T[size0 * size1];
        _size1 = size1;
    }

    public T this[int i0, int i1]
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        get => _data[i0 * _size1 + i1];
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        set => _data[i0 * _size1 + i1] = value;
    }

    public T[] RawData => _data;
}

public class LazyDistanceTable
{
    private static readonly int[] Dx = { 0, -1, 0, 1 };
    private static readonly int[] Dy = { -1, 0, 1, 0 };

    private readonly int _n;
    private readonly int _m;
    private readonly int _t;
    private readonly int[] BallPositions;
    private readonly int[] BasketPositions;
    public string Macro { get; private set; }

    private readonly FastArray2D<int> _wallDist;
    private readonly int[] _macroNextState;
    private readonly FastArray2D<int> _dist;
    private readonly FastArray2D<int> _turn;
    private readonly FastArray2D<int> _prevState;
    private readonly FastArray2D<char> _prevOp;

    private int _currentVersion;
    private readonly int[] _versionTable;
    private int _currentVisitedToken;
    private readonly int[] _visitedTokenTable;

    public LazyDistanceTable(
        int n,
        int m,
        int t,
        List<string> v,
        List<string> h,
        int[] ballPositions,
        int[] basketPositions,
        string macro
    )
    {
        _n = n; _m = m; _t = t;
        BallPositions = ballPositions;
        BasketPositions = basketPositions;
        Macro = macro;

        int stateSize = _n * _n * 4;


        _wallDist = new FastArray2D<int>(_n * _n, 4);
        _macroNextState = new int[_n * _n * 4];

        PrecalcWallDist(v, h);
        PrecalcMacroNextState(macro);

        _dist = new FastArray2D<int>(stateSize, stateSize);
        _turn = new FastArray2D<int>(stateSize, stateSize);
        _prevState = new FastArray2D<int>(stateSize, stateSize);
        _prevOp = new FastArray2D<char>(stateSize, stateSize);

        _versionTable = new int[stateSize];
        _visitedTokenTable = new int[stateSize];
        Array.Fill(_versionTable, -1);
        Array.Fill(_visitedTokenTable, -1);
        _currentVersion = 0;
        _currentVisitedToken = 0;
    }

    public void ResetMacro(string macro)
    {
        Macro = macro;
        _currentVersion++;
        PrecalcMacroNextState(macro);
    }

    public (int y, int x) Forward(int y, int x, int dir, int times)
    {
        int fromPos = y * _n + x;
        int dist = Math.Min(times, _wallDist[fromPos, dir]);
        return (y + Dy[dir] * dist, x + Dx[dir] * dist);
    }

    public (int y, int x, int dir) PlayMacro(int y, int x, int dir)
    {
        foreach (char op in Macro)
        {
            switch (op)
            {
                case 'F': (y, x) = Forward(y, x, dir, 1); break;
                case 'L': dir = (dir + 1) % 4; break;
                case 'R': dir = (dir + 3) % 4; break;
            }
        }
        return (y, x, dir);
    }

    public (int y, int x, int dir) PlayOperations(int y, int x, int dir, string operations)
    {
        foreach (char op in operations)
        {
            switch (op)
            {
                case 'F': (y, x) = Forward(y, x, dir, 1); break;
                case 'L': dir = (dir + 1) % 4; break;
                case 'R': dir = (dir + 3) % 4; break;
                case 'P': (y, x, dir) = PlayMacro(y, x, dir); break;
            }
        }
        return (y, x, dir);
    }

    public (int dist, int turn, int toPos, int toDir) Get(int fromPos, int fromDir, int toPos)
    {
        int fromState = EncodeState(fromPos, fromDir);
        if (_versionTable[fromState] != _currentVersion)
        {
            ComputeBfs(fromPos, fromDir);
            _versionTable[fromState] = _currentVersion;
        }

        // 全ての toDir で最小の dist を探す
        var bestDist = int.MaxValue;
        var bestDir = -1;
        var bestTurn = -1;

        for (int toDir = 0; toDir < 4; toDir++)
        {
            int toState = EncodeState(toPos, toDir);
            if (_dist[fromState, toState] < bestDist)
            {
                bestDist = _dist[fromState, toState];
                bestDir = toDir;
                bestTurn = _turn[fromState, toState];
            }
        }

        return (bestDist, bestTurn, toPos, bestDir);
    }

    public (List<char> path, int toPos, int toDir) GetPath(int fromPos, int fromDir, int toPos)
    {
        var (_, _, _, toDir) = Get(fromPos, fromDir, toPos);

        int fromState = EncodeState(fromPos, fromDir);
        int currentState = EncodeState(toPos, toDir);
        var path = new List<char>();

        while (currentState != fromState)
        {
            char op = _prevOp[fromState, currentState];
            path.Add(op);
            currentState = _prevState[fromState, currentState];
        }
        path.Reverse();
        return (path, toPos, toDir);
    }

    private void PrecalcWallDist(
        List<string> v,
        List<string> h
    )
    {

        for (int y = 0; y < _n; y++)
        {
            for (int x = 0; x < _n; x++)
            {
                int pos = y * _n + x;
                // 上方向
                if (y == 0 || h[y - 1][x] == '1') _wallDist[pos, Dir.Up] = 0;
                else _wallDist[pos, Dir.Up] = _wallDist[(y - 1) * _n + x, Dir.Up] + 1;
                // 左方向
                if (x == 0 || v[y][x - 1] == '1') _wallDist[pos, Dir.Left] = 0;
                else _wallDist[pos, Dir.Left] = _wallDist[y * _n + x - 1, Dir.Left] + 1;
            }
        }
        for (int y = _n - 1; y >= 0; y--)
        {
            for (int x = _n - 1; x >= 0; x--)
            {
                int pos = y * _n + x;
                // 下方向
                if (y == _n - 1 || h[y][x] == '1') _wallDist[pos, Dir.Down] = 0;
                else _wallDist[pos, Dir.Down] = _wallDist[(y + 1) * _n + x, Dir.Down] + 1;
                // 右方向
                if (x == _n - 1 || v[y][x] == '1') _wallDist[pos, Dir.Right] = 0;
                else _wallDist[pos, Dir.Right] = _wallDist[y * _n + x + 1, Dir.Right] + 1;
            }
        }
    }

    private void PrecalcMacroNextState(string macro)
    {
        for (int y = 0; y < _n; y++)
        {
            for (int x = 0; x < _n; x++)
            {
                for (int dir = 0; dir < 4; dir++)
                {
                    var (ny, nx, ndir) = PlayMacro(y, x, dir);
                    _macroNextState[EncodeState(y * _n + x, dir)] = EncodeState(ny * _n + nx, ndir);
                }
            }
        }
    }

    private void ComputeBfs(int fromPos, int fromDir)
    {
        int macroLength = Macro.Length;
        int fromState = EncodeState(fromPos, fromDir);
        _dist[fromState, fromState] = 0;
        _turn[fromState, fromState] = 0;
        _currentVisitedToken++;
        _visitedTokenTable[fromState] = _currentVisitedToken;

        var queue = new Queue<int>();
        queue.Enqueue(fromState);

        var nexts = new (char op, int state, int turn)[4];

        while (queue.Count > 0)
        {
            int currentState = queue.Dequeue();
            int currentPos = currentState / 4;
            int currentDir = currentState % 4;
            int y = currentPos / _n;
            int x = currentPos % _n;

            // 前進
            var (ny, nx) = Forward(y, x, currentDir, 1);
            nexts[0] = ('F', EncodeState(ny * _n + nx, currentDir), 1);

            // 左折
            nexts[1] = ('L', EncodeState(currentPos, (currentDir + 1) % 4), 1);

            // 右折
            nexts[2] = ('R', EncodeState(currentPos, (currentDir + 3) % 4), 1);

            // マクロ
            nexts[3] = ('P', _macroNextState[currentState], macroLength);

            foreach (var (op, nextState, turn) in nexts)
            {
                if (_visitedTokenTable[nextState] == _currentVisitedToken) continue;
                _visitedTokenTable[nextState] = _currentVisitedToken;

                _dist[fromState, nextState] = _dist[fromState, currentState] + 1;
                _turn[fromState, nextState] = _turn[fromState, currentState] + turn;
                _prevState[fromState, nextState] = currentState;
                _prevOp[fromState, nextState] = op;
                queue.Enqueue(nextState);
            }
        }
    }

    private int EncodeState(int pos, int dir) => pos * 4 + dir;
}

public abstract class Simulator
{
    protected static readonly Random Rand = new Random(0);

    protected readonly int N;
    protected readonly int M;
    protected readonly int T;
    protected readonly int[] BallPositions;
    protected readonly int[] BasketPositions;
    protected readonly LazyDistanceTable DistanceTable;

    protected Simulator(
        int n,
        int m,
        int t,
        int[] ballPositions,
        int[] basketPositions,
        LazyDistanceTable distanceTable
    )
    {
        N = n; M = m; T = t;
        BallPositions = ballPositions;
        BasketPositions = basketPositions;
        DistanceTable = distanceTable;
    }

    protected (List<int> route, int score) InitializeRouteByGreedy(
        string firstOperations, string macro
    )
    {
        var (currentY, currentX, currentDir) = DistanceTable.PlayOperations(0, 0, Dir.Right, firstOperations);
        (currentY, currentX, currentDir) = DistanceTable.PlayMacro(currentY, currentX, currentDir);
        int currentPos = currentY * N + currentX;
        int currentScore = firstOperations.Length + macro.Length + 2;
        int currentTurn = currentScore;

        var route = new List<int>();
        var remainingBalls = new HashSet<int>(Enumerable.Range(0, M));

        int dist, turn;
        while (remainingBalls.Count > 0)
        {
            int bestBall = -1;
            int bestDist = int.MaxValue;

            foreach (int ball in remainingBalls)
            {
                (dist, _, _, _) = DistanceTable.Get(currentPos, currentDir, ball);
                if (dist < bestDist)
                {
                    bestDist = dist;
                    bestBall = ball;
                }
            }

            // ボールを取る
            (dist, turn, currentPos, currentDir) = DistanceTable.Get(currentPos, currentDir, BallPositions[bestBall]);
            currentScore += dist + 1;
            currentTurn += turn + 1;

            // 対応するカゴに入れに行く
            (dist, turn, currentPos, currentDir) = DistanceTable.Get(currentPos, currentDir, BasketPositions[bestBall]);
            currentScore += dist + 1;
            currentTurn += turn + 1;

            if (currentScore > T)
            {
                currentScore = remainingBalls.Count * T;
                break;
            }

            route.Add(bestBall);
            remainingBalls.Remove(bestBall);
        }

        // ボールが入り切らなければ、ルートに足しておく
        foreach (int ball in remainingBalls)
        {
            route.Add(ball);
        }

        return (route, currentScore);
    }

    protected int EvaluateRoute(string firstOperations, string macro, List<int> route)
    {
        var (currentY, currentX, currentDir) = DistanceTable.PlayOperations(0, 0, Dir.Right, firstOperations);
        (currentY, currentX, currentDir) = DistanceTable.PlayMacro(currentY, currentX, currentDir);
        int currentPos = currentY * N + currentX;
        int currentScore = firstOperations.Length + macro.Length + 2;
        int currentTurn = currentScore;

        for (int i = 0; i < route.Count; i++)
        {
            int ball = route[i];

            // ボールを取る
            int dist, turn;
            (dist, turn, currentPos, currentDir) = DistanceTable.Get(currentPos, currentDir, BallPositions[ball]);
            currentScore += dist + 1;
            currentTurn += turn + 1;

            // 対応するカゴに入れに行く
            (dist, turn, currentPos, currentDir) = DistanceTable.Get(currentPos, currentDir, BasketPositions[ball]);
            currentScore += dist + 1;
            currentTurn += turn + 1;

            if (currentScore > T)
            {
                return (M - i) * T;
            }
        }

        return currentScore;
    }
}

public class ClimbSimulator : Simulator
{
    private const int Steps = 0;

    public ClimbSimulator(int n, int m, int t, int[] ballPositions, int[] basketPositions, LazyDistanceTable distanceTable)
        : base(n, m, t, ballPositions, basketPositions, distanceTable)
    { }

    public int Evaluate(string firstOperations, string macro)
    {
        if (DistanceTable.Macro != macro) DistanceTable.ResetMacro(macro);

        var (bestRoute, bestScore) = InitializeRouteByGreedy(firstOperations, macro);

        for (int step = 0; step < Steps; step++)
        {
            int i = Rand.Next(M);
            int j = (i + Rand.Next(1, M)) % M;

            var newRoute = new List<int>(bestRoute);
            double mode = Rand.NextDouble();

            if (mode < 0.2) // swap
            {
                (newRoute[i], newRoute[j]) = (newRoute[j], newRoute[i]);
            }
            else if (mode < 0.6) // reverse
            {
                if (i > j) (i, j) = (j, i);
                newRoute.Reverse(i, j - i + 1);
            }
            else // insert
            {
                int ball = newRoute[i];
                newRoute.RemoveAt(i);
                newRoute.Insert(j, ball);
            }

            int newScore = EvaluateRoute(firstOperations, macro, newRoute);
            if (newScore < bestScore)
            {
                bestScore = newScore;
                bestRoute = newRoute;
            }
        }

        return bestScore;
    }
}

public class AnnealSimulator : Simulator
{
    private const int Steps = 10000;
    private const double StartTemperature = 1;
    private const double EndTemperature = 0.1;

    public AnnealSimulator(int n, int m, int t, int[] ballPositions, int[] basketPositions, LazyDistanceTable distanceTable)
        : base(n, m, t, ballPositions, basketPositions, distanceTable)
    { }

    public List<char> CalcBestOperations(string firstOperations, string macro)
    {
        if (DistanceTable.Macro != macro) DistanceTable.ResetMacro(macro);

        var (currentRoute, currentScore) = InitializeRouteByGreedy(firstOperations, macro);
        var bestRoute = new List<int>(currentRoute);
        int bestScore = currentScore;

        for (int step = 0; step < Steps; step++)
        {
            double fraction = (double)step / Steps;
            double temperature = StartTemperature + fraction * (EndTemperature - StartTemperature);

            int i = Rand.Next(M);
            int j = (i + Rand.Next(1, M)) % M;

            var newRoute = new List<int>(currentRoute);
            double mode = Rand.NextDouble();

            if (mode < 0.2) // swap
            {
                (newRoute[i], newRoute[j]) = (newRoute[j], newRoute[i]);
            }
            else if (mode < 0.6) // reverse
            {
                if (i > j) (i, j) = (j, i);
                newRoute.Reverse(i, j - i + 1);
            }
            else // insert
            {
                int ball = newRoute[i];
                newRoute.RemoveAt(i);
                newRoute.Insert(j, ball);
            }

            int newScore = EvaluateRoute(firstOperations, macro, newRoute);

            int delta = newScore - currentScore;

            if (delta < 0 || Math.Exp(-delta / temperature) > Rand.NextDouble())
            {
                currentScore = newScore;
                currentRoute = newRoute;

                if (currentScore < bestScore)
                {
                    Console.Error.WriteLine($"New best score: {currentScore} at step {step} (firstOperations: {firstOperations}, macro: {macro})");
                    bestScore = currentScore;
                    bestRoute = newRoute;
                }
            }
        }
        return BuildOperations(firstOperations, macro, bestRoute);
    }

    private List<char> BuildOperations(string firstOperations, string macro, List<int> route)
    {
        var operations = new List<char>();
        operations.AddRange(firstOperations);
        operations.Add('M');
        operations.AddRange(macro);
        operations.Add('M');
        var (currentY, currentX, currentDir) = DistanceTable.PlayOperations(0, 0, Dir.Right, firstOperations);
        (currentY, currentX, currentDir) = DistanceTable.PlayMacro(currentY, currentX, currentDir);
        int currentPos = currentY * N + currentX;

        List<char> path;
        for (int i = 0; i < route.Count; i++)
        {
            int ball = route[i];

            // ボールを取る
            (path, currentPos, currentDir) = DistanceTable.GetPath(currentPos, currentDir, BallPositions[ball]);
            operations.AddRange(path);
            operations.Add('S'); // 取る

            // 対応するカゴに入れに行く
            (path, currentPos, currentDir) = DistanceTable.GetPath(currentPos, currentDir, BasketPositions[ball]);
            operations.AddRange(path);
            operations.Add('S'); // 入れる
        }

        return operations;
    }
}

public class Solver
{
    Random Rand = new Random(0);

    private static readonly string[] FirstOperationsCandidates = { "", "F", "L", "R", "RR" };

    private readonly int _n, _m, _t, _numWalls;
    private readonly int[] _ballPositions, _basketPositions;
    private readonly LazyDistanceTable _distanceTable;

    public Solver(int n, int m, int t, List<string> v, List<string> h, int[] ballPositions, int[] basketPositions)
    {
        _n = n; _m = m; _t = t;
        _ballPositions = ballPositions;
        _basketPositions = basketPositions;
        _distanceTable = new LazyDistanceTable(n, m, t, v, h, ballPositions, basketPositions, "");
        foreach (var row in v) foreach (char c in row) if (c == '1') _numWalls++;
        foreach (var row in h) foreach (char c in row) if (c == '1') _numWalls++;
    }

    public List<char> Solve()
    {
        int timeLimitMs = 1600;
        var sw = Stopwatch.StartNew();

        var climbSimulator = new ClimbSimulator(_n, _m, _t, _ballPositions, _basketPositions, _distanceTable);

        string bestMacro = "";
        string bestFirstOperations = "";
        int bestScore = int.MaxValue;

        int itr = 0;
        while (true)
        {
            if (itr % 32 == 0 && sw.ElapsedMilliseconds > timeLimitMs) break;
            itr++;

            string macro = GenerateRandomMacro();
            foreach (string firstOperations in FirstOperationsCandidates)
            {
                int score = climbSimulator.Evaluate(firstOperations, macro);
                if (score < bestScore)
                {
                    Console.Error.WriteLine($"New best score: {score} (firstOperations: {firstOperations}, macro: {macro})");
                    bestScore = score;
                    bestMacro = macro;
                    bestFirstOperations = firstOperations;
                }
            }
        }

        Console.Error.WriteLine($"Total iterations: {itr} within {sw.ElapsedMilliseconds} ms");

        var annealSimulator = new AnnealSimulator(_n, _m, _t, _ballPositions, _basketPositions, _distanceTable);
        var bestOperations = annealSimulator.CalcBestOperations(bestFirstOperations, bestMacro);

        return bestOperations;
    }

    private string GenerateRandomMacro()
    {
        int macroLength = Rand.Next(3, 23); // 3〜22

        // C#固有：文字列を動的に切り貼り・組み立てる場合は、`StringBuilder` を使うのが最速の定石です。
        var sb = new StringBuilder();
        char[] choice = { 'F', 'L', 'R' };

        sb.Append(choice[Rand.Next(3)]);
        for (int k = 0; k < macroLength - 3; k++) sb.Append('F');
        sb.Append(choice[Rand.Next(3)]);

        int i = Rand.Next(1, sb.Length);
        sb.Insert(i, choice[Rand.Next(3)]);

        if (_numWalls > 30)
        {
            int j = Rand.Next(1, sb.Length);
            sb.Insert(j, choice[Rand.Next(3)]);
        }

        if (Rand.NextDouble() < 0.5)
        {
            sb.Append(sb[sb.Length - 1]);
        }

        return sb.ToString();
    }
}