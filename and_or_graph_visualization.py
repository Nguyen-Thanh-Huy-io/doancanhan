import tkinter as tk
from tkinter import ttk, scrolledtext
from copy import deepcopy

class AndOrVisualizerWindow:
    def __init__(self, master_gui): 
        self.master_gui = master_gui
        self.algo = master_gui.algo 
        self.initial_state_config = master_gui.initial_state_config 
        self.goal_state_list = master_gui.goal_state_list     
        self.FONT_LABEL = master_gui.FONT_LABEL
        self.FONT_PATH = master_gui.FONT_PATH
        self.TILE_SIZE = master_gui.TILE_SIZE
        self.FONT_TILE = master_gui.FONT_TILE
        self.OR_VIZ_TILE_SIZE = master_gui.OR_VIZ_TILE_SIZE
        self.FONT_OR_VIZ_TILE = master_gui.FONT_OR_VIZ_TILE
        self.COLOR_FRAME_BG = master_gui.COLOR_FRAME_BG 
        self.COLOR_OR_VIZ_HIGHLIGHT = master_gui.COLOR_OR_VIZ_HIGHLIGHT
        self.COLOR_OR_VIZ_INVALID = master_gui.COLOR_OR_VIZ_INVALID
        self.COLOR_TILE = master_gui.COLOR_TILE
        self.COLOR_BLANK = master_gui.COLOR_BLANK
        self.COLOR_TEXT = master_gui.COLOR_TEXT


        self.window = tk.Toplevel(master_gui.master)         
        self.window.title("And-Or Search Visualizer")
        self.window.geometry("1150x850")          
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self.generator = None
        self.auto_running = False
        self.delay_var = tk.IntVar(value=1000)          
        self.current_path_display_var = tk.StringVar(value="Path: []")
        self.current_and_state_data = None          
        self.and_state_labels = None          
        self.or_state_gui_elements = []          
        self.log_text_widget = None  
        self._setup_ui()          
        self._clear_displays()  
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

    def _update_grid(self, grid_labels, state_data):
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
    
    def _setup_ui(self):
        main_viz_frame = ttk.Frame(self.window, padding="10"); main_viz_frame.pack(fill="both", expand=True)
        ctrl_frame = ttk.Frame(main_viz_frame); ctrl_frame.pack(side="top", fill="x", pady=5)

        self.start_button = ttk.Button(ctrl_frame, text="Start/Restart", command=self._start_visualization)
        self.start_button.pack(side="left", padx=5)
        self.next_button = ttk.Button(ctrl_frame, text="Next Step", command=self._next_step, state=tk.DISABLED)
        self.next_button.pack(side="left", padx=5)
        self.auto_button = ttk.Button(ctrl_frame, text="Run Automatically", command=self._run_auto, state=tk.DISABLED)
        self.auto_button.pack(side="left", padx=5)
        
        ttk.Label(ctrl_frame, text="Delay (ms):").pack(side="left", padx=(10,2))
        ttk.Scale(ctrl_frame, from_=100, to=2000, variable=self.delay_var, orient="horizontal", length=150).pack(side="left", padx=2)

        display_pane = ttk.PanedWindow(main_viz_frame, orient="horizontal"); display_pane.pack(fill="both", expand=True, pady=5)
        
        and_state_frame_outer = tk.LabelFrame(display_pane, text="Current AND State", padx=10, pady=10, font=self.FONT_LABEL, bg=self.COLOR_FRAME_BG)
        display_pane.add(and_state_frame_outer, weight=1)          
        ttk.Label(and_state_frame_outer, textvariable=self.current_path_display_var, font=self.FONT_LABEL, background=self.COLOR_FRAME_BG).pack(side="top", pady=2)
        and_state_grid_frame = tk.Frame(and_state_frame_outer, bg=self.COLOR_FRAME_BG); and_state_grid_frame.pack(pady=10, anchor="center")
        self.and_state_labels = self._create_grid_labels(and_state_grid_frame, self.TILE_SIZE, self.FONT_TILE)
        or_log_pane = ttk.PanedWindow(display_pane, orient="vertical") 
        display_pane.add(or_log_pane, weight=2)          
        or_states_frame_outer = tk.LabelFrame(or_log_pane, text="Possible OR Choices (Blank Moves: UP, DOWN, LEFT, RIGHT)", padx=10, pady=10, font=self.FONT_LABEL, bg=self.COLOR_FRAME_BG)
        or_log_pane.add(or_states_frame_outer, weight=2)          
        or_states_container = tk.Frame(or_states_frame_outer, bg=self.COLOR_FRAME_BG)
        or_states_container.pack(fill="both", expand=True, pady=5)

        or_row1_frame = tk.Frame(or_states_container, bg=self.COLOR_FRAME_BG)
        or_row1_frame.pack(side="top", fill="x", pady=2, anchor="center")
        or_row2_frame = tk.Frame(or_states_container, bg=self.COLOR_FRAME_BG)
        or_row2_frame.pack(side="top", fill="x", pady=2, anchor="center")
        
        self.or_state_gui_elements = []          
        or_parents = [or_row1_frame, or_row1_frame, or_row2_frame, or_row2_frame]
        
        for i in range(4): 
            f = tk.Frame(or_parents[i], bg=self.COLOR_FRAME_BG, bd=1, relief=tk.SOLID) 
            direction_label_text = self.algo.move_names.get(self.algo.moves_delta[i], f"Dir {i}")
            dir_label_widget = tk.Label(f, text=direction_label_text, font=("Helvetica", 10, "bold"), bg=self.COLOR_FRAME_BG)
            dir_label_widget.pack(side="top", pady=(0,2))
            grid_container = tk.Frame(f, bg=self.COLOR_FRAME_BG) 
            grid_container.pack(side="top")
            labels = self._create_grid_labels(grid_container, self.OR_VIZ_TILE_SIZE, self.FONT_OR_VIZ_TILE, is_or_viz=True) 
            status_var = tk.StringVar(value=f"") 
            status_label_widget = tk.Label(f, textvariable=status_var, font=("Helvetica", 9, "italic"), bg=self.COLOR_FRAME_BG, wraplength=150) 
            status_label_widget.pack(side="bottom", pady=2, fill="x")
            self.or_state_gui_elements.append({
                'frame': f, 'parent_row': or_parents[i], 'grid_labels': labels, 
                'status_var': status_var, 'direction_label': dir_label_widget, 
                'status_label': status_label_widget, 'visible': False
            })

        log_frame_outer = tk.LabelFrame(or_log_pane, text="Search Log", padx=10, pady=10, font=self.FONT_LABEL, bg=self.COLOR_FRAME_BG)
        or_log_pane.add(log_frame_outer, weight=1)          
        self.log_text_widget = scrolledtext.ScrolledText(log_frame_outer, height=10, width=70, font=self.FONT_PATH, wrap=tk.WORD, bg="#FEFEFE", fg="#101010")
        self.log_text_widget.pack(fill="both", expand=True)
        self.log_text_widget.insert(tk.END, "Click 'Start/Restart' to visualize And-Or search on current main puzzle.\n"); 
        self.log_text_widget.config(state=tk.DISABLED)


    def _log(self, message):
        if hasattr(self, 'log_text_widget') and self.log_text_widget and self.log_text_widget.winfo_exists():
            self.log_text_widget.config(state=tk.NORMAL)
            self.log_text_widget.insert(tk.END, str(message) + "\n")
            self.log_text_widget.see(tk.END)
            self.log_text_widget.config(state=tk.DISABLED)
        else:
            print(f"Log widget not available for: {message}")


    def _clear_displays(self):
        if self.and_state_labels:              self._update_grid(self.and_state_labels, [[0,0,0],[0,0,0],[0,0,0]])
        if hasattr(self, 'or_state_gui_elements'):
            for or_info in self.or_state_gui_elements:
                if or_info['frame'].winfo_exists(): 
                    if or_info['visible']: or_info['frame'].pack_forget(); or_info['visible'] = False
                    if or_info['grid_labels']: self._update_grid(or_info['grid_labels'], [[0,0,0],[0,0,0],[0,0,0]])
                    if or_info['status_var']: or_info['status_var'].set("")
        
        if hasattr(self, 'current_path_display_var') and self.current_path_display_var:              self.current_path_display_var.set("Path: []")
        self.current_and_state_data = None


    def _start_visualization(self):
        if hasattr(self, 'log_text_widget') and self.log_text_widget and self.log_text_widget.winfo_exists():
            self.log_text_widget.config(state=tk.NORMAL); self.log_text_widget.delete('1.0', tk.END); self.log_text_widget.config(state=tk.DISABLED)
        self._log("Starting/Restarting And-Or Search Visualization...")          
        self._clear_displays()  
        initial_s = deepcopy(self.master_gui.initial_state_config) 
        goal_s = deepcopy(self.master_gui.goal_state_list)
        if not self.algo.is_solvable(initial_s):
            self._log("Warning: Initial state is unsolvable against standard goal.");
        
        self.current_and_state_data = deepcopy(initial_s) 
        self.generator = self.algo.and_or_search_visual(initial_s, goal_s)
        self.auto_running = False
        if self.start_button: self.start_button.config(text="Restart")
        if self.next_button: self.next_button.config(state=tk.NORMAL)
        if self.auto_button: self.auto_button.config(state=tk.NORMAL, text="Run Automatically")
        self._next_step()

    def _update_path_display(self, path_coords_list):
        if not (hasattr(self, 'current_path_display_var') and self.current_path_display_var): return
        if not path_coords_list: self.current_path_display_var.set("Path: [Initial]"); return
        path_str = " -> ".join([str(coord) for coord in path_coords_list]) 
        self.current_path_display_var.set(f"Path (Moved Tiles): {len(path_coords_list)} moves -> {path_str}")

    def _next_step(self):
        if not self.generator: self._log("Gen not init. Click Start."); return
        try: yielded_item = next(self.generator, None)
        except Exception as e: self._log(f"ERR Search Step: {e}"); yielded_item = None
        if yielded_item is None:
            self._log("Search visualization complete or generator exhausted.")
            if self.next_button: self.next_button.config(state=tk.DISABLED)
            if self.auto_button: self.auto_button.config(state=tk.DISABLED, text="Run Automatically")
            self.auto_running = False; return

        viz_type, data, *rest = yielded_item
        current_path_disp = [] 
        if viz_type in ['AND_STATE', 'INFO', 'OR_OPTIONS', 'BACKTRACK_FROM_OR', 'NO_SOLUTION_OVERALL']: current_path_disp = rest[0] if rest else []
        elif viz_type == 'CHOSEN_OR': current_path_disp = rest[1] if len(rest) > 1 else []
        elif viz_type == 'GOAL_FOUND': current_path_disp = data
        self._update_path_display(current_path_disp)

        for or_info_gui in self.or_state_gui_elements: 
            if or_info_gui['frame'].winfo_exists(): 
                or_info_gui['frame'].config(relief=tk.SOLID, borderwidth=1, bg=self.COLOR_FRAME_BG)  

        if viz_type == 'AND_STATE':
            current_s, path_c = data, rest[0]
            self.current_and_state_data = deepcopy(current_s) 
            if self.and_state_labels: self._update_grid(self.and_state_labels, current_s)
            self._log(f"AND Node: Path Len {len(path_c)}.")
            for or_d_info in self.or_state_gui_elements: 
                if or_d_info['frame'].winfo_exists():
                    if or_d_info['visible']: or_d_info['frame'].pack_forget(); or_d_info['visible'] = False
        elif viz_type == 'INFO': self._log(f"INFO: {data}")
        
        elif viz_type == 'OR_OPTIONS':
            neighbors_list_from_generator, path_c = data, rest[0] 
            self._log(f"Evaluating OR Choices from current AND state:")

            if not self.current_and_state_data: self._log("Error: Missing current AND state data."); return
            current_and_for_or = self.current_and_state_data
            blank_pos_tuple = self.algo.find_blank(current_and_for_or)
            if blank_pos_tuple is None: self._log("Error: Blank not found in current AND state."); return
            blank_r, blank_c = blank_pos_tuple

            for slot_idx, (dr, dc) in enumerate(self.algo.moves_delta):
                or_gui = self.or_state_gui_elements[slot_idx]
                tile_to_move_r, tile_to_move_c = blank_r + dr, blank_c + dc
                if self.algo.is_valid(tile_to_move_r, tile_to_move_c):
                    resulting_or_state = deepcopy(current_and_for_or)
                    resulting_or_state[blank_r][blank_c], resulting_or_state[tile_to_move_r][tile_to_move_c] = \
                        resulting_or_state[tile_to_move_r][tile_to_move_c], resulting_or_state[blank_r][blank_c]
                    self._update_grid(or_gui['grid_labels'], resulting_or_state)
                    h_val_str = "h=?"
                    moved_tile_for_this_action = (tile_to_move_r, tile_to_move_c)
                    for gen_neighbor in neighbors_list_from_generator:
                        if gen_neighbor['move'] == moved_tile_for_this_action and \
                           self.algo.state_to_tuple(gen_neighbor['state']) == self.algo.state_to_tuple(resulting_or_state):
                            h_val = self.algo.manhattan_distance(gen_neighbor['state'], self.master_gui.goal_state_list)
                            h_val_str = f"h={h_val if h_val != float('inf') else 'Inf'}"
                            break
                    or_gui['status_var'].set(f"{h_val_str}")
                else:
                    empty_display_state = [[" ", " ", " "], ["-", "X", "-"], [" ", " ", " "]]
                    self._update_grid(or_gui['grid_labels'], empty_display_state)
                    for r_idx_inv in range(3): 
                        for c_idx_inv in range(3):
                            if or_gui['grid_labels'][r_idx_inv][c_idx_inv].winfo_exists():
                                or_gui['grid_labels'][r_idx_inv][c_idx_inv].config(bg=self.COLOR_OR_VIZ_INVALID, relief=tk.FLAT)
                    or_gui['status_var'].set("Invalid")
                if not or_gui['visible'] and or_gui['frame'].winfo_exists():
                    or_gui['frame'].pack(in_=or_gui['parent_row'], side="left", padx=10, pady=5, anchor="n", expand=True) 
                    or_gui['visible'] = True
            self._log(f"Algorithm's sorted choices has {len(neighbors_list_from_generator)} options.")

        elif viz_type == 'CHOSEN_OR':
            chosen_info, idx_in_sorted_list, path_c = data, rest[0], rest[1]
            self._log(f"Algorithm CHOSE to explore option (move by tile at {chosen_info['move']}).")
            current_and_for_chosen = self.current_and_state_data
            if current_and_for_chosen: 
                blank_r_chosen, blank_c_chosen = self.algo.find_blank(current_and_for_chosen)
                if blank_r_chosen is not None: 
                    dr_chosen = chosen_info['move'][0] - blank_r_chosen
                    dc_chosen = chosen_info['move'][1] - blank_c_chosen
                    chosen_slot_idx = -1
                    for i_slot, (md_dr, md_dc) in enumerate(self.algo.moves_delta):
                        if md_dr == dr_chosen and md_dc == dc_chosen:
                            chosen_slot_idx = i_slot; break
                    if chosen_slot_idx != -1 and chosen_slot_idx < len(self.or_state_gui_elements):
                        if self.or_state_gui_elements[chosen_slot_idx]['frame'].winfo_exists():
                             self.or_state_gui_elements[chosen_slot_idx]['frame'].config(bg=self.COLOR_OR_VIZ_HIGHLIGHT, relief=tk.RAISED, borderwidth=2)


        elif viz_type == 'BACKTRACK_FROM_OR': self._log(f"BACKTRACK from OR (Move by tile at: {data['move']}) failed.")
        elif viz_type == 'GOAL_FOUND':
            self._log(f"!!! GOAL FOUND !!! Path (Moved Tiles): {data} (Length: {len(data)})")
            if self.next_button: self.next_button.config(state=tk.DISABLED)
            if self.auto_button: self.auto_button.config(state=tk.DISABLED, text="Run Automatically")
            self.auto_running = False
            if self.and_state_labels: self._update_grid(self.and_state_labels, self.master_gui.goal_state_list)
        elif viz_type == 'NO_SOLUTION_OVERALL':
            self._log("--- NO SOLUTION FOUND after exploring all paths. ---")
            if self.next_button: self.next_button.config(state=tk.DISABLED)
            if self.auto_button: self.auto_button.config(state=tk.DISABLED, text="Run Automatically")
            self.auto_running = False

        if self.auto_running and yielded_item and viz_type not in ['GOAL_FOUND', 'NO_SOLUTION_OVERALL']:
            if hasattr(self.window, 'after') and self.window and self.window.winfo_exists(): 
                 self.window.after(self.delay_var.get(), self._next_step) 
            else: self.auto_running = False

    def _run_auto(self):
        if not self.generator: self._log("Click Start first."); return
        if self.auto_running:
            self.auto_running = False
            if self.auto_button: self.auto_button.config(text="Run Automatically")
            self._log("Automatic stepping paused.")
        else:
            self.auto_running = True
            if self.auto_button: self.auto_button.config(text="Pause Auto")
            self._log("Automatic stepping started..."); self._next_step()

    def _on_close(self):
        self.auto_running = False; self.generator = None
        self.master_gui.on_and_or_viz_window_closed()          
        if hasattr(self, 'window') and self.window:              
            try: self.window.destroy()
            except tk.TclError: pass
 