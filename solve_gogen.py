import click
import z3
from more_itertools import flatten

class NoSolution(Exception):
    pass

class Gogen(object):
    def __init__(self, board, remaining_letters, words):
        self.board = board
        self.remaining_letters = remaining_letters
        self.words = words

    @classmethod
    def load_from_file(cls, f):
        lines = list(map(str.strip, f.readlines()))
        board = [[c for c in line] for line in lines[:5]]
        remaining_letters = [c for c in lines[6]]
        words = [[c for c in line] for line in lines[8:]]
        return cls(board, remaining_letters, words)

    def show(self):
        print("Board:\n" + "\n".join("\t" + "".join(c for c in line) for line in self.board))
        print("Remaining letters: {}".format("".join(self.remaining_letters)))
        print("Words:\n" + "\n".join("\t" + "".join(c for c in line) for line in self.words))

    def solve(self):
        s = z3.Solver()

        # Create the grid of cells
        cells = {(i,j): z3.Int(str((i,j))) for i in range(5) for j in range(5)}

        # Add the letters we know in the grid
        # Or a disjonction on the available letters for the cells we don't know yet
        for i, word in enumerate(self.board):
            for j,char in enumerate(word):
                if char != '?':
                    s.add(cells[(i,j)] == ord(char))
                else:
                    disj = [cells[(i,j)] == ord(available_letter) for available_letter in self.remaining_letters]
                    s.add(z3.Or(*disj))

        # Make sure that all available letters are used
        for available_letter in self.remaining_letters:
            disj = [cells[(i,j)] == ord(available_letter) for i in range(5) for j in range(5) if self.board[i][j] == '?']
            s.add(z3.Or(*disj))

        # Add the constraints based on the words
        # I.e for all pairs of consecutive letters in words
        # There are two adjacent cells on the board with that pair
        # (as each letter appears only once, this is a sufficient condition)

        consecutive_letters = set(flatten(map(lambda w: list(zip(w[:-1],w[1:])), self.words)))

        for a, b in consecutive_letters:
            big_or = []
            for i in range(5):
                for j in range(5):
                    # small optimisation to help the solver
                    if self.board[i][j] == '?' or self.board[i][j] == a:
                        adjacent_cells_condition = [
                            cells[(i+k, j+l)] == ord(b)
                            for k in [-1,0,1] for l in [-1,0,1]
                            if
                                (0 <= (i+k) <= 4)
                                and (0 <= (j+l) <= 4)
                                and (not ((k == 0) and (l == 0)))
                                # small optimisation to help the solver
                                and (self.board[i+k][j+l] == '?' or self.board[i+k][j+l] == b)
                        ]
                        big_or.append(z3.And(cells[(i,j)] == ord(a), z3.Or(*adjacent_cells_condition)))
            s.add(z3.Or(*big_or))

        res = s.check()

        if res != z3.sat:
            raise NoSolution

        m = s.model()

        return Gogen(
            [[chr(m[cells[(i,j)]].as_long()) for j in range(5)] for i in range(5)],
            [],
            []
        )

@click.command()
@click.argument('filename')
def load_and_solve_gogen(filename):
    with open(filename, "r") as f:
        ggn = Gogen.load_from_file(f)

    ggn.show()

    print("Solving the Gogen...")
    solved_ggn = ggn.solve()
    print("Gogen solved.")

    solved_ggn.show()

if __name__ == '__main__':
    load_and_solve_gogen()

