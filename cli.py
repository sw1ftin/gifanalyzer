import argparse
from pathlib import Path
from gif_parser import GifParser

def main():
    parser = argparse.ArgumentParser(description='Analyze GIF files and extract detailed information')
    parser.add_argument('file', type=Path, help='Path to GIF file to analyze')
    parser.add_argument('-o', '--output', type=Path, help='Save result to specified file')
    
    args = parser.parse_args()
    
    try:
        gif_parser = GifParser(args.file)
        info = gif_parser.parse_file()

        text = []
        text.append("=== GIF Information ===")
        for section, items in info['headers'].items():
            text.append(f"\n{section}:")
            for key, (value, description) in items.items():
                text.append(f"{key}: {value} ({description})")
        
        text.append("\n=== Frame Information ===")
        for i, frame in enumerate(info['frames'], 1):
            text.append(f"\nFrame {i}:")
            for key, value in frame.items():
                text.append(f"{key}: {value}")
        
        result = "\n".join(text)
        
        if args.output:
            args.output.write_text(result, encoding='utf-8')
            print(f"Result saved to {args.output}")
        else:
            print(result)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
