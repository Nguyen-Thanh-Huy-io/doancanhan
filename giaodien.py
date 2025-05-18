# giaodien.py
import tkinter as tk
from tkinter import ttk, font, messagebox, scrolledtext
import threading
import time
from copy import deepcopy
import random

try:
    import thuattoan as algo
except ImportError:
    messagebox.showerror("Import Error", "Could not find 'thuattoan.py'. Make sure it's in the same directory and updated.")
    exit()
except AttributeError as e:
     messagebox.showerror("Attribute Error", f"Error importing from 'thuattoan.py'.\nMissing attribute: {e}\n\nPlease ensure 'thuattoan.py' is complete and updated.")
     exit()

# Import các class cửa sổ mới
try:
    from and_or_graph_visualization import AndOrVisualizerWindow
    from niemtin_visual import NiemTin
    # from kiemthu_giaodien import AlgorithmTestWindow # Đã xóa
    from csp_visualizer import CSPVisualizerWindow # <<< THÊM IMPORT MỚI
except ImportError as e:
    missing_files = []
    if 'AndOrVisualizerWindow' not in globals(): missing_files.append("and_or_graph_visualization.py")
    if 'NiemTin' not in globals(): missing_files.append("niemtin_visual.py")
    if 'CSPVisualizerWindow' not in globals(): missing_files.append("csp_visualizer.py")
    
    if missing_files:
        messagebox.showerror("Import Error", f"Could not import one or more window classes.\nMissing file(s): {', '.join(missing_files)}.\nMake sure these .py files exist in the same directory.\nError: {e}")
    print(f"Warning: Could not import some window classes: {e}")


class PuzzleGUI:
    def __init__(self, master):
        self.master = master
        master.title("8-Puzzle Solver")
        master.geometry("1200x700") # Điều chỉnh nếu cần không gian cho nhiều thuật toán hơn
        master.configure(bg="#E0E0E0")

        # --- Constants ---
        self.TILE_SIZE = 80
        self.BELIEF_TILE_SIZE = 40
        self.OR_VIZ_TILE_SIZE = 50
        self.GRID_PAD = 10
        self.FONT_TILE = font.Font(family="Helvetica", size=24, weight="bold")
        self.FONT_BELIEF_TILE = font.Font(family="Helvetica", size=12, weight="bold")
        self.FONT_OR_VIZ_TILE = font.Font(family="Helvetica", size=14, weight="bold")
        self.FONT_LABEL = font.Font(family="Helvetica", size=12)
        self.FONT_LABEL_RESULT = font.Font(family="Helvetica", size=10, weight="bold")
        self.FONT_BUTTON = font.Font(family="Helvetica", size=10)
        self.FONT_STATUS = font.Font(family="Helvetica", size=11, weight="bold")
        self.FONT_PATH = font.Font(family="Courier New", size=9)
        self.FONT_ENTRY = font.Font(family="Helvetica", size=14, weight="bold")
        self.COLOR_TILE = "#B0C4DE"
        self.COLOR_BLANK = "#F5F5F5"
        self.COLOR_TEXT = "#000000"
        self.COLOR_FRAME_BG = "#D3D3D3"
        self.COLOR_BUTTON_RUN = "#FFB6C1"
        self.COLOR_BUTTON_RESET = "#90EE90"
        self.COLOR_BUTTON_SET = "#B0E0E6"
        self.COLOR_STATUS_INFO = "#000080"
        self.COLOR_STATUS_SUCCESS = "#006400"
        self.COLOR_STATUS_ERROR = "#8B0000"
        self.COLOR_STATUS_WARNING = "#DAA520"
        self.COLOR_OR_VIZ_HIGHLIGHT = "#AEEEEE"
        self.COLOR_OR_VIZ_INVALID = "#D0D0D0"

        # --- State Variables ---
        self.default_initial_state = [[1, 2, 3], [4, 0, 6], [7, 5, 8]]
        self.initial_state_config = deepcopy(self.default_initial_state)
        self.goal_state_list = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
        self.current_display_state = deepcopy(self.initial_state_config)

        # --- Tkinter Variables ---
        self.selected_algorithm = tk.StringVar(value="BFS")
        self.selected_speed = tk.DoubleVar(value=0.4)
        self.status_text = tk.StringVar(value="Set initial state or use default. Then select algorithm and run.")
        self.result_status_text = tk.StringVar(value="Status: Idle")
        self.result_time_text = tk.StringVar(value="Time: -")

        # --- Main GUI Widgets (references) ---
        self.initial_entries = [[None for _ in range(3)] for _ in range(3)]
        self.initial_labels = [[None for _ in range(3)] for _ in range(3)]
        self.goal_labels = [[None for _ in range(3)] for _ in range(3)]
        self.run_button = None
        self.reset_button = None
        self.solution_display_text = None
        self.status_label = None
        self.result_status_label = None
        self.result_time_label = None

        # --- Animation State ---
        self.solution_path = None
        self.solution_step = 0
        self.animation_delay_ms = 400
        self.is_animating = False
        self.solve_thread = None

        # Tham chiếu đến các cửa sổ con (nếu đang mở)
        self.belief_window_instance = None
        self.partial_belief_window_instance = None
        self.and_or_viz_instance = None
        # self.algorithm_test_instance = None # Đã xóa
        self.csp_visualizer_instance = None # <<< THÊM THAM CHIẾU MỚI

        self.algo = algo

        self.create_widgets()
        self.update_grid(self.initial_labels, self.current_display_state)
        self.update_grid(self.goal_labels, self.goal_state_list)
        self._populate_entries_with_state(self.initial_state_config)

    def stop_animation(self):
        if self.is_animating: self.is_animating = False
        current_status_bottom = self.status_text.get().lower()
        current_status_top = self.result_status_text.get().lower()
        if ("solving" in current_status_bottom or "running" in current_status_top or "animating" in current_status_bottom) and \
           "error" not in current_status_bottom and "error" not in current_status_top and \
           "interrupted" not in current_status_bottom :
                 self.update_status("Solving/Animation interrupted by user.", "warning")
                 self.result_status_text.set("Status: Interrupted")
                 self.result_time_text.set("Time: -")
                 self.update_result_label_color("warning")
        try:
            if hasattr(self, 'run_button') and self.run_button and self.run_button.winfo_exists():
                 self.run_button.config(text="Run", command=self.start_solve, state=tk.NORMAL)
        except tk.TclError:
            pass
        except Exception as e:
            print(f"Error configuring run_button in stop_animation: {e}")

    def _create_grid_labels(self, parent_frame, tile_size, tile_font, is_or_viz=False):
        labels = [[None for _ in range(3)] for _ in range(3)]
        effective_tile_size = self.OR_VIZ_TILE_SIZE if is_or_viz else tile_size
        label_width = max(3, int(effective_tile_size / 18))
        label_height = max(1, int(effective_tile_size / 35))
        border_w = 1 if is_or_viz else 2
        for r_idx in range(3):
            for c_idx in range(3):
                label = tk.Label(parent_frame, text="", font=tile_font,
                                 width=label_width, height=label_height,
                                 borderwidth=border_w, relief=tk.RAISED,
                                 bg=self.COLOR_TILE, fg=self.COLOR_TEXT)
                label.grid(row=r_idx, column=c_idx, padx=1, pady=1)
                labels[r_idx][c_idx] = label
        return labels

    def update_grid(self, grid_labels, state_data):
        if not state_data or len(state_data) != 3: return
        for r_idx in range(3):
             if len(state_data[r_idx]) != 3: continue
             for c_idx in range(3):
                 if grid_labels[r_idx][c_idx] and grid_labels[r_idx][c_idx].winfo_exists():
                     try:
                         value = state_data[r_idx][c_idx]
                         if isinstance(value, str) and value.strip() == "":
                             grid_labels[r_idx][c_idx].config(text=value, bg=self.COLOR_BLANK, relief=tk.FLAT)
                         elif value == 0:
                             grid_labels[r_idx][c_idx].config(text="", bg=self.COLOR_BLANK, relief=tk.FLAT)
                         elif isinstance(value, str) and value == "-":
                             grid_labels[r_idx][c_idx].config(text=value, bg=self.COLOR_OR_VIZ_INVALID, relief=tk.FLAT, fg=self.COLOR_TEXT)
                         elif isinstance(value, str) and value in ["INV", "AL", "ID"]:
                             grid_labels[r_idx][c_idx].config(text=value, bg=self.COLOR_OR_VIZ_INVALID, relief=tk.FLAT, fg=self.COLOR_TEXT)
                         else:
                             grid_labels[r_idx][c_idx].config(text=str(value), bg=self.COLOR_TILE, fg=self.COLOR_TEXT, relief=tk.RAISED)
                     except tk.TclError: pass
                     except Exception as e: print(f"Error updating grid label ({r_idx},{c_idx}): {e}")

    def _populate_entries_with_state(self, state):
        if not state or len(state) != 3: return
        for r_idx in range(3):
            if len(state[r_idx]) != 3: continue
            for c_idx in range(3):
                if self.initial_entries[r_idx][c_idx]:
                    try:
                        self.initial_entries[r_idx][c_idx].delete(0, tk.END)
                        self.initial_entries[r_idx][c_idx].insert(0, str(state[r_idx][c_idx]))
                    except tk.TclError: pass

    def _validate_digit(self, P):
        if len(P) == 0: return True
        if len(P) == 1 and P.isdigit() and 0 <= int(P) <= 8: return True
        return False

    def on_algorithm_change(self):
        self.stop_animation()
        if self.solve_thread and self.solve_thread.is_alive():
            print("Algorithm changed: Stopping previous solver thread.")
            self.solve_thread = None

        selected_mode = self.selected_algorithm.get()
        current_status_lower = self.status_text.get().lower()
        if "interrupted" not in current_status_lower and "error" not in current_status_lower:
            self.update_status(f"Algorithm/Mode '{selected_mode}' selected. Click Run.", "info")
            self.result_status_text.set("Status: Idle")
            self.result_time_text.set("Time: -")
            self.update_result_label_color("info")
            self.clear_solution_display()

    def update_status(self, message, level="info"):
        self.status_text.set(message)
        color_map = { "info": self.COLOR_STATUS_INFO,"success": self.COLOR_STATUS_SUCCESS,"error": self.COLOR_STATUS_ERROR,"warning": self.COLOR_STATUS_WARNING}
        try:
             if hasattr(self, 'status_label') and self.status_label and self.status_label.winfo_exists():
                  self.status_label.config(fg=color_map.get(level, self.COLOR_STATUS_INFO))
        except tk.TclError: pass

    def update_animation_speed(self):
        try:
             self.animation_delay_ms = int(self.selected_speed.get() * 1000)
        except ValueError:
             self.animation_delay_ms = 400

    def update_result_label_color(self, level="info"):
        color_map = {"info": self.COLOR_STATUS_INFO,"success": self.COLOR_STATUS_SUCCESS,"error": self.COLOR_STATUS_ERROR,"warning": self.COLOR_STATUS_WARNING}
        status_color = color_map.get(level, self.COLOR_STATUS_INFO)
        try:
            if hasattr(self, 'result_status_label') and self.result_status_label and self.result_status_label.winfo_exists():
                 self.result_status_label.config(fg=status_color)
            if hasattr(self, 'result_time_label') and self.result_time_label and self.result_time_label.winfo_exists():
                 self.result_time_label.config(fg=status_color)
        except tk.TclError: pass

    def get_available_algorithms(self):
         return ["BFS", "DFS", "UCS", "IDS", "Greedy", "A*", "IDA*",
                 "HC", "Steepest HC", "Stochastic HC", "Beam Search",
                 "Simulated Annealing",
                 "Genetic Algorithm",
                 "Niềm Tin", "Niềm Tin 1 Phần",
                 "And-Or Visualizer",
                 "CSP: Backtracking",
                 "CSP: Forward Checking",
                 "CSP: Min-Conflicts",
                 "CSP: Generate AC-3 Board","Q-Learning",
                ]

    def create_widgets(self):
        top_frame = tk.Frame(self.master, bg=self.master.cget('bg'), padx=5, pady=5)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        display_frame = tk.Frame(top_frame, bg=self.master.cget('bg'))
        display_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        grid_frame = tk.Frame(display_frame, bg=display_frame.cget('bg'))
        grid_frame.pack(side=tk.LEFT, padx=(5, 10), pady=5, anchor='nw')
        initial_frame = tk.Frame(grid_frame, bd=2, relief=tk.SUNKEN, bg=self.COLOR_FRAME_BG)
        initial_frame.grid(row=0, column=0, padx=self.GRID_PAD, pady=0)
        tk.Label(initial_frame, text="Current / Initial State", font=self.FONT_LABEL, bg=self.COLOR_FRAME_BG).pack(pady=(5, 10))
        initial_grid_inner = tk.Frame(initial_frame, bg=self.COLOR_FRAME_BG); initial_grid_inner.pack(padx=5, pady=5)
        self.initial_labels = self._create_grid_labels(initial_grid_inner, self.TILE_SIZE, self.FONT_TILE)

        goal_frame = tk.Frame(grid_frame, bd=2, relief=tk.SUNKEN, bg=self.COLOR_FRAME_BG)
        goal_frame.grid(row=0, column=1, padx=self.GRID_PAD, pady=0)
        tk.Label(goal_frame, text="Goal State", font=self.FONT_LABEL, bg=self.COLOR_FRAME_BG).pack(pady=(5, 10))
        goal_grid_inner = tk.Frame(goal_frame, bg=self.COLOR_FRAME_BG); goal_grid_inner.pack(padx=5, pady=5)
        self.goal_labels = self._create_grid_labels(goal_grid_inner, self.TILE_SIZE, self.FONT_TILE)

        result_info_frame = tk.LabelFrame(display_frame, text="Result", font=self.FONT_LABEL, padx=8, pady=8, bg=self.COLOR_FRAME_BG)
        result_info_frame.pack(side=tk.LEFT, anchor='n', padx=5, pady=0)
        self.result_status_label = tk.Label(result_info_frame, textvariable=self.result_status_text, font=self.FONT_LABEL_RESULT, bg=self.COLOR_FRAME_BG, anchor="w", width=20)
        self.result_status_label.pack(fill=tk.X, pady=(0, 2))
        self.result_time_label = tk.Label(result_info_frame, textvariable=self.result_time_text, font=self.FONT_LABEL_RESULT, bg=self.COLOR_FRAME_BG, anchor="w", width=20)
        self.result_time_label.pack(fill=tk.X); self.update_result_label_color("info")

        path_frame = tk.LabelFrame(display_frame, text="Solution Path States", font=self.FONT_LABEL, padx=10, pady=10, bg=self.COLOR_FRAME_BG)
        path_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=0)
        self.solution_display_text = scrolledtext.ScrolledText(path_frame, wrap=tk.NONE, font=self.FONT_PATH, height=15, state=tk.DISABLED, bg="#FFFFFF", fg="#333333")
        self.solution_display_text.pack(fill=tk.BOTH, expand=True)

        input_state_frame = tk.LabelFrame(self.master, text="Input Initial State (0-8, 0 is blank)", font=self.FONT_LABEL, padx=10, pady=10, bg=self.COLOR_FRAME_BG)
        input_state_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 5))
        input_grid_frame = tk.Frame(input_state_frame, bg=self.COLOR_FRAME_BG); input_grid_frame.pack(side=tk.LEFT, padx=5)
        validate_cmd = self.master.register(self._validate_digit)
        for r_idx in range(3):
            for c_idx in range(3):
                entry = tk.Entry(input_grid_frame, width=3, font=self.FONT_ENTRY, justify='center', bd=2, relief=tk.SUNKEN, validate='key', validatecommand=(validate_cmd, '%P'))
                entry.grid(row=r_idx, column=c_idx, padx=2, pady=2); self.initial_entries[r_idx][c_idx] = entry
        set_button = tk.Button(input_state_frame, text="Set Initial State", font=self.FONT_BUTTON, bg=self.COLOR_BUTTON_SET, width=15, height=2, command=self.set_initial_state_from_entries)
        set_button.pack(side=tk.LEFT, padx=(20, 5), pady=5)

        bottom_control_area = tk.Frame(self.master, bg=self.master.cget('bg'), padx=10)
        bottom_control_area.pack(side=tk.TOP, fill=tk.X, pady=(5, 5))
        control_frame_inner = tk.Frame(bottom_control_area, bg=self.COLOR_FRAME_BG, bd=2, relief=tk.GROOVE, padx=10, pady=10)
        control_frame_inner.pack(side=tk.TOP, fill=tk.X); control_frame_inner.columnconfigure(0, weight=1); control_frame_inner.columnconfigure(1, weight=1); control_frame_inner.columnconfigure(2, weight=1)

        algo_frame = tk.LabelFrame(control_frame_inner, text="Algorithm / Mode", font=self.FONT_LABEL, padx=10, pady=10, bg=self.COLOR_FRAME_BG, bd=1, relief=tk.FLAT)
        algo_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        algorithms = self.get_available_algorithms()

        num_algo_cols = 3 # Có thể tăng nếu danh sách quá dài
        current_row = 0
        current_col = 0
        for algo_name_display in algorithms:
            rb = ttk.Radiobutton(algo_frame, text=algo_name_display, variable=self.selected_algorithm, value=algo_name_display, command=self.on_algorithm_change)
            rb.grid(row=current_row, column=current_col, padx=5, pady=2, sticky="w")
            current_col += 1
            if current_col >= num_algo_cols:
                current_col = 0
                current_row += 1
        for i in range(num_algo_cols):
            algo_frame.columnconfigure(i, weight=1)

        speed_frame = tk.LabelFrame(control_frame_inner, text="Animation Speed (Main Puzzle)", font=self.FONT_LABEL, padx=10, pady=10, bg=self.COLOR_FRAME_BG, bd=1, relief=tk.FLAT)
        speed_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        speeds = [("Slow (0.8s)", 0.8), ("Normal (0.4s)", 0.4), ("Fast (0.1s)", 0.1), ("Instant", 0.01)]
        for i, (text, val) in enumerate(speeds):
            rb = ttk.Radiobutton(speed_frame, text=text, variable=self.selected_speed, value=val, command=self.update_animation_speed); rb.pack(anchor=tk.W, pady=2)
        self.selected_speed.set(0.4); self.update_animation_speed()

        action_frame = tk.Frame(control_frame_inner, bg=self.COLOR_FRAME_BG)
        action_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        action_frame.columnconfigure(0, weight=1)
        action_frame.rowconfigure(0, weight=1)
        action_frame.rowconfigure(1, weight=1)

        self.run_button = tk.Button(action_frame, text="Run", font=self.FONT_BUTTON, bg=self.COLOR_BUTTON_RUN, width=12, height=2, command=self.start_solve)
        self.run_button.grid(row=0, column=0, pady=5, padx=10, sticky="ew")
        self.reset_button = tk.Button(action_frame, text="Reset", font=self.FONT_BUTTON, bg=self.COLOR_BUTTON_RESET, width=12, height=2, command=self.reset_puzzle)
        self.reset_button.grid(row=1, column=0, pady=5, padx=10, sticky="ew")

        status_frame = tk.Frame(self.master, bg=self.master.cget('bg'), padx=10, pady=5)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = tk.Label(status_frame, textvariable=self.status_text, font=self.FONT_STATUS, fg=self.COLOR_STATUS_INFO, bg=status_frame.cget('bg'), anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=5)

    def set_initial_state_from_entries(self):
        new_state = [[0,0,0],[0,0,0],[0,0,0]]
        entered_values = set(); contains_zero = False
        try:
            for r in range(3):
                for c in range(3):
                    val_str = self.initial_entries[r][c].get()
                    if not val_str.isdigit(): raise ValueError(f"Invalid input at ({r},{c}): '{val_str}' not digit.")
                    val = int(val_str)
                    if not (0 <= val <= 8): raise ValueError(f"Invalid input at ({r},{c}): '{val}' out of range 0-8.")
                    if val == 0: contains_zero = True
                    if val != 0 and val in entered_values: raise ValueError(f"Duplicate input: '{val}'.")
                    if val != 0: entered_values.add(val)
                    new_state[r][c] = val
            if not contains_zero: raise ValueError("Must contain blank tile (0).")
            if len(entered_values) != 8: raise ValueError("Must contain numbers 1-8 once.")

            self.stop_animation_and_thread()
            self.initial_state_config = new_state
            self.current_display_state = deepcopy(new_state)
            self.update_grid(self.initial_labels, self.current_display_state)
            self.clear_solution_display()
            self.update_status("New initial state set.", "success")
            self.result_status_text.set("Status: Idle"); self.result_time_text.set("Time: -")
            self.update_result_label_color("info")
            if not self.algo.is_solvable(new_state):
                 messagebox.showwarning("Unsolvable State", "Entered puzzle state is mathematically unsolvable.")
        except ValueError as e: messagebox.showerror("Invalid Input", str(e), parent=self.master)
        except Exception as e: messagebox.showerror("Error", f"Unexpected error: {e}", parent=self.master)

    def reset_puzzle(self):
        self.stop_animation_and_thread()
        self.initial_state_config = deepcopy(self.default_initial_state)
        self.current_display_state = deepcopy(self.initial_state_config)
        self.update_grid(self.initial_labels, self.current_display_state)
        self._populate_entries_with_state(self.initial_state_config)
        self.update_status("Puzzle reset to default. Select algorithm and run.")
        self.clear_solution_display()
        self.result_status_text.set("Status: Idle")
        self.result_time_text.set("Time: -")
        self.update_result_label_color("info")

    def start_solve(self):
        self.stop_animation_and_thread()
        algo_name_display = self.selected_algorithm.get()

        if algo_name_display == "Niềm Tin":
            if not hasattr(self, 'belief_window_instance') or \
               not self.belief_window_instance or \
               not self.belief_window_instance.window.winfo_exists():
                try: self.belief_window_instance = NiemTin(self, "Belief")
                except NameError: messagebox.showerror("Lỗi Import", "Không thể mở cửa sổ Niềm Tin.\nClass NiemTin không tìm thấy."); return
            else: self.belief_window_instance.window.lift()
            self.update_status("Opened Belief Solver window.", "info")
            self.result_status_text.set("Status: Belief Mode"); self.update_result_label_color("info")
            return

        elif algo_name_display == "Niềm Tin 1 Phần":
            if not hasattr(self, 'partial_belief_window_instance') or \
               not self.partial_belief_window_instance or \
               not self.partial_belief_window_instance.window.winfo_exists():
                try: self.partial_belief_window_instance = NiemTin(self, "PartialBelief")
                except NameError: messagebox.showerror("Lỗi Import", "Không thể mở cửa sổ Niềm Tin 1 Phần.\nClass NiemTin không tìm thấy."); return
            else: self.partial_belief_window_instance.window.lift()
            self.update_status("Opened Partial Belief Solver window.", "info")
            self.result_status_text.set("Status: Partial Belief Mode"); self.update_result_label_color("info")
            return

        elif algo_name_display == "And-Or Visualizer":
            if not hasattr(self, 'and_or_viz_instance') or \
               not self.and_or_viz_instance or \
               not self.and_or_viz_instance.window.winfo_exists():
                try: self.and_or_viz_instance = AndOrVisualizerWindow(self)
                except NameError: messagebox.showerror("Lỗi Import", "Không thể mở And-Or Visualizer.\nClass AndOrVisualizerWindow không tìm thấy."); return
            else: self.and_or_viz_instance.window.lift()
            self.update_status("Opened And-Or Search Visualizer.", "info")
            self.result_status_text.set("Status: Visualizing And-Or"); self.update_result_label_color("info")
            return

        elif algo_name_display.startswith("CSP:"):
            if not hasattr(self, 'csp_visualizer_instance') or \
               not self.csp_visualizer_instance or \
               not self.csp_visualizer_instance.window.winfo_exists():
                try:
                    if 'CSPVisualizerWindow' not in globals():
                        messagebox.showerror("Lỗi Import", "Không thể mở CSP Visualizer.\nClass CSPVisualizerWindow không được tìm thấy hoặc chưa được import.")
                        return
                    self.csp_visualizer_instance = CSPVisualizerWindow(self)
                except NameError:
                    messagebox.showerror("Lỗi Import", "Không thể mở CSP Visualizer.\nClass CSPVisualizerWindow không được tìm thấy (NameError).")
                    return
                except Exception as e_csp:
                    messagebox.showerror("Lỗi Mở Cửa Sổ", f"Không thể mở CSP Visualizer.\nLỗi: {e_csp}")
                    return
            else:
                self.csp_visualizer_instance.window.lift()
            
            self.update_status(f"Opened CSP Tools Window ({algo_name_display}).", "info")
            self.result_status_text.set(f"Status: {algo_name_display}"); self.update_result_label_color("info")
            return

        # Standard algorithm solving (non-windowed)
        self.current_display_state = deepcopy(self.initial_state_config)
        self.update_grid(self.initial_labels, self.current_display_state)
        self.solution_path = None; self.solution_step = 0; self.clear_solution_display()
        self.result_status_text.set("Status: Running..."); self.result_time_text.set("Time: -")
        self.update_result_label_color("info"); self.update_status(f"Solving with {algo_name_display}...", "info")

        try:
            if self.run_button and self.run_button.winfo_exists():
                 self.run_button.config(text="Stop", command=self.stop_animation_and_thread, state=tk.NORMAL)
        except tk.TclError: pass

        algo_key = algo_name_display.lower().replace("*", "_star").replace(" ", "_").replace("-","_")
        # Remap specific keys if needed (already done for HC variants, Greedy)
        if algo_key == "bfs": algo_key = "bfs"
        elif algo_key == "dfs": algo_key = "dfs"
        elif algo_key == "ucs": algo_key = "ucs"
        elif algo_key == "ids": algo_key = "iddfs"
        elif algo_key == "greedy": algo_key = "greedy_search"
        elif algo_key == "a_star": algo_key = "a_star"
        elif algo_key == "ida_star": algo_key = "ida_star"
        elif algo_key == "simulated_annealing": algo_key = "simulated_annealing"
        elif algo_key == "beam_search": algo_key = "beam_search"
        elif algo_key == "genetic_algorithm": algo_key = "genetic_algorithm"
        elif algo_key == "hc": algo_key = "hill_climbing"
        elif algo_key == "steepest_hc": algo_key = "steepest_hill_climbing"
        elif algo_key == "stochastic_hc": algo_key = "stochastic_hill_climbing"
        elif algo_key == "q_learning": algo_key = "q_learning_train_and_solve"
        # "backtracking" and "and_or_search" (direct solve) keys are no longer selected this way

        solver_func = getattr(self.algo, algo_key, None)
        if not solver_func:
            error_msg = f"Error: Algorithm function '{algo_key}' for '{algo_name_display}' not found in thuattoan.py or not a standard solver."
            self.update_status(error_msg, "error")
            self.result_status_text.set("Status: Error"); self.result_time_text.set("Time: N/A")
            self.update_result_label_color("error")
            if self.run_button and self.run_button.winfo_exists():
                 self.run_button.config(text="Run", command=self.start_solve, state=tk.NORMAL)
            return

        solve_initial_state = deepcopy(self.initial_state_config)
        solve_goal_state = deepcopy(self.goal_state_list)

        if not self.algo.is_solvable(solve_initial_state) and \
           algo_key not in ["genetic_algorithm", "q_learning_train_and_solve"]: # Removed "and_or_search"
            messagebox.showwarning("Unsolvable Puzzle", f"Initial state for '{algo_name_display}' is unsolvable.", parent=self.master)
            self.update_status(f"Warning: Initial state unsolvable for {algo_name_display}.", "warning")

        self.solve_thread = threading.Thread(target=self.run_solver_thread,
                                             args=(solver_func, solve_initial_state, solve_goal_state, algo_name_display),
                                             daemon=True)
        self.solve_thread.start()

    def stop_animation_and_thread(self):
        self.stop_animation()
        if self.solve_thread and self.solve_thread.is_alive():
            print("Signaling solver thread to stop.")
            self.solve_thread = None
        if not self.is_animating:
            self._safe_reset_run_button()

    def run_solver_thread(self, solver_func, initial_state_for_solver, goal_state_for_solver, algo_name_display):
        current_thread_obj = threading.current_thread()
        start_time = time.time(); solution = None; solve_duration = 0
        try:
            if not (hasattr(self, 'solve_thread') and self.solve_thread == current_thread_obj):
                print(f"Solver thread for {algo_name_display} exiting early (no longer active)."); return

            solution = solver_func(initial_state_for_solver, goal_state_for_solver)

            end_time = time.time(); solve_duration = end_time - start_time
            if hasattr(self, 'solve_thread') and self.solve_thread == current_thread_obj:
                self.master.after(0, self.handle_solve_result, solution, solve_duration, algo_name_display)
            else: print(f"Solver for {algo_name_display} finished but not active. Result not handled.")
        except Exception as e:
            end_time = time.time(); solve_duration = end_time - start_time
            print(f"!!! Solver Error ({algo_name_display}, {solve_duration:.3f}s): {e}")
            import traceback; traceback.print_exc()
            if hasattr(self, 'solve_thread') and self.solve_thread == current_thread_obj:
                err_msg = f"Error during {algo_name_display} ({solve_duration:.3f}s). See console."
                self.master.after(0, lambda m=err_msg: self.update_status(m, "error"))
                self.master.after(0, lambda: self.result_status_text.set("Status: Solver Error"))
                self.master.after(0, lambda d=solve_duration: self.result_time_text.set(f"Time: {d:.3f}s"))
                self.master.after(0, lambda: self.update_result_label_color("error"))
                self.master.after(0, self.clear_solution_display)
        finally:
            if hasattr(self, 'solve_thread') and self.solve_thread == current_thread_obj:
                self.master.after(10, self._safe_reset_run_button)
            if hasattr(self, 'solve_thread') and self.solve_thread == current_thread_obj:
                self.solve_thread = None

    def _safe_reset_run_button(self):
        try:
            if self.run_button and self.run_button.winfo_exists():
                if not self.is_animating and not (self.solve_thread and self.solve_thread.is_alive()):
                     self.run_button.config(text="Run", command=self.start_solve, state=tk.NORMAL)
        except tk.TclError: pass

    def handle_solve_result(self, solution, duration, algo_name_display="Algorithm"):
        result_status = "Status: -"; result_time = f"Time: {duration:.3f}s"; result_level = "info"
        num_steps = 0; can_animate = False; state_sequence = None
        if solution is not None and isinstance(solution, list) and \
           all(isinstance(move, (tuple, list)) and len(move) == 2 and \
               isinstance(move[0], int) and isinstance(move[1], int) for move in solution):
            self.solution_path = solution; self.solution_step = 0; num_steps = len(self.solution_path)
            can_animate = True if num_steps > 0 else False
            try:
                state_sequence = self.reconstruct_state_sequence(self.initial_state_config, self.solution_path)
                if state_sequence:
                    result_status = "Status: Solution Found"; result_level = "success"
                    msg = f"Solution found by {algo_name_display}: {num_steps} steps ({duration:.3f}s)."
                    if num_steps == 0: msg = f"Solution by {algo_name_display}: 0 steps (Initial is goal)."
                    self.update_status(msg, "success"); self.display_solution_states(state_sequence)
                else:
                    result_status = "Status: Path Error"; result_level = "error"
                    self.update_status(f"Error reconstructing states from path ({algo_name_display}, {duration:.3f}s).", "error")
                    self.clear_solution_display(); can_animate = False
            except Exception as recon_e:
                print(f"Error during state reconstruction: {recon_e}")
                result_status = "Status: Path Error"; result_level = "error"
                self.update_status(f"Error reconstructing states: {recon_e}", "error")
                self.clear_solution_display(); can_animate = False
        else:
            if algo_name_display == "Q-Learning" and solution is None and hasattr(self.algo, 'TRAINING_IN_PROGRESS') and not self.algo.TRAINING_IN_PROGRESS:
                 result_status = "Status: Q-Table Ready"
                 status_msg = f"Q-Learning training might be complete or Q-table used. Solving phase did not yield a path in time or Q-values insufficient. ({duration:.3f}s)."
                 result_level = "info" if hasattr(self.algo, 'Q_TABLE_GLOBAL') and self.algo.Q_TABLE_GLOBAL else "warning"
            else:
                result_status = "Status: No Solution" if solution is None else "Status: Invalid Result"
                result_level = "warning" if solution is None else "error"
                status_msg = f"No solution found by {algo_name_display} ({duration:.3f}s)." if solution is None else f"Error: {algo_name_display} returned unexpected result type ({type(solution)}) ({duration:.3f}s)."
            self.update_status(status_msg, result_level)
            self.clear_solution_display(); can_animate = False

        self.result_status_text.set(result_status); self.result_time_text.set(result_time)
        self.update_result_label_color(result_level)

        if can_animate and self.animation_delay_ms > 15:
             self.update_status(self.status_text.get() + " Animating...", "success")
             self.is_animating = True
             try:
                  if self.run_button and self.run_button.winfo_exists():
                       self.run_button.config(text="Stop", command=self.stop_animation_and_thread, state=tk.NORMAL)
             except tk.TclError: pass
             self.master.after(self.animation_delay_ms, self.animate_step)
        elif can_animate:
             try:
                 final_state = state_sequence[-1] if state_sequence else self.reconstruct_final_state(self.initial_state_config, self.solution_path)
                 if final_state:
                      self.current_display_state = final_state
                      self.update_grid(self.initial_labels, self.current_display_state)
                      current_status = self.status_text.get().replace(" Animating...", "")
                      self.update_status(current_status + " Applied instantly.", "success")
                 else: self.update_status(f"Error applying final state from path.", "error")
             except Exception as final_e:
                  print(f"Error reconstructing/applying final state: {final_e}")
                  self.update_status(f"Error applying final state: {final_e}", "error")
             self._safe_reset_run_button()
        else: self._safe_reset_run_button()

    def animate_step(self):
        if not self.is_animating: return
        if not self.solution_path or self.solution_step >= len(self.solution_path):
            self.is_animating = False
            current_status = self.status_text.get()
            if " Animating..." in current_status:
                self.update_status(current_status.replace(" Animating...", " Animation finished."), "success")
            self._safe_reset_run_button(); return

        move_coord = self.solution_path[self.solution_step]
        blank_pos = self.algo.find_blank(self.current_display_state)
        if blank_pos is None:
            print("Animation Error: Blank tile not found."); self.update_status("Animation error: Blank tile lost.", "error")
            self.stop_animation_and_thread(); return

        blank_r, blank_c = blank_pos; is_adjacent_move = False
        if isinstance(move_coord, (tuple, list)) and len(move_coord) == 2:
             move_r, move_c = move_coord
             if self.algo.is_valid(move_r, move_c) and abs(blank_r - move_r) + abs(blank_c - move_c) == 1:
                  is_adjacent_move = True
        if is_adjacent_move:
            self.current_display_state[blank_r][blank_c], self.current_display_state[move_r][move_c] = \
                self.current_display_state[move_r][move_c], self.current_display_state[blank_r][blank_c]
            self.update_grid(self.initial_labels, self.current_display_state)
            self.solution_step += 1
            if self.is_animating: self.master.after(self.animation_delay_ms, self.animate_step)
        else:
            print(f"Anim Error: Invalid move {move_coord} from blank {blank_pos} at step {self.solution_step}.")
            self.update_status(f"Animation error: Invalid move ({move_coord}).", "error")
            self.stop_animation_and_thread()

    def reconstruct_state_sequence(self, initial_state_list, path_coords):
        state_sequence = [deepcopy(initial_state_list)]
        if not path_coords: return state_sequence
        current_state = deepcopy(initial_state_list)
        for i, move_coord in enumerate(path_coords):
            blank_pos = self.algo.find_blank(current_state)
            if blank_pos is None: return None
            blank_r, blank_c = blank_pos
            if not (isinstance(move_coord, (tuple, list)) and len(move_coord) == 2): return None
            move_r, move_c = move_coord
            if not (self.algo.is_valid(move_r, move_c) and abs(blank_r - move_r) + abs(blank_c - move_c) == 1):
                print(f"Reconstruction error: Move {move_coord} is not adjacent to blank {blank_pos} at step {i}")
                return None
            current_state[blank_r][blank_c], current_state[move_r][move_c] = \
                current_state[move_r][move_c], current_state[blank_r][blank_c]
            state_sequence.append(deepcopy(current_state))
        return state_sequence

    def reconstruct_final_state(self, initial_state_list, path_coords):
         if not path_coords: return deepcopy(initial_state_list)
         current_state = deepcopy(initial_state_list)
         for i, move_coord in enumerate(path_coords):
             blank_pos = self.algo.find_blank(current_state)
             if blank_pos is None: return None
             blank_r, blank_c = blank_pos
             if not (isinstance(move_coord, (tuple, list)) and len(move_coord) == 2): return None
             move_r, move_c = move_coord
             if not (self.algo.is_valid(move_r, move_c) and abs(blank_r - move_r) + abs(blank_c - move_c) == 1): return None
             current_state[blank_r][blank_c], current_state[move_r][move_c] = current_state[move_r][move_c], current_state[blank_r][blank_c]
         return current_state

    def format_state(self, state):
        if not state or len(state) != 3 or any(len(row) != 3 for row in state):
            return "  [Invalid State Format]\n"
        return "\n".join(["  " + " ".join(map(lambda x: str(x) if x != 0 else '_', row)) for row in state]) + "\n"

    def display_solution_states(self, state_sequence):
        self.clear_solution_display()
        if not state_sequence: return
        try:
            if hasattr(self, 'solution_display_text') and self.solution_display_text and self.solution_display_text.winfo_exists():
                self.solution_display_text.config(state=tk.NORMAL)
                for i, state in enumerate(state_sequence):
                    step_header = f"Step {i}:\n" if i > 0 else "Initial State (Step 0):\n"
                    self.solution_display_text.insert(tk.END, step_header)
                    self.solution_display_text.insert(tk.END, self.format_state(state))
                    if i < len(state_sequence) - 1: self.solution_display_text.insert(tk.END, "----\n")
                self.solution_display_text.config(state=tk.DISABLED); self.solution_display_text.see("1.0")
        except tk.TclError: pass
        except Exception as e: print(f"Error displaying solution states: {e}")

    def clear_solution_display(self):
        try:
            if hasattr(self, 'solution_display_text') and self.solution_display_text and self.solution_display_text.winfo_exists():
                self.solution_display_text.config(state=tk.NORMAL)
                self.solution_display_text.delete('1.0', tk.END)
                self.solution_display_text.config(state=tk.DISABLED)
        except tk.TclError: pass
        except Exception as e: print(f"Error clearing solution display: {e}")

    def on_belief_type_window_closed(self, belief_type):
        if belief_type == "Belief":
            self.belief_window_instance = None
            if self.selected_algorithm.get() == "Niềm Tin":
                 self.update_status("Belief Solver closed.", "info")
        elif belief_type == "PartialBelief":
            self.partial_belief_window_instance = None
            if self.selected_algorithm.get() == "Niềm Tin 1 Phần":
                 self.update_status("Partial Belief Solver closed.", "info")

        current_selection = self.selected_algorithm.get()
        if current_selection in ["Niềm Tin", "Niềm Tin 1 Phần"]:
            self.result_status_text.set("Status: Idle")
            self.result_time_text.set("Time: -")
            self.update_result_label_color("info")

    def on_and_or_viz_window_closed(self):
        self.and_or_viz_instance = None
        if self.selected_algorithm.get() == "And-Or Visualizer":
            self.update_status("And-Or Visualizer closed.", "info")
            self.result_status_text.set("Status: Idle")
            self.result_time_text.set("Time: -")
            self.update_result_label_color("info")

    def on_csp_visualizer_window_closed(self):
        self.csp_visualizer_instance = None
        current_selection = self.selected_algorithm.get()
        if current_selection.startswith("CSP:"):
            self.update_status("CSP Visualizer window closed.", "info")
            self.result_status_text.set("Status: Idle")
            self.result_time_text.set("Time: -")
            self.update_result_label_color("info")


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    try:
        required_attrs = ['bfs', 'dfs', 'ucs', 'a_star', 'is_solvable', 'find_blank',
                          'state_to_tuple', 'get_neighbors', 'manhattan_distance',
                          'and_or_search_visual', 'moves_delta', 'move_names',
                          'q_learning_train_and_solve', # Giữ lại Q-Learning
                          # Thêm các hàm CSP đã định nghĩa trong thuattoan.py
                          'backtracking_csp',
                          'forward_checking_csp',
                          'min_conflicts_csp',
                          'ac3_generate_board_csp',
                          'are_tiles_adjacent_3_6_csp' # Hàm helper nếu nó là public và cần thiết
                         ]
        missing = [attr for attr in required_attrs if not hasattr(algo, attr)]
        if missing:
             error_msg = f"Module 'thuattoan.py' is missing required functions/variables: {', '.join(missing)}"
             print(f"FATAL ERROR: {error_msg}")
             messagebox.showerror("Initialization Error", error_msg)
             if root and root.winfo_exists(): root.destroy()
             exit()
        else:
             print("All required functions/variables from thuattoan.py found.")
             gui = PuzzleGUI(root)
             root.mainloop()
    except Exception as main_e:
        print(f"Fatal error starting GUI: {main_e}")
        import traceback
        traceback.print_exc()
        try:
            if root and root.winfo_exists():
                messagebox.showerror("Startup Error", f"Could not start the application.\nError: {main_e}\n\nPlease ensure all .py files are correct, complete, and in the same directory.")
        except tk.TclError: pass
        finally:
            if root and root.winfo_exists():
                root.destroy()