import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from copy import deepcopy
import threading
import time

class CSPVisualizerWindow:
    def __init__(self, master_gui):
        self.master_gui = master_gui
        self.algo = master_gui.algo            
        self.FONT_LABEL = master_gui.FONT_LABEL
        self.FONT_BUTTON = master_gui.FONT_BUTTON
        self.FONT_PATH = master_gui.FONT_PATH
        self.TILE_SIZE = master_gui.TILE_SIZE          
        self.FONT_TILE = master_gui.FONT_TILE
        self.COLOR_FRAME_BG = master_gui.COLOR_FRAME_BG
        self.COLOR_TILE = master_gui.COLOR_TILE
        self.COLOR_BLANK = master_gui.COLOR_BLANK
        self.COLOR_TEXT = master_gui.COLOR_TEXT
        
        self.window = tk.Toplevel(master_gui.master)
        self.window.title("CSP Solver Visualizer (8-Puzzle)")
        self.window.geometry("800x750")         
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self.current_board_to_solve = deepcopy(self.master_gui.initial_state_config)          
        self.goal_board_config = deepcopy(self.master_gui.goal_state_list)
        
        self.csp_board_labels = [[None for _ in range(3)] for _ in range(3)]
        self.solve_thread = None
        self.animation_path = None
        self.animation_step = 0
        self.is_animating = False
        self.animation_delay_ms = 300            
        self.selected_csp_algo_var = tk.StringVar(value="Backtracking CSP")
        self.depth_limit_var = tk.StringVar(value=str(self.algo.CSP_BACKTRACKING_MAX_DEPTH))          
        self.iterations_var = tk.StringVar(value=str(self.algo.CSP_MIN_CONFLICTS_MAX_ITERATIONS))  
        self._setup_ui()
        self._update_csp_board_display(self.current_board_to_solve)

    def _create_csp_grid_labels(self, parent_frame):          
        labels = [[None for _ in range(3)] for _ in range(3)]
        label_width = max(3, int(self.TILE_SIZE / 18))
        label_height = max(1, int(self.TILE_SIZE / 35))
        for r_idx in range(3):
            for c_idx in range(3):
                label = tk.Label(parent_frame, text="", font=self.FONT_TILE,
                                 width=label_width, height=label_height,
                                 borderwidth=2, relief=tk.RAISED,
                                 bg=self.COLOR_TILE, fg=self.COLOR_TEXT)
                label.grid(row=r_idx, column=c_idx, padx=1, pady=1)
                labels[r_idx][c_idx] = label
        return labels

    def _update_csp_board_display(self, board_data):          
        if not board_data or len(board_data) != 3: return
        for r_idx in range(3):
            if len(board_data[r_idx]) != 3: continue
            for c_idx in range(3):
                if self.csp_board_labels[r_idx][c_idx] and self.csp_board_labels[r_idx][c_idx].winfo_exists():
                    try:
                        value = board_data[r_idx][c_idx]
                        if value == 0:
                            self.csp_board_labels[r_idx][c_idx].config(text="", bg=self.COLOR_BLANK, relief=tk.FLAT)
                        else:
                            self.csp_board_labels[r_idx][c_idx].config(text=str(value), bg=self.COLOR_TILE, fg=self.COLOR_TEXT, relief=tk.RAISED)
                    except tk.TclError: pass
    
    def _log_message(self, message, clear_first=False):
        if hasattr(self, 'log_text_widget') and self.log_text_widget.winfo_exists():
            self.log_text_widget.config(state=tk.NORMAL)
            if clear_first:
                self.log_text_widget.delete('1.0', tk.END)
            self.log_text_widget.insert(tk.END, str(message) + "\n")
            self.log_text_widget.see(tk.END)
            self.log_text_widget.config(state=tk.DISABLED)
        else:
            print(message)

    def _setup_ui(self):
        main_pane = ttk.PanedWindow(self.window, orient=tk.VERTICAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)          
        top_frame_container = ttk.Frame(main_pane)
        main_pane.add(top_frame_container, weight=2)

        board_display_frame = ttk.LabelFrame(top_frame_container, text="Current Puzzle State", padding=10)
        board_display_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)          
        grid_center_frame = ttk.Frame(board_display_frame)
        grid_center_frame.pack(expand=True)          
        self.csp_board_labels = self._create_csp_grid_labels(grid_center_frame)

        controls_frame = ttk.LabelFrame(top_frame_container, text="CSP Controls", padding=10)
        controls_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)

        ttk.Label(controls_frame, text="Algorithm:", font=self.FONT_LABEL).pack(pady=(0,2), anchor="w")
        csp_algorithms = ["Backtracking CSP", "Forward Checking CSP", "Min-Conflicts CSP"]
        self.csp_algo_combo = ttk.Combobox(controls_frame, textvariable=self.selected_csp_algo_var, 
                                           values=csp_algorithms, state="readonly", font=self.FONT_LABEL, width=25)
        self.csp_algo_combo.pack(pady=(0,10), fill="x")
        self.csp_algo_combo.bind("<<ComboboxSelected>>", self._on_algo_select_csp)

        self.param_frame = ttk.Frame(controls_frame)          
        self.param_frame.pack(fill="x", pady=(0,10))

        self.depth_label = ttk.Label(self.param_frame, text="Depth Limit:", font=self.FONT_LABEL)
        self.depth_entry = ttk.Entry(self.param_frame, textvariable=self.depth_limit_var, font=self.FONT_LABEL, width=7)
        
        self.iterations_label = ttk.Label(self.param_frame, text="Max Iterations:", font=self.FONT_LABEL)
        self.iterations_entry = ttk.Entry(self.param_frame, textvariable=self.iterations_var, font=self.FONT_LABEL, width=7)
        self._on_algo_select_csp()  
        ttk.Button(controls_frame, text="Generate Board (AC-3)", command=self._generate_ac3_board_action, style="Accent.TButton").pack(pady=5, fill="x")
        ttk.Button(controls_frame, text="Run Selected Algorithm", command=self._run_selected_csp_algo, style="Accent.TButton").pack(pady=5, fill="x")
        ttk.Button(controls_frame, text="Set as Main Puzzle", command=self._set_as_main_puzzle_action).pack(pady=5, fill="x")
        ttk.Button(controls_frame, text="Reset This Board", command=self._reset_csp_board_action).pack(pady=5, fill="x")          
        log_frame_container = ttk.LabelFrame(main_pane, text="Log & Results", padding=10)
        main_pane.add(log_frame_container, weight=1)
        
        self.log_text_widget = scrolledtext.ScrolledText(log_frame_container, height=10, font=self.FONT_PATH, wrap=tk.WORD)
        self.log_text_widget.pack(fill=tk.BOTH, expand=True)
        self.log_text_widget.insert(tk.END, "CSP Visualizer ready. Generate a board or run an algorithm.\n")
        self.log_text_widget.config(state=tk.DISABLED)

    def _on_algo_select_csp(self, event=None):
        selected = self.selected_csp_algo_var.get()          
        self.depth_label.pack_forget()
        self.depth_entry.pack_forget()
        self.iterations_label.pack_forget()
        self.iterations_entry.pack_forget()

        if selected == "Backtracking CSP" or selected == "Forward Checking CSP":
            self.depth_label.pack(side="left", padx=(0,5)); self.depth_entry.pack(side="left")
        elif selected == "Min-Conflicts CSP":
            self.iterations_label.pack(side="left", padx=(0,5)); self.iterations_entry.pack(side="left")


    def _generate_ac3_board_action(self):
        self._stop_solver_thread_and_animation()
        self._log_message("Generating AC-3 board...", clear_first=True)
        generated_board = self.algo.ac3_generate_board_csp()
        if generated_board:
            self.current_board_to_solve = generated_board
            self._update_csp_board_display(self.current_board_to_solve)
            self._log_message("New AC-3 board generated and displayed.")
            if not self.algo.are_tiles_adjacent_3_6_csp(generated_board):
                 self._log_message("Warning: Generated board does NOT have 3&6 adjacent (might be fallback).")
            else:
                 self._log_message("Constraint: Tiles 3 and 6 ARE adjacent in this board.")
        else:
            self._log_message("Failed to generate AC-3 board.")
            messagebox.showerror("Generation Failed", "Could not generate an AC-3 board.", parent=self.window)

    def _run_selected_csp_algo(self):
        self._stop_solver_thread_and_animation()
        self.animation_path = None
        self.animation_step = 0

        algo_name = self.selected_csp_algo_var.get()
        initial_s = deepcopy(self.current_board_to_solve)
        goal_s = deepcopy(self.goal_board_config)  
        self._log_message(f"\nRunning {algo_name} on current board...", clear_first=True)
        if not self.algo.is_solvable(initial_s):              self._log_message("Warning: The current board may not be solvable to the standard goal state.")
        if algo_name == "Backtracking CSP" and not self.algo.are_tiles_adjacent_3_6_csp(initial_s):
            self._log_message("Info: For Backtracking CSP, the 3&6 adjacency rule only applies if they are ALREADY adjacent.")


        solver_func = None
        params = {}
        if algo_name == "Backtracking CSP":
            solver_func = self.algo.backtracking_csp
            try: params['depth'] = int(self.depth_limit_var.get())
            except ValueError: self._log_message("Invalid depth limit. Using default."); params['depth'] = self.algo.CSP_BACKTRACKING_MAX_DEPTH
        elif algo_name == "Forward Checking CSP":
            solver_func = self.algo.forward_checking_csp
            try: params['depth'] = int(self.depth_limit_var.get())
            except ValueError: self._log_message("Invalid depth limit. Using default."); params['depth'] = self.algo.CSP_FORWARD_CHECKING_MAX_DEPTH
        elif algo_name == "Min-Conflicts CSP":
            solver_func = self.algo.min_conflicts_csp
            try: params['max_iterations'] = int(self.iterations_var.get())
            except ValueError: self._log_message("Invalid iterations. Using default."); params['max_iterations'] = self.algo.CSP_MIN_CONFLICTS_MAX_ITERATIONS
        else:
            self._log_message(f"Algorithm {algo_name} not recognized for direct run.")
            return

        if solver_func:              self.solve_thread = threading.Thread(
                target=self._execute_csp_solver,
                args=(solver_func, initial_s, goal_s, algo_name, params),
                daemon=True
            )
        self.solve_thread.start()

    def _execute_csp_solver(self, solver_func, initial_s, goal_s, algo_name, params):
        current_thread_obj = threading.current_thread()
        start_time = time.time()
        solution_path = None
        try:
            if not (hasattr(self, 'solve_thread') and self.solve_thread == current_thread_obj):
                print(f"CSP Solver thread for {algo_name} exiting early (no longer active)."); return
            
            solution_path = solver_func(initial_s, goal_s, **params)
            
            solve_duration = time.time() - start_time

            if hasattr(self, 'solve_thread') and self.solve_thread == current_thread_obj:
                 self.window.after(0, self._handle_csp_solve_result, solution_path, solve_duration, algo_name, initial_s)
            else:
                 print(f"CSP Solver for {algo_name} finished but not active. Result not handled.")

        except Exception as e:
            solve_duration = time.time() - start_time
            error_message = f"Error during {algo_name} execution: {e}"
            print(error_message)
            import traceback; traceback.print_exc()
            if hasattr(self, 'solve_thread') and self.solve_thread == current_thread_obj:
                self.window.after(0, lambda: self._log_message(error_message))
                self.window.after(0, lambda: self._log_message(f"Time taken: {solve_duration:.3f}s"))
        finally:
             if hasattr(self, 'solve_thread') and self.solve_thread == current_thread_obj:
                self.solve_thread = None


    def _handle_csp_solve_result(self, path, duration, algo_name, original_initial_state):
        self._log_message(f"{algo_name} finished in {duration:.3f} seconds.")
        if path and isinstance(path, list) and len(path) > 0:
            self._log_message(f"Path found with {len(path) -1} steps.")
            final_state_in_path = path[-1]
            if final_state_in_path == self.goal_board_config:
                self._log_message("Goal state reached!")
            else:
                self._log_message("Goal state NOT reached. Path shown is sequence explored.")
            
            self.animation_path = path
            self.animation_step = 0              
            if len(path) > 1:
                self._log_message("Animating path...")
                self.is_animating = True
                self.window.after(self.animation_delay_ms, self._animate_csp_step)
            else:                  
                self._update_csp_board_display(path[0])
                self._log_message("Path contains only the initial state.")

        else:
            self._log_message("No solution path returned or path is empty.")
            self._update_csp_board_display(original_initial_state)  
    def _animate_csp_step(self):
        if not self.is_animating or not self.animation_path or self.animation_step >= len(self.animation_path):
            self.is_animating = False
            if self.animation_path and self.animation_step >= len(self.animation_path):
                 self._log_message("Animation finished.")                   
                 self._update_csp_board_display(self.animation_path[-1])
            return

        current_board_in_animation = self.animation_path[self.animation_step]
        self._update_csp_board_display(current_board_in_animation)
        self.animation_step += 1
        self.window.after(self.animation_delay_ms, self._animate_csp_step)


    def _set_as_main_puzzle_action(self):
        self._stop_solver_thread_and_animation()          
        self.master_gui.initial_state_config = deepcopy(self.current_board_to_solve)
        self.master_gui.current_display_state = deepcopy(self.current_board_to_solve)
        self.master_gui.update_grid(self.master_gui.initial_labels, self.master_gui.current_display_state)
        self.master_gui._populate_entries_with_state(self.master_gui.initial_state_config)          
        self.master_gui.clear_solution_display()
        self.master_gui.update_status(f"Initial state set from CSP Visualizer.", "success")
        self.master_gui.result_status_text.set("Status: Idle")
        self.master_gui.result_time_text.set("Time: -")
        self.master_gui.update_result_label_color("info")
        messagebox.showinfo("State Set", "Current board from CSP Visualizer has been set as the main puzzle's initial state.", parent=self.window)


    def _reset_csp_board_action(self):
        self._stop_solver_thread_and_animation()
        self.current_board_to_solve = deepcopy(self.master_gui.initial_state_config)          
        self._update_csp_board_display(self.current_board_to_solve)
        self._log_message("CSP board reset to initial state of main puzzle.", clear_first=True)
    
    def _stop_solver_thread_and_animation(self):
        if self.is_animating:
            self.is_animating = False          
        current_solver_thread = self.solve_thread
        if current_solver_thread and current_solver_thread.is_alive():
            print("CSP Visualizer: Signaling solver thread to stop.")
            self.solve_thread = None                    
            self._log_message("Solver process interrupted.")


    def _on_close(self):
        self._stop_solver_thread_and_animation()
        print("CSP Visualizer window closed by user.")
        if self.window:
            try: self.window.destroy()
            except tk.TclError: pass
        self.master_gui.on_csp_visualizer_window_closed() 