import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
from gif_parser import GifParser

class GifAnalyzer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GIF Analyzer")
        self.geometry("800x600")
        self.resizable(False, False)
        
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.top_frame = ctk.CTkFrame(self.main_frame)
        self.top_frame.pack(fill="x", padx=5, pady=5)
        
        self.select_button = ctk.CTkButton(
            self.top_frame,
            text="Select GIF File",
            command=self.open_file
        )
        self.select_button.pack(side="left", padx=5)
        
        self.zoom_frame = ctk.CTkFrame(self.top_frame)
        self.zoom_frame.pack(side="right", padx=5)
        
        self.zoom_out_btn = ctk.CTkButton(
            self.zoom_frame,
            text="-",
            width=30,
            command=self.zoom_out
        )
        self.zoom_out_btn.pack(side="left", padx=2)
        
        self.zoom_in_btn = ctk.CTkButton(
            self.zoom_frame,
            text="+",
            width=30,
            command=self.zoom_in
        )
        self.zoom_in_btn.pack(side="left", padx=2)
        
        self.reset_zoom_btn = ctk.CTkButton(
            self.zoom_frame,
            text="Reset",
            width=60,
            command=self.reset_zoom
        )
        self.reset_zoom_btn.pack(side="left", padx=2)
        
        self.playback_frame = ctk.CTkFrame(self.main_frame)
        self.playback_frame.pack(fill="x", padx=5, pady=5)
        
        self.controls_left = ctk.CTkFrame(self.playback_frame)
        self.controls_left.pack(side="left", padx=5)
        
        self.prev_frame_btn = ctk.CTkButton(
            self.controls_left,
            text="◁",
            width=30,
            command=self.prev_frame
        )
        self.prev_frame_btn.pack(side="left", padx=2)
        
        self.play_pause_btn = ctk.CTkButton(
            self.controls_left,
            text="PLAY",
            width=50,
            command=self.toggle_animation
        )
        self.play_pause_btn.pack(side="left", padx=2)
        
        self.next_frame_btn = ctk.CTkButton(
            self.controls_left,
            text="▷",
            width=30,
            command=self.next_frame
        )
        self.next_frame_btn.pack(side="left", padx=2)
        
        self.frame_label = ctk.CTkLabel(self.controls_left, text="Frame: 0/0")
        self.frame_label.pack(side="left", padx=5)
        
        self.controls_right = ctk.CTkFrame(self.playback_frame)
        self.controls_right.pack(side="right", padx=5)
        
        self.speed_label = ctk.CTkLabel(self.controls_right, text="Speed:")
        self.speed_label.pack(side="left", padx=2)
        
        self.speed_options = ["0.25x", "0.5x", "1x", "2x", "4x"]
        self.speed_var = ctk.StringVar(value="1x")
        self.speed_menu = ctk.CTkOptionMenu(
            self.controls_right,
            values=self.speed_options,
            variable=self.speed_var,
            width=70,
            command=self.change_speed
        )
        self.speed_menu.pack(side="left", padx=2)
        
        self.canvas = ctk.CTkCanvas(self.main_frame, width=400, height=300, bg='gray85', highlightthickness=0)
        self.canvas.pack(pady=10)
        
        self.info_text = ctk.CTkTextbox(self.main_frame, height=200)
        self.info_text.pack(fill="x", padx=5, pady=(5,0))
        
        self.copy_frame = ctk.CTkFrame(self.main_frame)
        self.copy_frame.pack(fill="x", padx=5, pady=(2,5))
        
        self.copy_button = ctk.CTkButton(
            self.copy_frame,
            text="Copy Result",
            width=100,
            command=self.copy_result
        )
        self.copy_button.pack(side="right", padx=5)
        
        self.save_button = ctk.CTkButton(
            self.copy_frame,
            text="Save As",
            width=100,
            command=self.save_result
        )
        self.save_button.pack(side="right", padx=5)
        
        self.current_image = None
        self.frames = []
        self.original_frames = []
        self.current_frame_index = 0
        self.total_frames = 0
        self.animation_speed = 100
        self.zoom_level = 1.0
        self.max_zoom = 32.0
        self.min_zoom = 0.1
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.image_x = 0
        self.image_y = 0
        self.animation_running = False
        self.current_file = None
        
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan)
        self.canvas.bind("<MouseWheel>", self.mouse_wheel)
        
    def update_frame_counter(self):
        self.frame_label.configure(text=f"Frame: {self.current_frame_index + 1}/{self.total_frames}")
        
    def prev_frame(self):
        if not self.frames:
            return
        self.stop_animation()
        self.current_frame_index = (self.current_frame_index - 1) % self.total_frames
        self.update_current_frame()
        
    def next_frame(self):
        if not self.frames:
            return
        self.stop_animation()
        self.current_frame_index = (self.current_frame_index + 1) % self.total_frames
        self.update_current_frame()
        
    def toggle_animation(self):
        if not self.frames:
            return
        if self.animation_running:
            self.stop_animation()
            self.play_pause_btn.configure(text="PLAY")
        else:
            self.start_animation()
            self.play_pause_btn.configure(text="STOP")
            
    def update_current_frame(self):
        if self.frames:
            self.canvas.delete("gif")
            self.canvas.create_image(200, 150, image=self.frames[self.current_frame_index], anchor="center", tags="gif")
            self.update_frame_counter()
    
    def mouse_wheel(self, event):
        if not self.frames:
            return
            
        if event.delta > 0:
            self.zoom_level = min(32.0, self.zoom_level * 1.1)
        else:
            self.zoom_level = max(0.1, self.zoom_level / 1.1)
            
        self.update_frames_zoom()
        
    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
    def pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        
    def create_checkerboard(self, width, height, cell_size=10):
        image = Image.new('RGB', (width, height), 'white')
        pixels = image.load()
        
        for i in range(0, width, cell_size):
            for j in range(0, height, cell_size):
                if (i // cell_size + j // cell_size) % 2:
                    for x in range(i, min(i + cell_size, width)):
                        for y in range(j, min(j + cell_size, height)):
                            pixels[x, y] = (192, 192, 192)
        return image
    
    def resize_image(self, image, zoom=1.0):
        width, height = image.size
        new_width = int(width * zoom)
        new_height = int(height * zoom)
        return image.resize((new_width, new_height), Image.Resampling.NEAREST if zoom > 1 else Image.Resampling.LANCZOS)
    
    def zoom_in(self):
        if self.zoom_level < self.max_zoom:
            self.zoom_level = min(self.max_zoom, self.zoom_level * 1.5)
            self.update_frames_zoom()
    
    def zoom_out(self):
        if self.zoom_level > self.min_zoom:
            self.zoom_level = max(self.min_zoom, self.zoom_level / 1.5)
            self.update_frames_zoom()
    
    def reset_zoom(self):
        if not self.frames:
            return
        self.zoom_level = 1.0
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.update_frames_zoom()
    
    def update_frames_zoom(self):
        self.frames.clear()
        for original in self.original_frames:
            resized = self.resize_image(original, self.zoom_level)
            self.frames.append(ImageTk.PhotoImage(resized))
        self.update_current_frame()
    
    def get_formatted_result(self):
        if not hasattr(self, 'gif_info'):
            return ""
            
        text = []
        
        # Add headers info
        text.append("=== GIF Information ===")
        for section, items in self.gif_info['headers'].items():
            text.append(f"\n{section}:")
            for key, (value, description) in items.items():
                text.append(f"{key}: {value} ({description})")
        
        # Add frame information
        text.append("\n=== Frame Information ===")
        for i, frame in enumerate(self.gif_info['frames'], 1):
            text.append(f"\nFrame {i}:")
            for key, value in frame.items():
                text.append(f"{key}: {value}")
                
        return "\n".join(text)
    
    def format_table(self, data):
        result = []
        for section, items in data.items():
            result.append(f"{section}:")
            for key, (value, description) in items.items():
                result.append(f"{key}: {value} ({description})")
        return "\n".join(result)
    
    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("GIF files", "*.gif")])
        if file_path:
            self.load_gif(file_path)
            
    def load_gif(self, file_path):
        try:
            self.frames = []
            self.original_frames = []
            self.current_frame_index = 0
            self.animation_running = False
            self.play_pause_btn.configure(text="PLAY")
            
            self.image = Image.open(file_path)
            self.current_file = file_path
            
            try:
                while True:
                    frame_copy = self.image.copy()
                    if frame_copy.mode == 'P':
                        frame_copy = frame_copy.convert('RGBA')
                    
                    checker = self.create_checkerboard(frame_copy.width, frame_copy.height)
                    
                    if frame_copy.mode == 'RGBA':
                        checker.paste(frame_copy, mask=frame_copy.split()[3])
                    else:
                        checker.paste(frame_copy)
                    
                    self.original_frames.append(checker)
                    self.frames.append(ImageTk.PhotoImage(checker))
                    self.image.seek(self.image.tell() + 1)
            except EOFError:
                pass
                
            self.total_frames = len(self.frames)
            self.update_frame_counter()
            
            if self.frames:
                self.update_current_frame()
                
            self.analyze_current_file()
                
        except Exception as e:
            print(f"Error loading GIF: {str(e)}")
            
    def analyze_current_file(self):
        if not hasattr(self, 'current_file') or not self.current_file:
            print("No file loaded to analyze")
            return
            
        try:
            parser = GifParser(self.current_file)
            self.gif_info = parser.parse_file()
            
            self.info_text.configure(state="normal")
            self.info_text.delete("1.0", "end")
            
            self.info_text.insert("end", "=== GIF Information ===\n")
            self.info_text.insert("end", self.format_table(self.gif_info['headers']))
            
            self.info_text.insert("end", "\n\n=== Frame Information ===")
            for i, frame in enumerate(self.gif_info['frames']):
                self.info_text.insert("end", f"\nFrame {i + 1}:")
                for key, value in frame.items():
                    self.info_text.insert("end", f"\n{key}: {value}")
                    
            self.info_text.configure(state="disabled")
            
        except Exception as e:
            print(f"Error analyzing GIF: {str(e)}")
    
    def stop_animation(self):
        self.animation_running = False
    
    def start_animation(self):
        self.animation_running = True
        self.play_pause_btn.configure(text="STOP")
        self.animate_gif()
    
    def animate_gif(self):
        if not self.animation_running or not self.frames:
            return
        
        self.current_frame_index = (self.current_frame_index + 1) % self.total_frames
        self.update_current_frame()
        self.after(self.animation_speed, self.animate_gif)
    
    def change_speed(self, value):
        speed_multiplier = {
            "0.25x": 4.0,
            "0.5x": 2.0,
            "1x": 1.0,
            "2x": 0.5,
            "4x": 0.25
        }
        self.animation_speed = int(100 * speed_multiplier[value])
    
    def copy_result(self):
        result = self.get_formatted_result()
        if result:
            self.clipboard_clear()
            self.clipboard_append(result)
            
    def save_result(self):
        if not hasattr(self, 'gif_info'):
            return
            
        # Get original file name without extension
        original_name = os.path.splitext(os.path.basename(self.current_file))[0] if hasattr(self, 'current_file') else "gif"
        default_name = f"{original_name}_analysis.txt"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=default_name
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.get_formatted_result())
            except Exception as e:
                print(f"Error saving file: {str(e)}")
    
    def run(self):
        self.mainloop()

if __name__ == "__main__":
    app = GifAnalyzer()
    app.run()
