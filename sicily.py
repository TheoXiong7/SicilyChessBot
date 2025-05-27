#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
sicily.py
"""

import os
from stockfish import Stockfish
import PIL.Image
import chessboard_finder
import tensorflow_chessbot as tcb
from helper_functions import shortenFEN
import subprocess
import tempfile

def get_stockfish_parameters():
    """
    Get Stockfish parameters from user at startup
    
    Returns:
        dict: Dictionary containing stockfish parameters
    """
    print("=" * 50)
    print("STOCKFISH CONFIGURATION")
    print("=" * 50)
    
    # Get skill level / ELO
    while True:
        try:
            print("\n🎯 Select stockfish strength:")
            print("   1. Beginner (ELO ~800)")
            print("   2. Casual (ELO ~1200)")
            print("   3. Intermediate (ELO ~1600)")
            print("   4. Advanced (ELO ~2000)")
            print("   5. Expert (ELO ~2400)")
            print("   6. Master (ELO ~2800)")
            print("   [Enter] Custom ELO")
            
            choice = input("Select option (1-6): ").strip()
            
            if choice == "1":
                skill_level = 0
                elo = 800
                break
            elif choice == "2":
                skill_level = 3
                elo = 1200
                break
            elif choice == "3":
                skill_level = 6
                elo = 1600
                break
            elif choice == "4":
                skill_level = 10
                elo = 2000
                break
            elif choice == "5":
                skill_level = 15
                elo = 2400
                break
            elif choice == "6":
                skill_level = 20
                elo = 2800
                break
            elif choice == "":
                elo = int(input("Enter custom ELO (800-3200): "))
                if 800 <= elo <= 3200:
                    # Approximate skill level mapping
                    skill_level = min(20, max(0, int((elo - 800) / 120)))
                    break
                else:
                    print("❌ ELO must be between 800 and 3200")
                    continue
            else:
                print("❌ Please select a valid option (1-7)")
                continue
        except ValueError:
            print("❌ Please enter a valid number")
            continue
    
    # Get depth
    while True:
        try:
            print(f"\n⚡ Search depth (higher = stronger but slower):")
            print("   Recommended: 6-12 for fast analysis, 15+ for tournament play")
            depth = int(input("Enter depth (1-20): "))
            if 1 <= depth <= 20:
                break
            else:
                print("❌ Depth must be between 1 and 20")
        except ValueError:
            print("❌ Please enter a valid number")
    
    params = {
        'skill_level': skill_level,
        'elo': elo,
        'depth': depth
    }
    
    print(f"\n✅ Configuration set:")
    print(f"   ELO: {elo} (Skill Level: {skill_level})")
    print(f"   Depth: {depth}")
    
    return params

def detect_board_orientation(fen):
    """
    Detect if board is oriented with white on bottom (normal) or black on bottom (flipped)
    
    Args:
        fen (str): Board position in FEN notation (piece placement only)
    
    Returns:
        tuple: (orientation, active_player) where orientation is 'normal' or 'flipped'
               and active_player is 'w' or 'b'
    """
    try:
        ranks = fen.split('/')
        bottom_rank = ranks[-1]  # 8th rank from white's perspective
        top_rank = ranks[0]      # 1st rank from white's perspective
        
        # Count pieces by color in bottom and top ranks
        bottom_white = sum(1 for c in bottom_rank if c.isupper() and c.isalpha())
        bottom_black = sum(1 for c in bottom_rank if c.islower() and c.isalpha())
        top_white = sum(1 for c in top_rank if c.isupper() and c.isalpha())
        top_black = sum(1 for c in top_rank if c.islower() and c.isalpha())
        
        # If more white pieces on bottom rank, likely normal orientation (white bottom)
        # If more black pieces on bottom rank, likely flipped orientation (black bottom)
        if bottom_white > bottom_black:
            return 'normal', 'w'  # White pieces on bottom = white to move
        elif bottom_black > bottom_white:
            return 'flipped', 'b'  # Black pieces on bottom = black to move
        else:
            # If unclear from back ranks, check for typical starting positions
            if 'r' in bottom_rank or 'k' in bottom_rank or 'q' in bottom_rank:
                return 'flipped', 'b'  # Black major pieces on bottom
            else:
                return 'normal', 'w'   # Default to normal orientation
                
    except:
        return 'normal', 'w'  # Default fallback

def flip_fen(fen):
    """
    Flip a FEN string to reverse board orientation
    
    Args:
        fen (str): Board position in FEN notation (piece placement only)
    
    Returns:
        str: Flipped FEN string
    """
    try:
        ranks = fen.split('/')
        # Reverse the order of ranks and flip each rank horizontally
        flipped_ranks = []
        for rank in reversed(ranks):
            # Reverse the rank string (flip horizontally)
            flipped_rank = rank[::-1]
            flipped_ranks.append(flipped_rank)
        return '/'.join(flipped_ranks)
    except:
        return fen

def take_screenshot():
    """
    Take a screenshot and save it to a temporary file
    
    Returns:
        str: Path to the screenshot file, or None if failed
    """
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Take screenshot using macOS screencapture
        result = subprocess.run(['screencapture', '-i', temp_path], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(temp_path):
            print(f"📸 Screenshot saved to: {temp_path}")
            return temp_path
        else:
            print("❌ Screenshot cancelled or failed")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return None
            
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return None

def init_stockfish(stockfish_params=None):
    """Initialize Stockfish engine with given parameters"""
    stockfish_path = os.path.join(os.path.dirname(__file__), "stockfish", "stockfish-macos-m1-apple-silicon")
    
    try:
        stockfish = Stockfish(path=stockfish_path)
        stockfish.reset_engine_parameters()
        
        # Apply user parameters if provided
        if stockfish_params:
            stockfish.set_skill_level(stockfish_params['skill_level'])
            stockfish.set_depth(stockfish_params['depth'])
            print(f"✅ Stockfish initialized with ELO {stockfish_params['elo']}, depth {stockfish_params['depth']}")
        else:
            # Default settings
            stockfish.set_skill_level(10)
            stockfish.set_depth(6)
            print("✅ Stockfish initialized with default settings")
        return stockfish
    except Exception as e:
        print(f"❌ Failed to initialize Stockfish: {e}")
        return None

def test_move_generation(image_path="input.png", stockfish_params=None, manual_side=None):
    """
    Test function to generate a chess move from an input image
    
    Args:
        image_path (str): Path to the chessboard image
        stockfish_params (dict): Stockfish configuration parameters
        manual_side (str): Manual override for side to move ('w' or 'b'), None for auto-detect
    
    Returns:
        tuple: (fen, best_move, success)
    """
    print(f"Testing move generation with image: {image_path}")
    
    # Initialize Stockfish
    stockfish = init_stockfish(stockfish_params)
    if stockfish is None:
        return None, None, False
    
    # Load and process the image
    try:
        # Check if image exists
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return None, None, False
            
        # Load image
        img = PIL.Image.open(image_path)
        print(f"✅ Image loaded: {img.size[0]}x{img.size[1]} pixels")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
    except Exception as e:
        print(f"❌ Failed to load image: {e}")
        return None, None, False
    
    # Find chessboard in image
    try:
        print("🔍 Detecting chessboard...")
        tiles, corners = chessboard_finder.findGrayscaleTilesInImage(img)
        
        if tiles is None or corners is None:
            print("❌ Could not detect chessboard in image")
            return None, None, False
            
        print(f"✅ Chessboard detected at corners: {corners}")
        
    except Exception as e:
        print(f"❌ Chessboard detection failed: {e}")
        return None, None, False
    
    # Get FEN from chessboard using TensorFlow model
    try:
        print("🧠 Analyzing board position with TensorFlow...")
        
        # Initialize the TensorFlow model predictor
        predictor = tcb.ChessboardPredictor()
        fen, tile_certainties = predictor.getPrediction(tiles)
        predictor.close()
        
        if fen is None:
            print("❌ Could not analyze board position")
            return None, None, False
        
        # Process the FEN and add game state info
        short_fen = shortenFEN(fen)
        
        # Detect board orientation and active player (or use manual override)
        if manual_side:
            active_player = manual_side
            # If manually selecting black, assume board needs flipping unless it already looks normal
            if manual_side == 'b':
                orientation = 'flipped'
                print("🔄 Manual black selection - flipping board orientation for analysis...")
                corrected_fen = flip_fen(short_fen)
                print(f"📋 Corrected FEN: {corrected_fen}")
                short_fen = corrected_fen
            else:
                orientation = 'normal'
            print(f"📋 Board FEN: {short_fen}")
            print(f"⚙️  Manual override: analyzing for {'White' if active_player == 'w' else 'Black'}")
        else:
            orientation, active_player = detect_board_orientation(short_fen)
            print(f"📋 Board FEN (raw): {short_fen}")
            print(f"🎯 Detected orientation: {orientation} (active player: {'White' if active_player == 'w' else 'Black'})")
            
            # If board is flipped (black on bottom), we need to flip the FEN
            if orientation == 'flipped':
                print("🔄 Flipping board orientation for analysis...")
                corrected_fen = flip_fen(short_fen)
                print(f"📋 Corrected FEN: {corrected_fen}")
                short_fen = corrected_fen
        
        # Add game state info (active player, castling, en passant, etc.)
        full_fen = f"{short_fen} {active_player} KQkq - 0 1"
        
        print(f"🔧 Full FEN: {full_fen}")
        print(f"🎯 Minimum tile certainty: {tile_certainties.min():.3f}")
        
    except Exception as e:
        print(f"❌ Board analysis failed: {e}")
        print("📝 Falling back to sample position for testing...")
        
        # Fallback to sample position if TensorFlow model fails
        sample_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR"
        fen = sample_fen
        short_fen = shortenFEN(fen)
        
        # Detect orientation for fallback position too
        orientation, active_player = detect_board_orientation(short_fen)
        full_fen = f"{short_fen} {active_player} KQkq - 0 1"
        
        print(f"📋 Board FEN (fallback): {short_fen}")
        print(f"🎯 Detected orientation: {orientation} (active player: {'White' if active_player == 'w' else 'Black'})")
    
    # Generate best move with Stockfish
    try:
        print("♟️  Calculating best move...")
        
        # Validate position BEFORE setting it to avoid corrupting engine state
        if not stockfish.is_fen_valid(full_fen):
            print(f"❌ Invalid FEN position: {full_fen}")
            print("🔧 Trying to fix FEN by using default castling/en passant...")
            
            # Try with no castling rights but keep the detected active player
            simplified_fen = f"{short_fen} {active_player} - - 0 1"
            if stockfish.is_fen_valid(simplified_fen):
                full_fen = simplified_fen
                print(f"✅ Using simplified FEN: {full_fen}")
            else:
                # Try with the opposite player
                opposite_player = 'b' if active_player == 'w' else 'w'
                opposite_fen = f"{short_fen} {opposite_player} - - 0 1"
                if stockfish.is_fen_valid(opposite_fen):
                    full_fen = opposite_fen
                    active_player = opposite_player
                    print(f"✅ Using opposite-player FEN: {full_fen}")
                else:
                    print("❌ Could not create valid FEN from detected position")
                    return short_fen, None, False
        
        # Now set the validated position
        stockfish.set_fen_position(full_fen)
        
        # Check if Stockfish is still running before getting moves
        try:
            # Test if engine is responsive
            if not stockfish.is_fen_valid("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
                print("❌ Stockfish engine is not responsive")
                return fen, None, False
        except:
            print("❌ Stockfish engine has crashed or is unresponsive")
            return fen, None, False
        
        # Get top moves first (this ensures consistent search)
        try:
            top_moves = stockfish.get_top_moves(3)
        except Exception as e:
            print(f"❌ Failed to get top moves: {e}")
            print("🔄 Attempting to restart Stockfish engine...")
            
            # Try to reinitialize Stockfish
            stockfish = init_stockfish(stockfish_params)
            if stockfish is None:
                print("❌ Could not restart Stockfish engine")
                return fen, None, False
            
            # Set the position again
            try:
                stockfish.set_fen_position(full_fen)
                top_moves = stockfish.get_top_moves(3)
                print("✅ Successfully restarted engine and got moves")
            except Exception as e2:
                print(f"❌ Engine restart failed: {e2}")
                print("🔄 Trying single best move as final fallback...")
                try:
                    best_move = stockfish.get_best_move()
                    if best_move:
                        print(f"✅ Best move (fallback): {best_move}")
                        return short_fen, best_move, True
                    else:
                        print("❌ No moves available")
                        return fen, None, False
                except Exception as e3:
                    print(f"❌ All fallback attempts failed: {e3}")
                    return fen, None, False
        
        if not top_moves or len(top_moves) == 0:
            print("❌ No valid moves found")
            return fen, None, False
        
        # Best move is always the first in top moves
        best_move = top_moves[0]['Move']
        
        # Get evaluation safely
        try:
            evaluation = stockfish.get_evaluation()
        except:
            evaluation = {"type": "unknown", "value": "N/A"}
        
        player_name = "White" if active_player == 'w' else "Black"
        print(f"✅ Best move for {player_name}: {best_move}")
        
        # Flip evaluation for black perspective
        display_evaluation = evaluation.copy() if isinstance(evaluation, dict) else evaluation
        if active_player == 'b' and isinstance(display_evaluation, dict):
            if display_evaluation.get('type') == 'cp' and display_evaluation.get('value') is not None:
                display_evaluation['value'] = -display_evaluation['value']
            elif display_evaluation.get('type') == 'mate' and display_evaluation.get('value') is not None:
                display_evaluation['value'] = -display_evaluation['value']
        
        print(f"📊 Evaluation: {display_evaluation}")
        
        # Display all top moves with flipped centipawn for black
        print(f"🏆 Top moves for {player_name}:")
        for i, move_data in enumerate(top_moves, 1):
            centipawn = move_data['Centipawn']
            if active_player == 'b' and centipawn is not None:
                centipawn = -centipawn
            print(f"   {i}. {move_data['Move']} (centipawn: {centipawn})")
        
        return short_fen, best_move, True
        
    except Exception as e:
        print(f"❌ Move generation failed: {e}")
        return fen, None, False

def main():
    """Main function with interactive screenshot analysis"""
    print("=" * 50)
    print("SICILY - Interactive Chess Analysis")
    print("=" * 50)
    
    # Get Stockfish parameters from user
    stockfish_params = get_stockfish_parameters()
    
    print("\n" + "=" * 50)
    print("INTERACTIVE MODE")
    print("=" * 50)
    print("📸 Press [ENTER] to take screenshot and auto-detect side")
    print("⚪ Press [W] then [ENTER] to analyze for White")
    print("⚫ Press [B] then [ENTER] to analyze for Black")
    print("🛑 Press [Q] then [ENTER] to quit")
    print("=" * 50)
    
    analysis_count = 0
    
    while True:
        try:
            # Get user input
            user_input = input("\nReady> ").strip().lower()
            
            if user_input == 'q':
                print("👋 Goodbye!")
                break
            elif user_input in ['', 'w', 'b']:
                # Take screenshot and analyze
                analysis_count += 1
                print(f"\n🔍 Analysis #{analysis_count}")
                print("-" * 30)
                
                # Take screenshot
                screenshot_path = take_screenshot()
                if screenshot_path is None:
                    print("⏭️  Skipping analysis - no screenshot taken")
                    continue
                
                # Determine manual override for side selection
                manual_side = None
                if user_input == 'w':
                    manual_side = 'w'
                    print("⚪ Manual override: Analyzing for White")
                elif user_input == 'b':
                    manual_side = 'b'
                    print("⚫ Manual override: Analyzing for Black")
                
                # Analyze the screenshot
                fen, best_move, success = test_move_generation(screenshot_path, stockfish_params, manual_side)
                
                print("\n" + "-" * 30)
                print("RESULTS:")
                print("-" * 30)
                
                if success:
                    print(f"✅ SUCCESS!")
                    print(f"📋 Position: {fen}")
                    print(f"♟️  Best Move: {best_move}")
                    print(f"💡 Move: {best_move[:2]} → {best_move[2:4]}")
                    if len(best_move) > 4:
                        print(f"🔄 Promotion: {best_move[4:]}")
                else:
                    print("❌ FAILED - Could not analyze position")
                
                # Clean up screenshot file
                try:
                    os.unlink(screenshot_path)
                except:
                    pass
                
                print("-" * 30)
            else:
                print("❓ Unknown command. Press [ENTER], [W], [B], or [Q].")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Continuing...")

if __name__ == "__main__":
    main()