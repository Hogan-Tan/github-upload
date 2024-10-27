import random
import math


# 定义井字游戏的状态类
class GameState:
    def __init__(self, board=None, mark='X'):
        # 初始化游戏状态，board为None时创建新游戏，否则复制已有游戏状态
        if board is None:
            self.board = [[' ' for _ in range(3)] for _ in range(3)]
            self.mark = mark
            self.current_player = mark
        else:
            self.board = [row[:] for row in board]
            self.mark = mark
            self.current_player = ('X' if mark == 'O' else 'O')

            # 检查游戏是否结束

    def is_end(self):
        # 检查是否有玩家获胜
        # 检查所有行
        for row in self.board:
            if row[0] == row[1] == row[2] != ' ':
                return True, row[0]

        # 检查所有列
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != ' ':
                return True, self.board[0][col]

        # 检查对角线
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != ' ':
            return True, self.board[1][1]

        if self.board[0][2] == self.board[1][1] == self.board[2][0] != ' ':
            return True, self.board[1][1]

        # 检查是否平局（棋盘已满）
        if all([item != ' ' for sublist in self.board for item in sublist]):
            return True, 'Draw'

        return False, None

    # 执行一个动作（在棋盘上放置棋子）
    def execute_move(self, move):
        x, y = move
        self.board[x][y] = self.current_player
        self.current_player = ('X' if self.current_player == 'O' else 'O')

        # 获取所有可能的合法动作

    def get_legal_moves(self):
        legal_moves = []
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == ' ':
                    legal_moves.append((i, j))
        return legal_moves

    # 打印当前棋盘状态
    def __str__(self):
        result = ""
        for row in self.board:
            result += " | ".join(row) + "\n" + "-" * 10 + "\n"
        return result[:-11]


# 定义蒙特卡洛树搜索节点类
class MCTSNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = {}  # 存储子节点的字典，键为动作，值为MCTSNode对象
        self.visits = 0  # 该节点被访问的次数
        self.value = 0.0  # 该节点的累积价值（由模拟结果得出）

    def is_fully_expanded(self):
        # 直接检查子节点的数量是否等于当前状态下所有可能的合法动作的数量
        return len(self.children) == len(self.state.get_legal_moves())
        # 这种方式假设了每次展开节点时，都会为当前状态下的所有合法动作创建子节点，不考虑当前是谁在行动（因为MCTS会交替选择动作）。这是井字游戏等回合制游戏中常见的做法。

    # 选择子节点，使用UCT公式
    def select_child(self, exploration_weight=math.sqrt(2)):  # 默认的探索权重为sqrt(2)
        if not self.children:
            return None
        selected_child = max(self.children.values(),
                             key=lambda c: (c.value / c.visits) + exploration_weight * math.sqrt(
                                 (2 * math.log(self.visits) / c.visits)))
        return selected_child

    # 展开节点（生成子节点）
    def expand(self):
        legal_moves = self.state.get_legal_moves()
        if not legal_moves:
            return None
            # 过滤出未被扩展的合法移动
        unexpanded_moves = [move for move in legal_moves if move not in self.children]
        if not unexpanded_moves:
            return None  # 所有合法移动都已被扩展
        # 随机选择一个未被扩展的移动
        move = random.choice(unexpanded_moves)
        next_state = GameState(self.state.board, self.state.mark)
        next_state.execute_move(move)
        child_node = MCTSNode(next_state, self)
        self.children[move] = child_node
        return child_node

    # 模拟游戏直到结束，并返回结果
    def simulate(self):
        visited_paths = set()  # 记录已访问的路径
        path = []  # 当前路径
        state = GameState(self.state.board, self.state.mark)
        while True:
            end, winner = state.is_end()
            if end:
                if (winner != self.state.mark) and (winner != 'Draw') and (winner is not None):
                    return 1.0
                elif winner == 'Draw':
                    return 0.5
                else:
                    return 0.0
            re_count = 0
            re_count_quit = True
            while True:
                legal_moves = state.get_legal_moves()
                if not legal_moves:
                    return 100.0  # 没有合法移动，返回默认值
                move = random.choice(legal_moves)  # 使用 random.choice 返回一个单一的移动
                path.append(move)
                path_tuple = tuple(path)
                if path_tuple not in visited_paths:
                    visited_paths.add(path_tuple)
                    break
                path.pop()  # 移除最后一个移动，重新选择
                re_count += 1
                if re_count > 100:  # 如果连续100次都遇到重复路径，则退出
                    re_count_quit = False
                    break
            if re_count_quit:
                if MCTSNode.loss_path(self) == 'loss':
                    return 'loss'
                else:
                    state.execute_move(move)
            else:
                return 100.0

    # def loss_path(self, move):
    #     state = GameState(self.state.board, self.state.mark)
    #     state.execute_move(move)
    #     result = 0
    #     for legal_move in state.get_legal_moves():
    #         result = MCTSNode.loss_path_result(self, legal_move)
    #         result += result
    #     if result != 0:
    #         return 'loss'

    def loss_path_result(self, move):
        state = GameState(self.state.board, self.state.mark)
        state.current_player = ('X' if state.current_player == 'O' else 'O')
        state.execute_move(move)
        end, winner = state.is_end()
        if end:
            if (winner == self.state.mark) and (winner != 'Draw') and (winner is not None):
                return 1
        return 0

    def loss_path(self):
        state = GameState(self.state.board, self.state.mark)
        result_add = 0
        for legal_move in state.get_legal_moves():
            result = MCTSNode.loss_path_result(self, legal_move)
            result_add += result
        if result_add != 0:
            return 'loss'


# 定义蒙特卡洛树搜索类
class MCTS:
    def __init__(self, initial_state, iterations=1000):
        self.root = MCTSNode(initial_state)
        self.iterations = iterations

        # 执行蒙特卡洛树搜索

    def search(self):
        for _ in range(self.iterations):
            node = self.root
            # 选择阶段
            while node.is_fully_expanded() and (node.select_child() is not None):
                node = node.select_child()
            # 展开阶段
            if node.is_fully_expanded() is False:
                node = node.expand()
            # 模拟阶段
            result_value = 0
            i = 0
            for i in range(self.iterations):
                result = node.simulate()
                if result != 100.0 and result != 'loss':
                    result_value += result
                elif result == 'loss':
                    node.value = -100
                else:
                    break
            result_value = result_value/i+1
            # 回溯阶段
            while node is not None:
                node.visits += 1
                node.value += result_value
                node = node.parent

    # 获取最佳动作
    def get_best_move(self):
        best_move = max(self.root.children.values(), key=lambda c: (c.value / c.visits))
        return list(self.root.children.keys())[list(self.root.children.values()).index(best_move)]

    # 示例使用


if __name__ == "__main__":
    initial_state = GameState(board=[[' ', ' ', ' '], [' ', ' ', ' '], [' ', ' ', ' ']], mark='O')
    mcts = MCTS(initial_state, iterations=100)
    mcts.search()
    best_move = mcts.get_best_move()
    print("Best move:", best_move)
    print("Initial board:")
    print(initial_state)
    initial_state.execute_move(best_move)
    print("Board after best move:")
    print(initial_state)
    win_or_lose, result_winner = GameState.is_end(initial_state)
    if win_or_lose:
        if result_winner == 'draw':
            print("平局")
        else:
            print("胜利者:", result_winner)
