# belief_system_window.py
import tkinter as tk
from tkinter import ttk, scrolledtext,messagebox
from copy import deepcopy
import random # Cần cho việc tạo state
import threading # Cần cho việc chạy solver trong thread
import time # Cần cho việc đo thời gian và sleep


# import thuattoan as algo # Sẽ được truy cập qua self.master_gui.algo

class NiemTin:
    def __init__(self, master_gui, belief_type):
        self.master_gui = master_gui
        self.belief_type = belief_type # "Belief" or "PartialBelief"
        self.algo = master_gui.algo
        
        # Constants from master_gui
        self.FONT_LABEL = master_gui.FONT_LABEL
        self.COLOR_FRAME_BG = master_gui.COLOR_FRAME_BG
        self.BELIEF_TILE_SIZE = master_gui.BELIEF_TILE_SIZE
        self.FONT_BELIEF_TILE = master_gui.FONT_BELIEF_TILE
        # ... (Thêm các hằng số khác nếu cần)

        self.window = tk.Toplevel(master_gui.master)
        window_title = "Belief State Puzzle Solver" if belief_type == "Belief" else "Partial Belief State Solver"
        self.window.title(window_title)
        self.window.geometry("1150x750")
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self.belief_states = [] # Các trạng thái ban đầu được tạo
        self.goal_states = []   # Các trạng thái đích tương ứng (thường là cố định)
        self.display_grids_info = [] # Thông tin về các grid hiển thị puzzle
        self.solve_thread = None # Thread để chạy giải thuật

        self._setup_ui()

    def _create_grid_labels(self, parent_frame, tile_size, tile_font, is_or_viz=False):
        # Sao chép từ PuzzleGUI hoặc làm cho nó có thể tái sử dụng
        labels = [[None for _ in range(3)] for _ in range(3)]
        effective_tile_size = tile_size 
        label_width = max(3, int(effective_tile_size / 18))
        label_height = max(1, int(effective_tile_size / 35))
        border_w = 1 if is_or_viz else 2
        for r_idx in range(3):
            for c_idx in range(3):
                label = tk.Label(parent_frame, text="", font=tile_font,
                                 width=label_width, height=label_height,
                                 borderwidth=border_w, relief=tk.RAISED,
                                 bg=self.master_gui.COLOR_TILE, fg=self.master_gui.COLOR_TEXT)
                label.grid(row=r_idx, column=c_idx, padx=1, pady=1)
                labels[r_idx][c_idx] = label
        return labels

    def _update_grid(self, grid_labels, state_data):
        # Sao chép từ PuzzleGUI hoặc làm cho nó có thể tái sử dụng
        if not state_data or len(state_data) != 3: return
        for r_idx in range(3):
             if len(state_data[r_idx]) != 3: continue
             for c_idx in range(3):
                 if grid_labels[r_idx][c_idx] and grid_labels[r_idx][c_idx].winfo_exists():
                     try:
                         value = state_data[r_idx][c_idx]
                         if value == 0: 
                             grid_labels[r_idx][c_idx].config(text="", bg=self.master_gui.COLOR_BLANK, relief=tk.FLAT)
                         else:
                             grid_labels[r_idx][c_idx].config(text=str(value), bg=self.master_gui.COLOR_TILE, fg=self.master_gui.COLOR_TEXT, relief=tk.RAISED)
                     except tk.TclError: pass 

    def _setup_ui(self):
        main_frame = ttk.Frame(self.window, padding="10"); main_frame.pack(fill="both", expand=True)
        control_frame = ttk.Frame(main_frame); control_frame.pack(side="top", fill="x", pady=5)
        display_pane = ttk.PanedWindow(main_frame, orient="horizontal"); display_pane.pack(fill="both", expand=True, pady=10)

        ttk.Label(control_frame, text="Algorithm:").pack(side="left", padx=5)
        self.algo_var = tk.StringVar(value="BFS") # Biến cho combobox
        excluded = ["Niềm Tin", "Niềm Tin 1 Phần", "And-Or Visualizer"] 
        algos = [a for a in self.master_gui.get_available_algorithms() if a not in excluded]
        self.algo_combo = ttk.Combobox(control_frame, textvariable=self.algo_var, values=algos, state="readonly", width=15)
        self.algo_combo.pack(side="left", padx=5)

        ttk.Label(control_frame, text="Num States:").pack(side="left", padx=(10, 2))
        self.num_states_var = tk.StringVar(value="10") # Biến cho số lượng states
        ttk.Entry(control_frame, textvariable=self.num_states_var, width=5).pack(side="left", padx=2)

        canvas_frame = ttk.Frame(display_pane, width=600); display_pane.add(canvas_frame, weight=2)
        self.canvas = tk.Canvas(canvas_frame, borderwidth=0, background="#ffffff") 
        vbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vbar.set); vbar.pack(side="right", fill="y"); self.canvas.pack(side="left", fill="both", expand=True)
        
        # self.inner_frame là frame bên trong canvas để vẽ các puzzle lên
        self.inner_frame = ttk.Frame(self.canvas) 
        self.canvas.create_window((4,4), window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", lambda e, c=self.canvas: c.configure(scrollregion=c.bbox("all")))

        log_pane_frame = ttk.Frame(display_pane, width=500); display_pane.add(log_pane_frame, weight=1) 
        self.log_text_widget = scrolledtext.ScrolledText(log_pane_frame, height=30, width=60, font=("Courier",9), wrap=tk.WORD)
        self.log_text_widget.pack(fill="both", expand=True)
        self.log_text_widget.insert(tk.END, f"Generate states for {self.belief_type} mode.\n"); self.log_text_widget.config(state=tk.DISABLED)

        self.generate_button = ttk.Button(control_frame, text="Generate States", command=self._handle_generate_states)
        self.generate_button.pack(side="left", padx=5)
        
        self.run_button = ttk.Button(control_frame, text="Run Simulation", command=self._start_simulation)
        self.run_button.pack(side="left", padx=5)

        self.reset_button = ttk.Button(control_frame, text="Reset Display", command=self._reset_display)
        self.reset_button.pack(side="left", padx=5)

        self._reset_display_content() # Khởi tạo hiển thị

    def _generate_own_belief_states(self, num_states):
         self.belief_states = []; self.goal_states = []
         base_goal = deepcopy(self.master_gui.goal_state_list)
         attempts = 0; max_attempts = num_states * 20
         while len(self.belief_states) < num_states and attempts < max_attempts:
             attempts += 1; flat_state_gen = list(range(9)); random.shuffle(flat_state_gen)
             current_s = [flat_state_gen[i*3:(i+1)*3] for i in range(3)]
             if self.algo.is_solvable(current_s) and current_s != base_goal:
                 self.belief_states.append(current_s); self.goal_states.append(deepcopy(base_goal))
         if not self.belief_states and num_states > 0 :
             print(f"Warning: Could not generate random solvable states for {self.belief_type} mode.");
         print(f"Generated {len(self.belief_states)} full random belief state pairs for {self.belief_type}.")

    def _generate_own_partial_belief_states(self, num_states):
        self.belief_states = []; self.goal_states = []
        base_goal = deepcopy(self.master_gui.goal_state_list)
        remaining_pool = [0, 4, 5, 6, 7, 8]; attempts = 0; max_attempts = num_states * 20
        while len(self.belief_states) < num_states and attempts < max_attempts:
            attempts += 1; current_s = [[1,2,3],[0,0,0],[0,0,0]]
            shuffled_rem = random.sample(remaining_pool, len(remaining_pool))
            idx = 0
            for r_fill in range(1,3): 
                for c_fill in range(3):
                    current_s[r_fill][c_fill] = shuffled_rem[idx]; idx+=1
            if self.algo.is_solvable(current_s) and current_s != base_goal and current_s not in self.belief_states:
                self.belief_states.append(deepcopy(current_s)); self.goal_states.append(deepcopy(base_goal))
        if not self.belief_states and num_states > 0: print(f"Warning: Could not generate partial belief states for {self.belief_type}.");
        print(f"Generated {len(self.belief_states)} partial belief state pairs for {self.belief_type}.")

    def _handle_generate_states(self):
        try:
            num_to_gen = int(self.num_states_var.get())
            if not (1 <= num_to_gen <= 50): raise ValueError("Num states 1-50.")
        except ValueError as e:
            messagebox.showerror("Invalid Number", str(e), parent=self.window); return
        
        self._stop_simulation() # Dừng simulation cũ nếu có

        if self.log_text_widget.winfo_exists(): # Xóa log cũ
            self.log_text_widget.config(state=tk.NORMAL); self.log_text_widget.delete('1.0', tk.END)
            self.log_text_widget.insert(tk.END, f"Generating {num_to_gen} states for {self.belief_type}...\n")
            self.log_text_widget.see(tk.END); self.log_text_widget.config(state=tk.DISABLED)

        if self.belief_type == "Belief": self._generate_own_belief_states(num_to_gen)
        elif self.belief_type == "PartialBelief": self._generate_own_partial_belief_states(num_to_gen)
        
        self._draw_puzzles()
        if self.log_text_widget.winfo_exists():
            self.log_text_widget.config(state=tk.NORMAL)
            self.log_text_widget.insert(tk.END, f"Displayed {len(self.belief_states)} pairs. Select algo & run.\n")
            self.log_text_widget.see(tk.END); self.log_text_widget.config(state=tk.DISABLED)


    def _draw_puzzles(self):
        try:
            if not self.inner_frame.winfo_exists(): return
            for widget in self.inner_frame.winfo_children(): widget.destroy()
        except tk.TclError: return # Frame có thể đã bị hủy
        self.display_grids_info = [] 
        if not self.belief_states or not self.goal_states:
             try: ttk.Label(self.inner_frame, text="Gen states.").pack()
             except tk.TclError: pass; return
        
        cols=2; c_count=0; row_f=None
        for i, (bs, gs) in enumerate(zip(self.belief_states, self.goal_states)):
            try:
                if c_count % cols == 0: row_f = ttk.Frame(self.inner_frame); row_f.pack(fill="x", pady=5, anchor="nw")
                if row_f is None or not row_f.winfo_exists(): break
                pair_f = ttk.Frame(row_f, padding=5); pair_f.pack(side="left", padx=10, pady=5, anchor="n")
                prefix = f"{self.belief_type} " if self.belief_type else ""
                
                bf = tk.LabelFrame(pair_f, text=f"{prefix}Initial {i+1}", bg=self.COLOR_FRAME_BG, font=self.FONT_LABEL, padx=5, pady=5)
                bf.pack(side="top", pady=2)
                bf_inner_grid = tk.Frame(bf, bg=self.COLOR_FRAME_BG) 
                bf_inner_grid.pack()
                bl = self._create_grid_labels(bf_inner_grid, self.BELIEF_TILE_SIZE, self.FONT_BELIEF_TILE)
                self._update_grid(bl, bs)
                
                gf = tk.LabelFrame(pair_f, text=f"{prefix}Goal {i+1}", bg=self.COLOR_FRAME_BG, font=self.FONT_LABEL, padx=5, pady=5)
                gf.pack(side="top", pady=2)
                gf_inner_grid = tk.Frame(gf, bg=self.COLOR_FRAME_BG) 
                gf_inner_grid.pack()
                gl = self._create_grid_labels(gf_inner_grid, self.BELIEF_TILE_SIZE, self.FONT_BELIEF_TILE)
                self._update_grid(gl, gs)
                self.display_grids_info.append({'belief_labels': bl, 'goal_labels': gl, 'frame': pair_f}); c_count+=1
            except tk.TclError: print(f"TclError drawing belief puzzle {i+1}."); break
        if self.canvas.winfo_exists():
            self.canvas.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))


    def _start_simulation(self):
        self._stop_simulation(); algo_name = self.algo_var.get()
        if not self.belief_states:
             messagebox.showinfo("Gen States", "Please generate states first.", parent=self.window); return
        try:
            if not self.log_text_widget.winfo_exists(): return
            self.log_text_widget.config(state=tk.NORMAL); self.log_text_widget.delete('1.0', tk.END)
            self.log_text_widget.insert(tk.END, f"Starting {self.belief_type} Sim: {algo_name} ({len(self.belief_states)} states)\n---\n")
            self.log_text_widget.see(tk.END); self.log_text_widget.config(state=tk.DISABLED)
            if hasattr(self, 'run_button') and self.run_button.winfo_exists(): self.run_button.config(state=tk.DISABLED)
            if hasattr(self, 'reset_button') and self.reset_button.winfo_exists(): self.reset_button.config(state=tk.DISABLED)
        except tk.TclError: print("Error accessing belief log/buttons."); return

        algo_key = algo_name.lower().replace("*", "_star").replace(" ", "_").replace("-", "_")
        solver_func = getattr(self.algo, algo_key, None)
        if not solver_func: 
            messagebox.showerror("Algo Error", f"Func '{algo_key}' not found.", parent=self.window)
            if hasattr(self,'run_button') and self.run_button.winfo_exists(): self.run_button.config(state=tk.NORMAL)
            if hasattr(self,'reset_button') and self.reset_button.winfo_exists(): self.reset_button.config(state=tk.NORMAL)
            return
        
        bc = deepcopy(self.belief_states); gc = deepcopy(self.goal_states)
        self.solve_thread = threading.Thread(target=self._run_solver_thread_logic,
            args=(solver_func, bc, gc, algo_name), daemon=True)
        self.solve_thread.start()

    def _run_solver_thread_logic(self, solver, b_list, g_list, algo_n):
        tid = threading.current_thread(); num_b = len(b_list); solved_c=0; total_d=0.0
        for i in range(num_b):
            active_t = self.solve_thread # Check against self.solve_thread
            if active_t != tid: print(f"Belief thread {tid} ({self.belief_type}) interrupted."); return
            bs = b_list[i]; gs = g_list[i]; start_t=time.time(); sol_path=None; err_detail=None
            try: sol_path = solver(deepcopy(bs), deepcopy(gs))
            except Exception as e: err_detail = f"Error: {e}"
            dur = time.time() - start_t; total_d += dur
            res_send = err_detail if err_detail else sol_path
            if self.solve_thread == tid: # Check again before master.after
                self.master_gui.master.after(0, lambda idx=i+1, r=res_send, d=dur: self._update_log(idx,r,d))
            if isinstance(sol_path, list): solved_c+=1
            if num_b > 1: time.sleep(0.01) 
        if self.solve_thread == tid: # Final check
            self.master_gui.master.after(0, lambda nb=num_b,ts=solved_c,td=total_d: self._finalize_log(nb,ts,td))
            self.master_gui.master.after(10, self._reset_thread_var_and_buttons, tid)

    def _reset_thread_var_and_buttons(self, completed_tid):
         if self.solve_thread == completed_tid:
              self.solve_thread = None
              try: 
                   if hasattr(self, 'run_button') and self.run_button.winfo_exists(): self.run_button.config(state=tk.NORMAL)
                   if hasattr(self, 'reset_button') and self.reset_button.winfo_exists(): self.reset_button.config(state=tk.NORMAL)
              except tk.TclError: pass
              print(f"{self.belief_type} solver thread var reset & buttons re-enabled.")


    def _update_log(self, index, result, duration):
        try:
            if not self.log_text_widget or not self.log_text_widget.winfo_exists(): return
            self.log_text_widget.config(state=tk.NORMAL)
            self.log_text_widget.insert(tk.END, f"\n--- {self.belief_type} Instance {index} --- ({duration:.4f}s)\n")
            if isinstance(result, list): self.log_text_widget.insert(tk.END, f"  Status: Solved ({len(result)} steps)\n")
            elif isinstance(result, str) and "Error" in result: self.log_text_widget.insert(tk.END, f"  Status: Solver Error\n  Detail: {result}\n")
            elif result is None: self.log_text_widget.insert(tk.END, f"  Status: No Solution Found\n")
            else: self.log_text_widget.insert(tk.END, f"  Status: Unknown Result Type ({type(result)})\n")
            self.log_text_widget.see(tk.END); self.log_text_widget.config(state=tk.DISABLED)
        except tk.TclError: pass
        except Exception as e: print(f"Unexpected error updating belief log: {e}")

    def _finalize_log(self, total_num, solved_num, total_dur):
        try:
            if not self.log_text_widget or not self.log_text_widget.winfo_exists(): return
            self.log_text_widget.config(state=tk.NORMAL)
            self.log_text_widget.insert(tk.END, f"\n====================================\n{self.belief_type.upper()} SIMULATION COMPLETE\n")
            self.log_text_widget.insert(tk.END, f"  Total Simulated: {total_num}, Solved: {solved_num}, Time: {total_dur:.4f}s\n")
            self.log_text_widget.insert(tk.END, "====================================\n")
            self.log_text_widget.see(tk.END); self.log_text_widget.config(state=tk.DISABLED)
        except tk.TclError: pass
        except Exception as e: print(f"Unexpected error finalizing belief log: {e}")

    def _stop_simulation(self):
        current_b_thread = self.solve_thread
        if current_b_thread and current_b_thread.is_alive():
            print(f"Requested {self.belief_type} simulation stop."); self.solve_thread = None
            try:
                 if hasattr(self, 'run_button') and self.run_button.winfo_exists(): self.run_button.config(state=tk.NORMAL)
                 if hasattr(self, 'reset_button') and self.reset_button.winfo_exists(): self.reset_button.config(state=tk.NORMAL)
            except tk.TclError: pass
        elif not current_b_thread: 
            try:
                if hasattr(self, 'run_button') and self.run_button.winfo_exists(): self.run_button.config(state=tk.NORMAL)
                if hasattr(self, 'reset_button') and self.reset_button.winfo_exists(): self.reset_button.config(state=tk.NORMAL)
            except tk.TclError: pass

    def _reset_display_content(self): # Renamed from _reset_display
        if self.inner_frame and self.inner_frame.winfo_exists():
            for widget in self.inner_frame.winfo_children(): widget.destroy()
        if self.log_text_widget and self.log_text_widget.winfo_exists():
            self.log_text_widget.config(state=tk.NORMAL); self.log_text_widget.delete('1.0', tk.END)
            self.log_text_widget.insert(tk.END, f"{self.belief_type} display reset. Gen states.\n")
            self.log_text_widget.config(state=tk.DISABLED)
        self.belief_states = []; self.goal_states = []; self.display_grids_info = []
        if self.canvas and self.canvas.winfo_exists():
            self.canvas.update_idletasks(); self.canvas.configure(scrollregion=(0,0,1,1))
        print(f"{self.belief_type} display content reset.")
    
    def _reset_display(self): # This is called by the button
        self._stop_simulation()
        self._reset_display_content()
        # Re-enable buttons
        try: 
            if hasattr(self, 'run_button') and self.run_button.winfo_exists(): self.run_button.config(state=tk.NORMAL)
            if hasattr(self, 'reset_button') and self.reset_button.winfo_exists(): self.reset_button.config(state=tk.NORMAL)
            if hasattr(self, 'generate_button') and self.generate_button.winfo_exists(): self.generate_button.config(state=tk.NORMAL)
        except tk.TclError: pass


    def _on_close(self):
        print(f"{self.belief_type} window closed by user.")
        self._stop_simulation()
        if self.window: # Check if self.window exists
            try: self.window.destroy()
            except tk.TclError: pass
        # Inform master_gui to update its state
        self.master_gui.on_belief_type_window_closed(self.belief_type)