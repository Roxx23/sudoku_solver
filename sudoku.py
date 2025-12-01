import tkinter as tk
from tkinter import messagebox

# --------------------- LOGIC HELPERS --------------------- #

def is_valid(board, num, row, col):
    for c in range(9):
        if board[row][c] == num and c != col:
            return False
    for r in range(9):
        if board[r][col] == num and r != row:
            return False

    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if board[r][c] == num and (r, c) != (row, col):
                return False
    return True


def find_empty(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


def backtracking_solve(board):
    pos = find_empty(board)
    if pos is None:
        return True
    r, c = pos
    for num in range(1, 10):
        if is_valid(board, num, r, c):
            board[r][c] = num
            if backtracking_solve(board):
                return True
            board[r][c] = 0
    return False


def compute_all_candidates(board):
    """Return 9x9 array of candidate sets for each empty cell."""
    candidates = [[set() for _ in range(9)] for _ in range(9)]
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                for d in range(1, 10):
                    if is_valid(board, d, r, c):
                        candidates[r][c].add(d)
    return candidates


def find_naked_single(board, candidates):
    """Cell with exactly one candidate."""
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0 and len(candidates[r][c]) == 1:
                val = next(iter(candidates[r][c]))
                msg = f"Naked single: cell ({r+1}, {c+1}) must be {val}."
                return r, c, val, msg
    return None


def find_hidden_single_in_unit(board, candidates, cells, unit_name):
    """Hidden single inside given unit (row/col/box)."""
    count = {d: [] for d in range(1, 10)}
    for (r, c) in cells:
        if board[r][c] == 0:
            for d in candidates[r][c]:
                count[d].append((r, c))

    for d in range(1, 10):
        if len(count[d]) == 1:
            r, c = count[d][0]
            msg = f"Hidden single in {unit_name}: digit {d} can only go in cell ({r+1}, {c+1})."
            return r, c, d, msg
    return None


def find_hidden_single(board, candidates):
    """Search rows, columns and boxes for a hidden single."""
    # Rows
    for r in range(9):
        cells = [(r, c) for c in range(9)]
        res = find_hidden_single_in_unit(board, candidates, cells, f"row {r+1}")
        if res:
            return res

    # Columns
    for c in range(9):
        cells = [(r, c) for r in range(9)]
        res = find_hidden_single_in_unit(board, candidates, cells, f"column {c+1}")
        if res:
            return res

    # Boxes
    for br in range(3):
        for bc in range(3):
            cells = []
            for r in range(br*3, br*3 + 3):
                for c in range(bc*3, bc*3 + 3):
                    cells.append((r, c))
            res = find_hidden_single_in_unit(board, candidates, cells, f"box ({br+1},{bc+1})")
            if res:
                return res

    return None


# ----------------------- GUI CLASS ------------------------ #

class SudokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Responsive Sudoku (Auto-Fit Screen)")
        self.root.configure(bg="#222831")

        # Model data
        self.board = [[0]*9 for _ in range(9)]
        self.candidates = [[set() for _ in range(9)] for _ in range(9)]
        self.selected = None
        self.pencil_mode = False

        # --------- Top Button Bar --------- #
        top = tk.Frame(root, bg="#222831")
        top.pack(pady=5)

        self.pencil_label = tk.Label(top, text="Pencil: OFF", fg="white", bg="#222831", font=("Arial", 12))
        self.pencil_label.grid(row=0, column=0, padx=10)

        tk.Button(top, text="Pencil (P)", bg="#00adb5", fg="white",
                  command=self.toggle_pencil, font=("Arial", 12, "bold")).grid(row=0, column=1, padx=10)

        tk.Button(top, text="Hint", bg="#393e46", fg="white",
                  command=self.hint, font=("Arial", 12)).grid(row=0, column=2, padx=10)

        tk.Button(top, text="Solve", bg="#00adb5", fg="white",
                  command=self.solve, font=("Arial", 12, "bold")).grid(row=0, column=3, padx=10)

        tk.Button(top, text="Clear", bg="#393e46", fg="white",
                  command=self.clear, font=("Arial", 12)).grid(row=0, column=4, padx=10)

        # --------- Responsive Canvas --------- #
        self.canvas = tk.Canvas(root, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Redraw grid when window resizes
        self.canvas.bind("<Configure>", self.redraw)

        # Click handler
        self.canvas.bind("<Button-1>", self.handle_click)

        # Keyboard input
        root.bind("<Key>", self.key_input)

    # -------------------- GRID RENDERING -------------------- #

    def redraw(self, event=None):
        self.canvas.delete("all")

        # Determine square area that fits both width & height
        size = min(self.canvas.winfo_width(), self.canvas.winfo_height())
        self.cell = size / 9
        self.size = size

        # Center grid
        self.x_offset = (self.canvas.winfo_width() - size) / 2
        self.y_offset = (self.canvas.winfo_height() - size) / 2

        # Draw highlight
        self.draw_highlights()

        # Draw cells
        self.draw_numbers()

        # Draw grid lines
        self.draw_grid()

    def draw_grid(self):
        for i in range(10):
            thickness = 3 if i % 3 == 0 else 1
            color = "black"

            # horizontal
            self.canvas.create_line(
                self.x_offset,
                self.y_offset + i*self.cell,
                self.x_offset + self.size,
                self.y_offset + i*self.cell,
                width=thickness,
                fill=color
            )

            # vertical
            self.canvas.create_line(
                self.x_offset + i*self.cell,
                self.y_offset,
                self.x_offset + i*self.cell,
                self.y_offset + self.size,
                width=thickness,
                fill=color
            )

    def draw_highlights(self):
        if not self.selected:
            return
        r, c = self.selected

        for rr in range(9):
            for cc in range(9):
                x1 = self.x_offset + cc*self.cell
                y1 = self.y_offset + rr*self.cell
                x2 = x1 + self.cell
                y2 = y1 + self.cell

                if (rr, cc) == (r, c):
                    color = "#4da3ff"   # blue
                elif rr == r or cc == c or (rr//3 == r//3 and cc//3 == c//3):
                    color = "#fff3b0"   # yellow
                else:
                    continue

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    def draw_numbers(self):
        for r in range(9):
            for c in range(9):
                x = self.x_offset + c*self.cell + self.cell/2
                y = self.y_offset + r*self.cell + self.cell/2

                if self.board[r][c] != 0:
                    # Final number
                    self.canvas.create_text(
                        x, y, text=str(self.board[r][c]),
                        font=("Arial", int(self.cell/2.1)),
                        fill="black"
                    )
                elif self.candidates[r][c]:
                    # Pencil marks
                    text = "·".join(str(d) for d in sorted(self.candidates[r][c]))
                    self.canvas.create_text(
                        x, y, text=text,
                        font=("Arial", int(self.cell/4.5)),
                        fill="#444444"
                    )

    # -------------------- INPUT HANDLERS -------------------- #

    def handle_click(self, event):
        x, y = event.x, event.y

        # Convert click to cell index
        col = int((x - self.x_offset) // self.cell)
        row = int((y - self.y_offset) // self.cell)

        if 0 <= row < 9 and 0 <= col < 9:
            self.selected = (row, col)
            self.redraw()

    def key_input(self, event):
        if not self.selected:
            return

        r, c = self.selected
        ch = event.char

        # Toggle pencil
        if ch in ("p", "P"):
            self.toggle_pencil()
            return

        # Clear
        if ch == "0" or event.keysym in ("BackSpace", "Delete"):
            self.board[r][c] = 0
            self.candidates[r][c].clear()
            self.redraw()
            return

        # Digits
        if ch in "123456789":
            d = int(ch)
            if self.pencil_mode:
                if d in self.candidates[r][c]:
                    self.candidates[r][c].remove(d)
                else:
                    self.candidates[r][c].add(d)
            else:
                self.board[r][c] = d
                self.candidates[r][c].clear()

            self.redraw()

    # -------------------- BUTTON ACTIONS -------------------- #

    def toggle_pencil(self):
        self.pencil_mode = not self.pencil_mode
        self.pencil_label.config(text=f"Pencil: {'ON' if self.pencil_mode else 'OFF'}")

    def clear(self):
        self.board = [[0]*9 for _ in range(9)]
        self.candidates = [[set() for _ in range(9)] for _ in range(9)]
        self.selected = None
        self.redraw()

    def solve(self):
        temp = [row[:] for row in self.board]
        if backtracking_solve(temp):
            self.board = temp
            self.candidates = [[set() for _ in range(9)] for _ in range(9)]
            self.redraw()
            messagebox.showinfo("Solved", "Sudoku solved successfully!")
        else:
            messagebox.showerror("Error", "Cannot solve this Sudoku.")

    def hint(self):
        # Work on a copy of the current board (ignores current manual candidates)
        temp = [row[:] for row in self.board]
        candidates = compute_all_candidates(temp)

        # First try naked single
        res = find_naked_single(temp, candidates)
        if not res:
            # Then try hidden single
            res = find_hidden_single(temp, candidates)

        if not res:
            messagebox.showinfo(
                "Hint",
                "No simple logical move found.\n(Next step would need more advanced strategies.)"
            )
            return

        r, c, val, msg = res
        # Apply to real board
        self.board[r][c] = val
        self.candidates[r][c].clear()
        self.selected = (r, c)
        self.redraw()
        messagebox.showinfo("Hint", msg)


# -------------------- RUN APP -------------------- #

if __name__ == "__main__":
    root = tk.Tk()
    SudokuGUI(root)
    root.mainloop()
