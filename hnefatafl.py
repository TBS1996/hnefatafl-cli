import enum
# these numbers are just for initialization. the board matrix gets replaced with all the squares objects that
# contain the tile and the piece on it and its position.
# the numbers correspond to the enum values in the "Piece"-enum-object
init_board =  [
  [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0],
  [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 2, 2, 2, 0, 0, 0, 1],
  [1, 1, 0, 2, 2, 3, 2, 2, 0, 1, 1],
  [1, 0, 0, 0, 2, 2, 2, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
  [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0],
]

standard_7x7 = [
	[0, 0, 1, 1, 1, 0, 0],
	[0, 0, 0, 1, 0, 0, 0],
	[1, 0, 2, 2, 2, 0, 1],
	[1, 1, 2, 3, 2, 1, 1],
	[1, 0, 2, 2, 2, 0, 1],
	[0, 0, 0, 1, 0, 0, 0],
	[0, 0, 1, 1, 1, 0, 0]
]

class SquareType(enum.Enum):
	"""Unlike chess, the tiles actually have different meanings.
	norm is the normal one
	esc is for ecsape, meaning the corner tiles
	throne is where the king starts"""

	norm = 0
	esc = 1
	throne = 2


class Piece(enum.Enum):
	"""Each square can have one type of player, if theres no player then a 'none'-piece is associated with it """
	void = -1
	none = 0
	attacker = 1
	defender = 2
	king = 3

class GameState(enum.Enum):
	"""The game is either being played, or one of the sides won."""
	playing = 0
	attacker_won = 1
	defender_won = 2




class Square:
	"""This object creates all the squares on the board. The data it contains is which position it has, which
	piece is on it, and which kind of tile it is (normal, corner, throne), and which board it is connected to"""

	def __init__(self, board, sq, pc, pos):
		self.board = board
		self.piece = pc
		self.square = sq
		self.pos = pos
		row, col = self.pos
		self.neighbours = [(row-1, col), (row+1, col), (row, col-1), (row, col+1)]


	def collision_detected(self, dest_pos: tuple[int, int]):
		"""This method stops the player from jumping over another player when moving from one spot to another"""

		dest_pos = self.board.get_square(dest_pos).pos
		path     = Board.get_path(self.pos, dest_pos)

		for tile in path:
			if tile == self.pos: continue
			tile_piece = self.board.get_piece(tile)
			chess_not = self.board.matrix_to_chess_notation(tile)
			if tile_piece is not Piece.none:
				print(f"invalid move: theres a {tile_piece.name} blocking your path at {chess_not}!")
				return True
		return False

	def valid_origin_selection(self):
		"""When you select a piece to move, this makes sure its valid to do that."""

		free_path = False
		for neighbour in self.neighbours:
			if self.board.valid_pos(neighbour):
				neighbour = self.board.get_square(neighbour)
				if neighbour.piece is Piece.none:
					free_path = True
		if not free_path:
			print("This piece is stuck :(")
			return False

		match self.piece:
			case Piece.none:
				print("No piece selected")
				return False
			case Piece.attacker:
				if not self.board.attackers_turn:
					print("Its defenders turn now")
					return False
			case Piece.defender | Piece.king:
				if self.board.attackers_turn:
					print("Its attackers turn now")
					return False
		return True

	def valid_destination_selection(self, dest_square):
		row, col = self.pos
		dest_row, dest_col = dest_square.pos

		if self.piece is not Piece.king and dest_square.square is SquareType.esc:
			print("Only the king can go to the corner piece")
			return False
		elif not (dest_row is row or dest_col is col):
			print("You can only move in straight lines")
			return False
		elif dest_square.pos is self.pos:
			print("Choose another destination than your current one")
			return False
		elif dest_square.square is SquareType.throne and self.piece is not Piece.king:
			print("Only the king can visit the throne")
			return False
		elif self.collision_detected(dest_square.pos):
			return False
		else:
			return True




	def move(self, dest_square):
		"""" This method is for moving a piece from one spot to another
		if it passes all the conditions, itll set the destination square's piece equal to its own,
		and put its own piece to none. and also change who's turn it is"""

		# copies your piece to target position, then clears your own
		dest_square.piece = self.piece
		self.clear()

		#check if this move caused any deaths
		dest_square.check_neighbour_deaths()


		if dest_square.square is SquareType.esc and dest_square.piece is Piece.king:
			self.board.state = GameState.defender_won

		self.board.attackers_turn = not self.board.attackers_turn



	def check_neighbour_deaths(self):
		"""Checks to see if the death condition is true for any of its neighbours.
		since its possible to capture a neighbouring piece when you move your piece, this method
		will be invoked whenever you make a move."""

		neighbours = ["above", "right", "below", "left"]
		for neighbour in neighbours:
			neighbour = self.get_neighbour(neighbour)
			if not neighbour: continue
			if neighbour.piece is Piece.none: continue
			chess_not = self.board.matrix_to_chess_notation(neighbour.pos)
			if neighbour.check_death():
				match neighbour.piece:
					case Piece.attacker:
						print(f"The defenders killed an attacker standing at {chess_not}!")
					case Piece.defender:
						print(f"The attackers killed a defender standing at {chess_not}!")
					case Piece.king:
						self.board.state = GameState.attacker_won
				neighbour.clear()


	def check_death(self):
		"""The piece is captured when its surrounded on left and right side, OR over and under"""

		neighbours = ["above", "right", "below", "left"]
		for i in range(2):
			neighbour = self.get_neighbour(neighbours[i])
			opposite_neighbour = self.get_neighbour(neighbours[i + 2])
			if neighbour and opposite_neighbour:
				if self.check_scary_neighbour(neighbour):
					if self.check_scary_neighbour(opposite_neighbour):
						return True
		return False


	def get_neighbour(self, direction: str):
		row, col = self.pos
		match direction:
			case "above":
				pos = (row - 1, col)
			case "below":
				pos = (row + 1, col)
			case "right":
				pos = (row, col + 1)
			case "left":
				pos = (row, col - 1)
		if self.board.valid_pos(pos):
			return self.board.get_square(pos)
		else:
			return None

	def check_scary_neighbour(self, neighbour):
		"""Checks if this neighbour is out to get you. Making it its own method cause
		the three types became a bit cumbersome to deal with in the check_death function"""

		match self.piece:
			case Piece.attacker:
				opponent = Piece.defender
			case Piece.defender | Piece.king:
				opponent = Piece.attacker
			case Piece.none:
				return False

		if neighbour.piece == opponent:
			return True
		elif neighbour.square == SquareType.throne and neighbour.piece == Piece.none:
			return True
		elif neighbour.square == SquareType.esc:
			return True
		else:
			return False


	def clear(self):
		"""method invoked either when you move a piece, or when the piece is captured"""
		self.piece = Piece.none






class Board:
	"""the actual board. the main data here is all the invididual squares that contain the pieces and other info"""
	def __init__(self, board):
		self.board = board
		self.board_size = len(self.board)
		self.corner_pos = [(0, 0), (0, self.board_size - 1), (self.board_size - 1, 0), (self.board_size - 1, self.board_size - 1)]
		self.state = GameState.playing
		self.attackers_turn = True

		for row in board:
			assert len(row) == self.board_size, "The given board must be a square!"

		# replaces the numbers in the board matrix with actual square-objects.
		# the square objects need the square-type, the type of piece and the position
		for row_idx, row in enumerate(self.board): # I always spell index like idx in loops because of you now X)
			for col_idx, value in enumerate(row):
				pos = (row_idx, col_idx)
				piece = Piece(value) # value is the number in the matrix, here it creates a corresponding piece

				if pos in self.corner_pos:
					sq = SquareType.esc
				elif piece == Piece.king:
					sq = SquareType.throne
				else:
					sq = SquareType.norm
				self.board[row_idx][col_idx] = Square(self, sq, piece, pos)


	def print(self):
		print("   ", end="")
		for i in range(self.board_size):
			print(f" {chr(ord('a') + i)} ", end="") # prints the letters that represent the columns
		print()
		for row_idx, row in enumerate(self.board):
			num = str(self.board_size - row_idx)
			num = num.ljust(2)
			print(num, end=" ")
			for col_idx, tile in enumerate(row):
				if (row_idx, col_idx) in self.corner_pos:
					print(" ╳ ", end="")
					continue


				# here True/False means whether the block character should connect to this direction or not
				left  = tile.get_neighbour("left")
				right = tile.get_neighbour("right")
				under = tile.get_neighbour("below")
				over  = tile.get_neighbour("above")
				left =  True if left  and left.piece  == Piece.none else False
				right = True if right and right.piece == Piece.none else False
				over =  True if over  and over.piece  == Piece.none else False
				under = True if under and under.piece == Piece.none else False



				match tile.piece:
					case Piece.none:
						if tile.square == SquareType.throne:
							print(" 🪑 ", end="")
						elif     left and     right and     over and     under: print("═╬═", end="")
						elif     left and     right and     over and not under: print("═╩═", end="")
						elif     left and     right and not over and     under: print("═╦═", end="")
						elif     left and not right and     over and     under: print("═╣ ", end="")
						elif not left and     right and     over and     under: print(" ╠═", end="")
						elif not left and     right and     over and not under: print(" ╚═", end="")
						elif not left and     right and not over and     under: print(" ╔═", end="")
						elif not left and not right and     over and     under: print(" ║ ", end="")
						elif     left and not right and     over and not under: print("═╝ ", end="")
						elif     left and not right and not over and     under: print("═╗ ", end="")
						elif     left and not right and not over and not under: print("   ", end="")
						elif     left and     right and not over and not under: print("═══", end="")
						elif not left and     right and not over and not under: print("   ", end="")
						elif not left and not right and not over and     under: print(" ╥ ", end="")
						elif not left and not right and     over and not under: print(" ╨ ", end="")
						elif not left and not right and not over and not under: print("   ", end="")

					case Piece.attacker:
						print(" █ ", end="")
					case Piece.defender:
						print(" ░ ", end="")
					case Piece.king:
						print(" K ", end="")
			num = num.ljust(2)
			print(num, end=" ")
			print()

		print("   ", end="")
		for i in range(self.board_size):
			print(f" {chr(ord('a') + i)} ", end="")
		print()
		mystr = "wtf"
		return repr(mystr)


	def get_piece(self, pos: tuple[int, int]):
		"""
		Returns the piece on the given square. returns a none-piece if you gave an invalid position by design,
		useful when youre on the edge and it checks neighbours there.
		"""
		if self.valid_pos(pos):
			return self.get_square(pos).piece
		else:
			return Piece.void

	def get_square(self, pos: tuple[int, int]):
		"""Returns square object on the given coordinate. """
		row, col = pos
		return self.board[row][col]


	def valid_pos(self, pos: tuple[int, int]):
		"""Checks whether given position is within the board"""
		row, col = pos
		if  0 <= row < self.board_size and  0 <= col < self.board_size:
			return True
		return False

	@staticmethod
	def get_path(orig_pos: tuple[int, int], dest_pos: tuple[int, int]):
		"""Gets a path between from the origin position to the destination when they share either
		the same row or the same column"""

		orig_row, orig_col = orig_pos
		dest_row, dest_col = dest_pos

		diff_col = dest_col - orig_col
		col_step = 1 if diff_col > 0 else -1

		diff_row = dest_row - orig_row
		row_step = 1 if diff_row > 0 else -1

		path = []
		for i in range(0, diff_col + col_step, col_step):
			for j in range(0, diff_row + row_step, row_step):
				path.append((orig_row + j, orig_col + i))
		return path[1::]

	def matrix_to_chess_notation(self, pos: tuple[int, int]):
		row, col = pos
		row = str(self.board_size - row)
		col = chr(ord("a") + col)
		return col + row

	def chess_to_matrix_notation(self, pos: str):
		"""Converts the user-defined positions into matrix coordinates.... e.g. c5 -> (6, 3) (in 11x11)"""

		col = pos[0]
		row = int(pos[1::])

		col = ord(col) - ord("a")
		row = self.board_size - row
		return row, col


	def check_unique_move(self, pos):
		team = (Piece.attacker,) if self.attackers_turn else (Piece.defender, Piece.king)
		row, col = self.chess_to_matrix_notation(pos)
		contenders = 0

		if self.get_piece((row, col)) is not Piece.none:
			print("Choose an empty tile")
			return None

		for direction in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
			i, j = 0, 0
			while (check_piece := self.get_piece((row + i, col + j))) is Piece.none:
				i += direction[0]
				j += direction[1]
			if check_piece in team:
				contenders += 1
				cont_pos = (row + i, col + j)

		match contenders:
			case 0:
				print("None of your players can make this move")
			case 1:
				return self.matrix_to_chess_notation(cont_pos)
			case 2:
				print(f"Only one player should be able to make this move. But now {contenders} of them can.")
		return None




	def move(self):
		"""
		converts from algebraic notation to cartesian matrix coordinates,
		then calls on the move method on the origin square to the destination position
		"""


		prompt = "Attackers turn: " if self.attackers_turn else "Defenders turn: "
		valid_move = False
		while not valid_move:
			mymove = input(prompt).strip().split()

			if len(mymove) == 1:  # if user just wrote one coordinate, program will check if just one piece can move there
				mymove = mymove[0]
				if self.valid_chess_notation(mymove):
					destination = mymove
					if not (origin := self.check_unique_move(destination)):
						continue
				else:
					prompt = f"{mymove} not recognized as valid chess notation\nTry again: "
					continue
			elif len(mymove) == 2:
				origin, destination = mymove
			else:
				prompt = "Write origin and destination square in chess notation, separated by a space.\nTry again: "
				continue

			if not self.valid_chess_notation(origin) and not self.valid_chess_notation(destination):
				prompt = f"{origin} and {destination} not valid chess notation.\nTry again: "
				continue
			elif not self.valid_chess_notation(origin):
				prompt = f"{origin} not valid chess notation.\nTry again: "
				continue
			elif not self.valid_chess_notation(destination):
				prompt = f"{destination} not valid chess notation.\nTry again: "
				continue


			#converts chess notation to matrix notation and gets the square on that position
			origin_square = self.get_square(self.chess_to_matrix_notation(origin))
			destin_square = self.get_square(self.chess_to_matrix_notation(destination))

			if not origin_square.valid_origin_selection():
				prompt = "Try again: "
				continue
			if not origin_square.valid_destination_selection(destin_square):
				prompt = "Try again: "
				continue

			valid_move = True

		origin_square.move(destin_square)



	def valid_chess_notation(self, pos):
		"""Lets user choose coordinate. the form is like on chess, e.g. f7 or a3 or whatever."""
		col = pos[0]
		row = pos[1::]

		if  col.isalpha() \
			and row.isdigit() \
			and 0 <= int(row) <= self.board_size \
			and ord("a") <= ord(col) < ord("a") + self.board_size:
				return True
		return False



def main():

	myboard = Board(init_board)
	myboard.print()

	while True:
		myboard.move()
		myboard.print()

		if not myboard.state == GameState.playing:
			break

	if myboard.state == GameState.attacker_won:
		print("The King is dead.")
		print("The attackers have won!")
	else:
		print("The King managed to escape.")
		print("The defenders have won!")


if __name__ == "__main__":
	main()





