#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Test script to generate a chess move from an input image
Usage: python3 test.py [image_path]
"""

import sys
import os
from stockfish import Stockfish
import PIL.Image
from PIL import ImageDraw, ImageFont
import chessboard_finder
import tensorflow_chessbot as tcb
from helper_functions import shortenFEN

def square_to_coordinates(square, corners):
    """
    Convert chess square notation (like 'e4') to pixel coordinates
    
    Args:
        square (str): Chess square notation (e.g., 'e4')
        corners (list): Chessboard corners [x0, y0, x1, y1]
    
    Returns:
        tuple: (x, y) pixel coordinates of the square center
    """
    if len(square) != 2:
        return None
    
    file = ord(square[0]) - ord('a')  # a=0, b=1, ..., h=7
    rank = int(square[1]) - 1         # 1=0, 2=1, ..., 8=7
    
    # Calculate board dimensions
    board_width = corners[2] - corners[0]
    board_height = corners[3] - corners[1]
    
    # Calculate square size
    square_width = board_width / 8
    square_height = board_height / 8
    
    # Calculate center of the square
    x = corners[0] + (file + 0.5) * square_width
    y = corners[3] - (rank + 0.5) * square_height  # Flip Y coordinate
    
    return int(x), int(y)

def draw_move_on_image(img, move, corners, output_path="output.png"):
    """
    Draw the chess move on the image and save it
    
    Args:
        img (PIL.Image): Original image
        move (str): Chess move in UCI notation (e.g., 'e2e4')
        corners (list): Chessboard corners [x0, y0, x1, y1]
        output_path (str): Path to save the annotated image
    
    Returns:
        str: Path to the saved image
    """
    if not move or len(move) < 4:
        return None
    
    # Create a copy of the image for drawing
    img_copy = img.copy()
    draw = ImageDraw.Draw(img_copy)
    
    # Extract from and to squares
    from_square = move[:2]
    to_square = move[2:4]
    
    # Get coordinates
    from_coords = square_to_coordinates(from_square, corners)
    to_coords = square_to_coordinates(to_square, corners)
    
    if from_coords is None or to_coords is None:
        print(f"❌ Could not convert squares to coordinates: {from_square} -> {to_square}")
        return None
    
    # Draw arrow from source to destination
    arrow_color = (255, 0, 0)  # Red
    arrow_width = 8
    
    # Draw the main line
    draw.line([from_coords, to_coords], fill=arrow_color, width=arrow_width)
    
    # Draw arrowhead
    import math
    
    # Calculate arrow direction
    dx = to_coords[0] - from_coords[0]
    dy = to_coords[1] - from_coords[1]
    length = math.sqrt(dx*dx + dy*dy)
    
    if length > 0:
        # Normalize direction
        dx /= length
        dy /= length
        
        # Arrowhead parameters
        arrowhead_length = 20
        arrowhead_angle = 0.5  # radians
        
        # Calculate arrowhead points
        cos_angle = math.cos(arrowhead_angle)
        sin_angle = math.sin(arrowhead_angle)
        
        # Left arrowhead point
        left_x = to_coords[0] - arrowhead_length * (dx * cos_angle - dy * sin_angle)
        left_y = to_coords[1] - arrowhead_length * (dy * cos_angle + dx * sin_angle)
        
        # Right arrowhead point
        right_x = to_coords[0] - arrowhead_length * (dx * cos_angle + dy * sin_angle)
        right_y = to_coords[1] - arrowhead_length * (dy * cos_angle - dx * sin_angle)
        
        # Draw arrowhead
        draw.polygon([to_coords, (int(left_x), int(left_y)), (int(right_x), int(right_y))], 
                    fill=arrow_color, outline=arrow_color)
    
    # Draw circles at from and to positions
    circle_radius = 15
    circle_color = (255, 255, 0)  # Yellow
    outline_color = (255, 0, 0)   # Red
    
    # From circle (hollow)
    draw.ellipse([from_coords[0] - circle_radius, from_coords[1] - circle_radius,
                  from_coords[0] + circle_radius, from_coords[1] + circle_radius],
                 outline=outline_color, width=4)
    
    # To circle (filled)
    draw.ellipse([to_coords[0] - circle_radius, to_coords[1] - circle_radius,
                  to_coords[0] + circle_radius, to_coords[1] + circle_radius],
                 fill=circle_color, outline=outline_color, width=4)
    
    # Add text labels
    try:
        # Try to use a better font if available
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text_color = (255, 255, 255)  # White
    shadow_color = (0, 0, 0)      # Black
    
    # Draw move text with shadow effect
    move_text = f"{from_square.upper()} → {to_square.upper()}"
    text_x = corners[0] + 10
    text_y = corners[1] - 40
    
    # Shadow
    draw.text((text_x + 2, text_y + 2), move_text, fill=shadow_color, font=font)
    # Main text
    draw.text((text_x, text_y), move_text, fill=text_color, font=font)
    
    # Save the annotated image
    img_copy.save(output_path)
    print(f"🎨 Move visualization saved to: {output_path}")
    
    return output_path

def test_move_generation(image_path="input.png"):
    """
    Test function to generate a chess move from an input image
    
    Args:
        image_path (str): Path to the chessboard image
    
    Returns:
        tuple: (fen, best_move, corners, img, success)
    """
    print(f"Testing move generation with image: {image_path}")
    
    # Initialize Stockfish
    stockfish_path = os.path.join(os.path.dirname(__file__), "stockfish", "stockfish-macos-m1-apple-silicon")
    
    try:
        stockfish = Stockfish(path=stockfish_path)
        stockfish.reset_engine_parameters()
        stockfish.set_skill_level(10)
        stockfish.set_depth(6)
        print("✅ Stockfish initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Stockfish: {e}")
        return None, None, None, None, False
    
    # Load and process the image
    try:
        # Check if image exists
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return None, None, None, None, False
            
        # Load image
        img = PIL.Image.open(image_path)
        print(f"✅ Image loaded: {img.size[0]}x{img.size[1]} pixels")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
    except Exception as e:
        print(f"❌ Failed to load image: {e}")
        return None, None, None, None, False
    
    # Find chessboard in image
    try:
        print("🔍 Detecting chessboard...")
        tiles, corners = chessboard_finder.findGrayscaleTilesInImage(img)
        
        if tiles is None or corners is None:
            print("❌ Could not detect chessboard in image")
            return None, None, None, None, False
            
        print(f"✅ Chessboard detected at corners: {corners}")
        
    except Exception as e:
        print(f"❌ Chessboard detection failed: {e}")
        return None, None, None, None, False
    
    # Get FEN from chessboard using TensorFlow model
    try:
        print("🧠 Analyzing board position with TensorFlow...")
        
        # Initialize the TensorFlow model predictor
        predictor = tcb.ChessboardPredictor()
        fen, tile_certainties = predictor.getPrediction(tiles)
        predictor.close()
        
        if fen is None:
            print("❌ Could not analyze board position")
            return None, None, None, None, False
        
        # Process the FEN and add game state info
        short_fen = shortenFEN(fen)
        
        # Add game state info (active player, castling, en passant, etc.)
        # Default to white to move with full castling rights
        full_fen = f"{short_fen} w KQkq - 0 1"
        
        print(f"📋 Board FEN: {short_fen}")
        print(f"🔧 Full FEN: {full_fen}")
        print(f"🎯 Minimum tile certainty: {tile_certainties.min():.3f}")
        
    except Exception as e:
        print(f"❌ Board analysis failed: {e}")
        print("📝 Falling back to sample position for testing...")
        
        # Fallback to sample position if TensorFlow model fails
        sample_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR"
        fen = sample_fen
        full_fen = f"{fen} w KQkq - 0 1"
        short_fen = shortenFEN(fen)
        print(f"📋 Board FEN: {short_fen}")
    
    # Generate best move with Stockfish
    try:
        print("♟️  Calculating best move...")
        
        stockfish.set_fen_position(full_fen)
        
        # Check if position is valid
        if not stockfish.is_fen_valid(full_fen):
            print(f"❌ Invalid FEN position: {full_fen}")
            print("🔧 Trying to fix FEN by using default castling/en passant...")
            
            # Try with no castling rights and different active player
            simplified_fen = f"{short_fen} w - - 0 1"
            if stockfish.is_fen_valid(simplified_fen):
                full_fen = simplified_fen
                print(f"✅ Using simplified FEN: {full_fen}")
            else:
                # Try with black to move
                black_fen = f"{short_fen} b - - 0 1"
                if stockfish.is_fen_valid(black_fen):
                    full_fen = black_fen
                    print(f"✅ Using black-to-move FEN: {full_fen}")
                else:
                    print("❌ Could not create valid FEN from detected position")
                    return short_fen, None, corners, img, False
        
        best_move = stockfish.get_best_move()
        
        if best_move is None:
            print("❌ No valid moves found")
            return fen, None, corners, img, False
            
        # Get evaluation
        evaluation = stockfish.get_evaluation()
        
        print(f"✅ Best move: {best_move}")
        print(f"📊 Evaluation: {evaluation}")
        
        # Get top 3 moves for comparison
        top_moves = stockfish.get_top_moves(3)
        print("🏆 Top 3 moves:")
        for i, move_data in enumerate(top_moves, 1):
            print(f"   {i}. {move_data['Move']} (centipawn: {move_data['Centipawn']})")
        
        return short_fen, best_move, corners, img, True
        
    except Exception as e:
        print(f"❌ Move generation failed: {e}")
        return fen, None, corners, img, False

def main():
    """Main function to run the test"""
    print("=" * 50)
    print("Chess.com AI - Move Generation Test")
    print("=" * 50)
    
    # Get image path from command line or use default
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "input.png"
    
    # Test move generation
    fen, best_move, corners, img, success = test_move_generation(image_path)
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    print("=" * 50)
    
    if success:
        print(f"✅ SUCCESS!")
        print(f"📋 Position: {fen}")
        print(f"♟️  Best Move: {best_move}")
        print(f"\n💡 Move explanation:")
        print(f"   From: {best_move[:2]}")
        print(f"   To: {best_move[2:4]}")
        if len(best_move) > 4:
            print(f"   Promotion: {best_move[4:]}")
        
        # Draw move on image and save
        if corners is not None and img is not None:
            print(f"\n🎨 Creating move visualization...")
            output_path = draw_move_on_image(img, best_move, corners, f"{image_path.split('.')[0]}_out.png")
            if output_path:
                print(f"📁 Output saved to: {output_path}")
                
                # Try to open the image with default viewer
                try:
                    import subprocess
                    subprocess.run(["open", output_path], check=True)
                    print("🖼️  Image opened in default viewer")
                except:
                    print("💡 You can manually open the output image to see the move visualization")
    else:
        print("❌ FAILED - Could not generate move")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()