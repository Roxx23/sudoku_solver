import tkinter as tk
from tkinter import messagebox

# ============================================================
#                 BOARD LOGIC HELPERS
# ============================================================

def is_valid(board, num, row, col):
    """Check if num can be placed at (row, col)."""
    for c in range(9):
        if board[row][c] == num and c != col:
            return False
    for r in range(9):
        if board[r][col] == num and r != row:
            return False

    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br+3):
        for c in range(bc, bc+3):
            if board[r][c] == num and (r, c) != (row, col):
                return False
    return True


def find_empty(board):
    """Find first empty cell."""
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


# ============================================================
#          ANIMATED BACKTRACK SOLVER (GENERATOR)
# ============================================================

def solve_generator(board):
    empty = find_empty(board)
    if not empty:
        yield ("final", None, None, None)
        return

    r, c = empty
    for guess in range(1, 10):
        if is_valid(board, guess, r, c):
            board[r][c] = guess
            yield ("place", r, c, guess)

            for step in solve_generator(board):
                yield step
                if step[0] == "final":
                    return

        # backtrack
        board[r][c] = 0
        yield ("backtrack", r, c, guess)

    yield ("deadend", r, c, None)


# ============================================================
#                     CANDIDATE LOGIC
# ============================================================

def compute_all_candidates(board):
    cand = [[set() for _ in range(9)] for _ in range(9)]
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                for d in range(1, 10):
                    if is_valid(board, d, r, c):
                        cand[r][c].add(d)
    return cand


def find_naked_single(board, candidates):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0 and len(candidates[r][c]) == 1:
                val = next(iter(candidates[r][c]))
                msg = f"Naked single → Cell ({r+1},{c+1}) = {val}"
                return r, c, val, msg
    return None


def find_hidden_single_in_unit(board, candidates, cells, name):
    count = {d: [] for d in range(1, 10)}

    for (r, c) in cells:
        if board[r][c] == 0:
            for d in candidates[r][c]:
                count[d].append((r, c))

    for d in range(1, 10):
        if len(count[d]) == 1:
            r, c = count[d][0]
            msg = f"Hidden single in {name} → digit {d} at ({r+1},{c+1})"
            return r, c, d, msg

    return None


def find_hidden_single(board, candidates):
    for r in range(9):
        cells = [(r, c) for c in range(9)]
        res = find_hidden_single_in_unit(board, candidates, cells, f"row {r+1}")
        if res:
            return res

    for c in range(9):
        cells = [(r, c) for r in range(9)]
        res = find_hidden_single_in_unit(board, candidates, cells, f"column {c+1}")
        if res:
            return res

    for br in range(3):
        for bc in range(3):
            cells = [(r, c) for r in range(br*3, br*3+3)
                             for c in range(bc*3, bc*3+3)]
            res = find_hidden_single_in_unit(board, candidates, cells, f"box ({br+1},{bc+1})")
            if res:
                return res

    return None


# ============================================================
#                     GUI CLASS
# ============================================================

class SudokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku — Pencil, Hint, Animation")
        self.root.configure(bg="#222831")

        # Board model
        self.board = [[0]*9 for _ in range(9)]
        self.candidates = [[set() for _ in range(9)] for _ in range(9)]
        self.selected = None
        self.pencil_mode = False

        self.solve_steps = None
        self.solve_running = False

        self.build_ui()

    # --------------------------------------------------------
    #                   UI SETUP
    # --------------------------------------------------------
    def build_ui(self):
        top = tk.Frame(self.root, bg="#222831")
        top.pack(pady=5)

        self.pencil_label = tk.Label(top, text="Pencil: OFF",
                                     fg="white", bg="#222831", font=("Arial", 12))
        self.pencil_label.grid(row=0, column=0, padx=10)

        tk.Button(top, text="Pencil (P)", bg="#00adb5", fg="white",
                  command=self.toggle_pencil,
                  font=("Arial", 12, "bold")).grid(row=0, column=1, padx=10)

        tk.Button(top, text="Hint", bg="#393e46", fg="white",
                  command=self.hint,
                  font=("Arial", 12)).grid(row=0, column=2, padx=10)

        tk.Button(top, text="Solve", bg="#00adb5", fg="white",
                  command=self.start_animation,
                  font=("Arial", 12, "bold")).grid(row=0, column=3, padx=10)

        tk.Button(top, text="Clear", bg="#393e46", fg="white",
                  command=self.clear,
                  font=("Arial", 12)).grid(row=0, column=4, padx=10)

        # Canvas Grid
        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Configure>", self.redraw)
        self.canvas.bind("<Button-1>", self.handle_click)
        self.root.bind("<Key>", self.key_input)

    # --------------------------------------------------------
    #             CANVAS DRAWING FUNCTIONS
    # --------------------------------------------------------
    def redraw(self, event=None):
        self.canvas.delete("all")

        size = min(self.canvas.winfo_width(), self.canvas.winfo_height())
        self.cell = size / 9
        self.size = size

        self.x_offset = (self.canvas.winfo_width() - size)/2
        self.y_offset = (self.canvas.winfo_height() - size)/2

        self.draw_highlights()
        self.draw_numbers()
        self.draw_grid()

    def draw_grid(self):
        for i in range(10):
            thick = 3 if i % 3 == 0 else 1
            # horizontal
            self.canvas.create_line(
                self.x_offset,
                self.y_offset + i*self.cell,
                self.x_offset + self.size,
                self.y_offset + i*self.cell,
                width=thick
            )
            # vertical
            self.canvas.create_line(
                self.x_offset + i*self.cell,
                self.y_offset,
                self.x_offset + i*self.cell,
                self.y_offset + self.size,
                width=thick
            )

    def draw_highlights(self):
        if not self.selected:
            return
        sr, sc = self.selected

        for r in range(9):
            for c in range(9):
                x1 = self.x_offset + c*self.cell
                y1 = self.y_offset + r*self.cell
                x2 = x1 + self.cell
                y2 = y1 + self.cell

                if (r, c) == (sr, sc):
                    color = "#4da3ff"
                elif r == sr or c == sc or (r//3 == sr//3 and c//3 == sc//3):
                    color = "#fff3b0"
                else:
                    continue
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    def draw_numbers(self):
        for r in range(9):
            for c in range(9):
                x = self.x_offset + c*self.cell + self.cell/2
                y = self.y_offset + r*self.cell + self.cell/2
                val = self.board[r][c]

                if val != 0:
                    self.canvas.create_text(
                        x, y, text=str(val),
                        font=("Arial", int(self.cell/2)),
                        fill="black"
                    )
                elif self.candidates[r][c]:
                    text = "·".join(str(d) for d in sorted(self.candidates[r][c]))
                    self.canvas.create_text(
                        x, y, text=text,
                        font=("Arial", int(self.cell/5)),
                        fill="#444444"
                    )

    # --------------------------------------------------------
    #       INPUT: MOUSE CLICK & KEYBOARD HANDLING
    # --------------------------------------------------------
    def handle_click(self, event):
        x, y = event.x, event.y
        col = int((x - self.x_offset)//self.cell)
        row = int((y - self.y_offset)//self.cell)

        if 0 <= row < 9 and 0 <= col < 9:
            self.selected = (row, col)
            self.redraw()

    def key_input(self, event):
        if not self.selected:
            return
        r, c = self.selected
        ch = event.char

        if ch in ("p", "P"):
            self.toggle_pencil()
            return

        if ch == "0" or event.keysym in ("BackSpace", "Delete"):
            self.board[r][c] = 0
            self.candidates[r][c].clear()
            self.redraw()
            return

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

    # --------------------------------------------------------
    #                BUTTON FUNCTIONS
    # --------------------------------------------------------
    def toggle_pencil(self):
        self.pencil_mode = not self.pencil_mode
        self.pencil_label.config(text=f"Pencil: {'ON' if self.pencil_mode else 'OFF'}")

    def clear(self):
        self.board = [[0]*9 for _ in range(9)]
        self.candidates = [[set() for _ in range(9)] for _ in range(9)]
        self.selected = None
        self.redraw()

    # ----------------- SOLVE WITH ANIMATION -----------------
    def start_animation(self):
        if self.solve_running:
            return

        temp = [row[:] for row in self.board]
        self.solve_steps = solve_generator(temp)
        self.solve_running = True
        self.animate(temp)

    def animate(self, temp):
        try:
            step, r, c, val = next(self.solve_steps)

            if step == "place":
                self.board[r][c] = val
                self.selected = (r, c)

            elif step == "backtrack":
                self.board[r][c] = 0
                self.selected = (r, c)

            elif step == "deadend":
                self.selected = (r, c)

            elif step == "final":
                self.board = temp
                self.solve_running = False
                self.selected = None
                self.redraw()
                messagebox.showinfo("Solved!", "Sudoku solved with animation!")
                return

            self.redraw()
            self.root.after(20, lambda: self.animate(temp))

        except StopIteration:
            self.solve_running = False

    # ---------------------- HINT LOGIC ----------------------
    def hint(self):
        temp = [row[:] for row in self.board]
        cand = compute_all_candidates(temp)

        res = find_naked_single(temp, cand)
        if not res:
            res = find_hidden_single(temp, cand)

        if not res:
            messagebox.showinfo("Hint", "No logical hint found.")
            return

        r, c, val, msg = res
        self.board[r][c] = val
        self.candidates[r][c].clear()
        self.selected = (r, c)
        self.redraw()
        messagebox.showinfo("Hint", msg)


# ============================================================
#                        RUN APP
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    SudokuGUI(root)
    root.mainloop()
