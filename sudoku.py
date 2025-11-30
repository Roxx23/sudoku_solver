import tkinter as tk
from tkinter import messagebox

# -------------------- SUDOKU LOGIC -------------------- #

def find_empty_spot(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == -1:
                return r, c
    return None, None

def is_valid(board, guess, row, col):
    # Row
    for c in range(9):
        if c != col and board[row][c] == guess:
            return False

    # Column
    for r in range(9):
        if r != row and board[r][col] == guess:
            return False

    # 3x3 square
    sr = (row // 3) * 3
    sc = (col // 3) * 3
    for r in range(sr, sr+3):
        for c in range(sc, sc+3):
            if (r != row or c != col) and board[r][c] == guess:
                return False

    return True

def solver(board):
    row, col = find_empty_spot(board)
    if row is None:
        return True

    for guess in range(1, 10):
        if is_valid(board, guess, row, col):
            board[row][col] = guess
            if solver(board):
                return True
        board[row][col] = -1

    return False


# -------------------- GUI -------------------- #

class SudokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Solver (Real-Time Validation)")
        self.root.configure(bg="#222831")

        self.cells = [[None for _ in range(9)] for _ in range(9)]
        self.vars = [[None for _ in range(9)] for _ in range(9)]

        # Container
        container = tk.Frame(root, bg="#222831")
        container.pack(padx=20, pady=20)

        # Main grid frame
        self.grid_frame = tk.Frame(container, bg="#222831")
        self.grid_frame.grid(row=0, column=0)

        # Create 3×3 bold subgrids
        self.subgrids = [[None for _ in range(3)] for _ in range(3)]
        for sg_r in range(3):
            for sg_c in range(3):
                frame = tk.Frame(
                    self.grid_frame,
                    bg="#eeeeee",
                    bd=4,
                    relief="solid"
                )
                frame.grid(row=sg_r, column=sg_c, padx=4, pady=4)
                self.subgrids[sg_r][sg_c] = frame

        # Create entry cells with validation bind
        for r in range(9):
            for c in range(9):
                frame = self.subgrids[r // 3][c // 3]

                var = tk.StringVar()
                var.trace("w", lambda *args, row=r, col=c: self.validate_cell(row, col))

                entry = tk.Entry(
                    frame,
                    width=2,
                    font=("Helvetica", 20),
                    justify="center",
                    bd=2,
                    relief="ridge",
                    textvariable=var
                )
                entry.grid(row=r % 3, column=c % 3, padx=4, pady=4)

                self.cells[r][c] = entry
                self.vars[r][c] = var

        solve_button = tk.Button(
            container,
            text="Solve",
            font=("Helvetica", 15, "bold"),
            command=self.solve_and_fill,
            bg="#00adb5",
            fg="white",
            padx=12,
            pady=5
        )
        solve_button.grid(row=1, column=0, pady=20)


    # -------------------- REAL-TIME VALIDATION -------------------- #

    def validate_cell(self, row, col):
        text = self.vars[row][col].get()

        # Empty → white
        if text == "":
            self.cells[row][col].configure(bg="white")
            return

        # Non-digit
        if not text.isdigit():
            self.cells[row][col].configure(bg="#ff4d4d")
            return

        num = int(text)
        if not (1 <= num <= 9):
            self.cells[row][col].configure(bg="#ff4d4d")
            return

        board = self.read_board()

        if is_valid(board, num, row, col):
            self.cells[row][col].configure(bg="#b3ffcc")  # light green
        else:
            self.cells[row][col].configure(bg="#ff4d4d")  # red


    # -------------------- HELPERS -------------------- #

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

    def solve_and_fill(self):
        board = self.read_board()

        if solver(board):
            for r in range(9):
                for c in range(9):
                    self.vars[r][c].set(str(board[r][c]))
                    self.cells[r][c].configure(bg="#b3ffcc")
        else:
            messagebox.showerror("Unsolvable", "This Sudoku cannot be solved!")


# -------------------- RUN APP -------------------- #

if __name__ == "__main__":
    root = tk.Tk()
    SudokuGUI(root)
    root.mainloop()
