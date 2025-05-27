# Sicily - Interactive Chess Analysis Tool

Sicily is a real-time chess position analyzer that uses computer vision to detect chessboard positions from screenshots and provides AI-powered move suggestions using Stockfish.

## Features

- =� **Screenshot Analysis**: Take interactive screenshots of chess positions from any application
- >� **AI Position Recognition**: Uses TensorFlow to detect and analyze chess piece positions
- _ **Stockfish Integration**: Provides best move suggestions with configurable strength (ELO 800-2800)
- �� **Dual Perspective Support**: Supports both White and Black perspectives with automatic board orientation detection
- <� **Manual Override**: Force analysis for either side with simple keyboard commands
- =� **Detailed Analysis**: Shows evaluation scores, top moves, and mate detection
- = **Real-time Processing**: Continuous analysis loop for live game assistance

## Installation

### Prerequisites

- Python 3.11
- macOS (uses `screencapture` utility)
- Stockfish chess engine

### Setup

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Ensure Stockfish binary is available:
   - Download `stockfish-macos-m1-apple-silicon` binary 
   - For other systems, download Stockfish and update the path in `sicily.py`

## Usage

### Basic Usage

Run the main script:
```bash
python3 sicily.py
```

## How It Works

1. **Screenshot Capture**: Uses macOS `screencapture -i` for interactive area selection
2. **Board Detection**: Computer vision algorithms locate the chessboard boundaries
3. **Piece Recognition**: TensorFlow model identifies individual pieces and positions
4. **FEN Generation**: Creates standard chess notation from detected position
5. **Orientation Detection**: Automatically determines if board is flipped (Black on bottom)
6. **Engine Analysis**: Stockfish evaluates position and suggests best moves
7. **Perspective Correction**: For Black analysis, flips centipawn values for proper perspective

## Board Orientation Support

Sicily automatically detects board orientation:

- **Normal Orientation**: White pieces on bottom (standard view)
- **Flipped Orientation**: Black pieces on bottom (playing as Black)

When Black pieces are detected on the bottom:
- Board FEN is automatically flipped for correct analysis
- Active player is set to Black
- Move suggestions are optimized for Black

## Credits

- **Image Processing**: Based on computer vision techniques from [Chess.com-AI](https://github.com/MusadiqPasha/Chess.com-AI/tree/main) by MusadiqPasha
- **Chess Engine**: [Stockfish](https://stockfishchess.org/) - open source chess engine
- **Piece Recognition**: TensorFlow-based neural network for chess piece classification

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Disclaimer

This tool is for educational and analysis purposes. Please ensure compliance with the terms of service of any chess platform you use this with.