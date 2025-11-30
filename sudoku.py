import tkinter as tk
from tkinter import messagebox

ANIMATION_DELAY = 40  # animation speed (ms)


# -------------------- SUDOKU UTILITIES -------------------- #

def find_empty(board):
    """Return the next empty cell in (row, col) format, or None if done."""
    for r in range(9):
        for c in range(9):
            if board[r][c] == -1:
                return r, c
    return None


def is_valid(board, num, row, col):
    """Check if num can be placed at board[row][col]."""
    # Row
    for c in range(9):
        if c != col and board[row][c] == num:
            return False

    # Column
    for r in range(9):
        if r != row and board[r][col] == num:
            return False

    # Block
    br = (row // 3) * 3
    bc = (col // 3) * 3

    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if not (r == row and c == col) and board[r][c] == num:
                return False

    return True


def solve_with_trace(board, steps):
    """
    Perfect backtracking solver.
    Records steps as:
    (row, col, value)
    where value = 1..9 for placement, or -1 for backtracking undo.
    """

    empty = find_empty(board)
    if empty is None:
        return True  # SOLVED

    row, col = empty

    for guess in range(1, 10):
        if is_valid(board, guess, row, col):
            board[row][col] = guess
            steps.append((row, col, guess))  # record placement

            if solve_with_trace(board, steps):
                return True

            # Backtrack
            board[row][col] = -1
            steps.append((row, col, -1))  # record undo

    return False


# -------------------- GUI CLASS -------------------- #

class SudokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Solver – Beautiful GUI + Animation")
        self.root.configure(bg="#222831")

        self.cells = [[None]*9 for _ in range(9)]
        self.vars = [[None]*9 for _ in range(9)]

        self.steps = []          # recorded animation steps
        self.step_index = 0      # current animation index
        self.solution_board = [] # final board

        # Outer container
        container = tk.Frame(root, bg="#222831")
        container.pack(padx=20, pady=20)

        # Sudoku grid frame
        grid_frame = tk.Frame(container, bg="#222831")
        grid_frame.grid(row=0, column=0)

        # Build bold 3×3 blocks
        blocks = [[None]*3 for _ in range(3)]
        for br in range(3):
            for bc in range(3):
                frame = tk.Frame(
                    grid_frame,
                    bg="#eeeeee",
                    bd=4,
                    relief="solid"
                )
                frame.grid(row=br, column=bc, padx=3, pady=3)
                blocks[br][bc] = frame

        # Build cells inside blocks
        for r in range(9):
            for c in range(9):
                parent = blocks[r // 3][c // 3]

                var = tk.StringVar()
                var.trace("w", lambda *args, rr=r, cc=c: self.validate(rr, cc))

                e = tk.Entry(
                    parent,
                    width=2,
                    font=("Helvetica", 20),
                    justify="center",
                    textvariable=var,
                    bd=2,
                    relief="ridge"
                )
                e.grid(row=r % 3, column=c % 3, padx=4, pady=4)

                self.cells[r][c] = e
                self.vars[r][c] = var

        # Buttons
        btn_frame = tk.Frame(container, bg="#222831")
        btn_frame.grid(row=1, column=0, pady=15)

        tk.Button(
            btn_frame,
            text="Animate Solve",
            font=("Helvetica", 14, "bold"),
            bg="#00adb5",
            fg="white",
            padx=10,
            command=self.start_animation
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            btn_frame,
            text="Clear",
            font=("Helvetica", 14),
            bg="#393e46",
            fg="white",
            padx=10,
            command=self.clear
        ).grid(row=0, column=1, padx=5)

    # -------------------- VALIDATION -------------------- #

    def validate(self, row, col):
        txt = self.vars[row][col].get()

        if txt == "":
            self.cells[row][col].configure(bg="white")
            return

        if not txt.isdigit():
            self.cells[row][col].configure(bg="#ff4d4d")
            return

        num = int(txt)
        if not (1 <= num <= 9):
            self.cells[row][col].configure(bg="#ff4d4d")
            return

        board = self.read_board()

        if is_valid(board, num, row, col):
            self.cells[row][col].configure(bg="#b3ffcc")
        else:
            self.cells[row][col].configure(bg="#ff4d4d")

    # -------------------- UTILS -------------------- #

    def read_board(self):
        board = []
        for r in range(9):
            row_vals = []
            for c in range(9):
                val = self.vars[r][c].get()
                if val.isdigit():
                    row_vals.append(int(val))
                else:
                    row_vals.append(-1)
            board.append(row_vals)
        return board

    def clear(self):
        for r in range(9):
            for c in range(9):
                self.vars[r][c].set("")
                self.cells[r][c].configure(bg="white")

        self.steps = []
        self.step_index = 0

    # -------------------- ANIMATION -------------------- #

    def start_animation(self):
        # Reset state
        self.steps = []
        self.step_index = 0

        # Copy board
        board = self.read_board()
        work = [row[:] for row in board]

        # Solve and record steps
        if not solve_with_trace(work, self.steps):
            messagebox.showerror("Unsolvable", "This Sudoku cannot be solved!")
            return

        self.solution_board = work

        # Wipe empty cells to white
        for r in range(9):
            for c in range(9):
                if self.vars[r][c].get().strip() == "":
                    self.cells[r][c].configure(bg="white")

        self.animate_step()

    def animate_step(self):
        if self.step_index >= len(self.steps):
            # Finalize board
            for r in range(9):
                for c in range(9):
                    self.vars[r][c].set(str(self.solution_board[r][c]))
                    self.cells[r][c].configure(bg="#b3ffcc")
            return

        r, c, val = self.steps[self.step_index]

        if val == -1:
            # Backtrack undo
            self.vars[r][c].set("")
            self.cells[r][c].configure(bg="#ff4d4d")
        else:
            # Try a number
            self.vars[r][c].set(str(val))
            self.cells[r][c].configure(bg="#b3ffcc")

        self.step_index += 1
        self.root.after(ANIMATION_DELAY, self.animate_step)


# -------------------- MAIN -------------------- #

if __name__ == "__main__":
    root = tk.Tk()
    SudokuGUI(root)
    root.mainloop()
