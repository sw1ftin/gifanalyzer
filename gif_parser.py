import struct
from typing import BinaryIO
from pathlib import Path

class GifParser:
    # GIF Block Types
    IMAGE_SEPARATOR: bytes = b'\x2C'
    EXTENSION_INTRODUCER: bytes = b'\x21'
    TRAILER: bytes = b'\x3B'
    
    # GIF Extension Labels
    GRAPHICS_CONTROL_LABEL: bytes = b'\xF9'
    APPLICATION_LABEL: bytes = b'\xFF'
    COMMENT_LABEL: bytes = b'\xFE'
    
    def __init__(self, file_path: Path):
        self._file_path: Path = file_path
        self._width: int = 0
        self._height: int = 0
        self._global_color_table: list[tuple[int, int, int]] = []
        self._frames_info: list[dict[str, str | tuple[int, int] | bool | int | None]] = []
        self._headers_info: dict[str, dict[str, tuple[str | int | bool, str]]] = {}
        self._frame_count: int = 0
        self._file_size: int = 0
        self._total_duration: int = 0
        self._global_color_table_flag: bool = False
        self._global_color_table_size: int = 0
        
    def parse_file(self) -> dict[str, dict | list | tuple | int]:
        if not self._file_path.exists():
            raise FileNotFoundError(f"File {self._file_path} not found")
            
        self._file_size = self._file_path.stat().st_size
        
        with self._file_path.open('rb') as f:
            self._parse_header(f)
            self._parse_logical_screen_descriptor(f)
            self._parse_global_color_table(f)
            self._parse_frames(f)
            
        return self.get_info()
    
    def _parse_header(self, f: BinaryIO) -> None:
        header = f.read(6)
        signature = header[:3].decode('ascii')
        version = header[3:6].decode('ascii')
        
        self._headers_info['Header'] = {
            'Signature': (signature, 'GIF signature'),
            'Version': (version, 'GIF version')
        }
    
    def _parse_logical_screen_descriptor(self, f: BinaryIO) -> None:
        self._width, self._height = struct.unpack("<HH", f.read(4))
        packed = struct.unpack("<B", f.read(1))[0]
        background_color = struct.unpack("<B", f.read(1))[0]
        aspect_ratio = struct.unpack("<B", f.read(1))[0]
        
        global_color_table_flag = bool(packed & 0b10000000)
        color_resolution = ((packed & 0b01110000) >> 4) + 1
        sort_flag = bool(packed & 0b00001000)
        global_color_table_size = 2 << (packed & 0b00000111)
        
        self._headers_info['Logical Screen Descriptor'] = {
            'Canvas Size': (f"{self._width}x{self._height}", 'Image dimensions'),
            'Global Color Table': (global_color_table_flag, 'Whether global color table exists'),
            'Color Resolution': (color_resolution, 'Bits per primary color'),
            'Sort Flag': (sort_flag, 'Whether colors are sorted'),
            'Color Table Size': (global_color_table_size, 'Number of entries in global color table'),
            'Background Color': (background_color, 'Background color index'),
            'Aspect Ratio': (aspect_ratio, 'Pixel aspect ratio')
        }
        
        self._global_color_table_flag = global_color_table_flag
        self._global_color_table_size = global_color_table_size
    
    def _parse_global_color_table(self, f: BinaryIO) -> None:
        if self._global_color_table_flag:
            table_size = self._global_color_table_size * 3
            color_table = f.read(table_size)
            
            for i in range(0, table_size, 3):
                r, g, b = color_table[i:i+3]
                self._global_color_table.append((r, g, b))
    
    def _parse_frames(self, f: BinaryIO) -> None:
        current_frame_data = None
        
        while True:
            try:
                block_type = f.read(1)
                if not block_type:
                    break
                    
                if block_type == self.IMAGE_SEPARATOR:
                    current_frame_data = self._parse_image_descriptor(f)
                    if current_frame_data:
                        self._frames_info.append(current_frame_data)
                        self._frame_count += 1
                        
                elif block_type == self.EXTENSION_INTRODUCER:
                    extension_type = f.read(1)
                    if extension_type == self.GRAPHICS_CONTROL_LABEL:
                        if current_frame_data is None:
                            current_frame_data = {}
                        self._parse_graphics_control_extension(f, current_frame_data)
                    elif extension_type == self.APPLICATION_LABEL:
                        self._parse_application_extension(f)
                    elif extension_type == self.COMMENT_LABEL:
                        self._parse_comment_extension(f)
                    self._skip_data_blocks(f)
                elif block_type == self.TRAILER:
                    break
            except Exception as e:
                print(f"Error parsing frame: {str(e)}")
                break
    
    def _parse_image_descriptor(self, f: BinaryIO) -> dict[str, tuple[int, int] | str | bool | int]:
        left, top, width, height = struct.unpack("<HHHH", f.read(8))
        packed = struct.unpack("<B", f.read(1))[0]
        
        local_color_table_flag = bool(packed & 0b10000000)
        interlace_flag = bool(packed & 0b01000000)
        sort_flag = bool(packed & 0b00100000)
        local_color_table_size = 2 << (packed & 0b00000111)
        
        frame_info = {
            'Position': (left, top),
            'Size': f"{width}x{height}",
            'Local Color Table': local_color_table_flag,
            'Interlaced': interlace_flag,
            'Sort Flag': sort_flag,
            'Color Table Size': local_color_table_size
        }
        
        if local_color_table_flag:
            f.seek(3 * local_color_table_size, 1)
            
        f.read(1)
        self._skip_data_blocks(f)
        return frame_info
    
    def _parse_graphics_control_extension(self, f: BinaryIO, frame_info: dict[str, str | int | bool | None]) -> None:
        f.read(1)
        packed = struct.unpack("<B", f.read(1))[0]
        delay_time = struct.unpack("<H", f.read(2))[0]
        transparent_color_index = struct.unpack("<B", f.read(1))[0]
        
        disposal_method = (packed & 0b00011100) >> 2
        user_input_flag = bool(packed & 0b00000010)
        transparency_flag = bool(packed & 0b00000001)
        
        disposal_methods = [
            "No disposal specified",
            "Do not dispose",
            "Restore to background",
            "Restore to previous"
        ]
        
        delay_ms = delay_time * 10
        self._total_duration += delay_ms
        
        frame_info.update({
            'Delay': f"{delay_ms}ms",
            'Disposal Method': disposal_methods[disposal_method] if disposal_method < len(disposal_methods) else f"Unknown ({disposal_method})",
            'User Input': user_input_flag,
            'Transparency': transparency_flag,
            'Transparent Color': transparent_color_index if transparency_flag else None
        })
    
    def _parse_application_extension(self, f: BinaryIO) -> None:
        block_size = struct.unpack("<B", f.read(1))[0]
        app_data = f.read(block_size)
        if app_data.startswith(b'NETSCAPE2.0'):
            self._parse_netscape_extension(f)
        else:
            self._skip_data_blocks(f)
    
    def _parse_netscape_extension(self, f: BinaryIO) -> None:
        while True:
            block_size = struct.unpack("<B", f.read(1))[0]
            if block_size == 0:
                break
            if block_size == 3:
                f.read(1)
                iterations = struct.unpack("<H", f.read(2))[0]
                self._headers_info.setdefault('Metadata', {})['Loop Count'] = (iterations, 'Number of animation iterations (0 = infinite)')
            else:
                f.read(block_size)
    
    def _parse_comment_extension(self, f: BinaryIO) -> None:
        comment = []
        while True:
            block_size = struct.unpack("<B", f.read(1))[0]
            if block_size == 0:
                break
            comment.append(f.read(block_size).decode('ascii', errors='ignore'))
        
        if comment:
            self._headers_info.setdefault('Metadata', {})['Comment'] = (''.join(comment), 'GIF comment data')
    
    def _skip_data_blocks(self, f: BinaryIO) -> None:
        while True:
            block_size = f.read(1)
            if not block_size or block_size == b'\x00':
                break
            f.seek(struct.unpack("<B", block_size)[0], 1)
    
    def _format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} GB"
    
    def get_info(self) -> dict[str, dict | list | tuple | int]:
        summary = {
            'Summary': {
                'Resolution': (f"{self._width}x{self._height}", 'Image dimensions'),
                'Frame Count': (self._frame_count, 'Total number of frames'),
                'File Size': (self._format_size(self._file_size), 'Size on disk'),
                'Duration': (f"{self._total_duration}ms", 'Total animation duration'),
                'Frame Rate': (f"{1000 * self._frame_count / self._total_duration:.1f} FPS" if self._total_duration > 0 else "N/A", 'Average frame rate')
            }
        }
        
        return {
            'headers': {**summary, **self._headers_info},
            'frames': self._frames_info,
            'dimensions': (self._width, self._height),
            'frame_count': self._frame_count
        }
