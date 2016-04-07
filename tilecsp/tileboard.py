import functools

from csp.cspbase import *


class TileBoard(CSP):
    """
    Attributes:

        tiles:          list of Tiles, (initial domain for each variable in the
                        board)
        dimensions:     tuple of (int, int)
        vars:           list of Variables, n x n sized array (n = dimensions)


        (Optional)
        border_goals:   list of Variables
                        each Variable corresponds to some position on the border
                        of the board
                        e.g. goal on border : house, for a puzzle game where
                        there exists one tile whose edge contains a path that
                        leads to the house
                        i.e. the tile's edge should align with the goal
    """

    def __init__(self, name, tiles, terminal_points, dim=3):
        self.name = name
        self.tiles = tiles
        self.dimensions = dim
        variable_grid = TileBoard.create_board(self.dimensions, self.tiles)
        CSP.__init__(self, name, variable_grid)
        self._add_all_diff_constraint()
        self._add_adjacency_constraints(variable_grid)
        # self._add_terminal_point_constraints(terminal_points)

    def _add_adjacency_constraints(self, var_grid):
        # TODO: write constraint function(s)
        # TODO: replace "None" arg below with correct constraint function ref
        constraints = (Constraint("Pair {}".format(pair), pair, None)
                       for pair in TileBoard.get_adjacent_pairs(var_grid))
        for c in constraints:
            self.add_constraint(c)

    def _add_all_diff_constraint(self):
        # Inner function
        def all_diff(var_map):
            """
            :param var_map: Dictionary of variables mapped to assigned values
            :type var_map: dict[Variable, Tile]
            :return: True iff all tiles have unique IDs
            :rtype: bool
            """
            seen = set()
            # Uses early exit
            return not any(
                t_id in seen or seen.add(t_id)
                for t_id in map(lambda tile: tile.id, var_map.values())
            )
        self.add_constraint(
            Constraint("All-diff", self.get_all_vars(), all_diff))

    def _add_terminal_point_constraints(self, terminal_points):
        #TODO: write constraint function for perimeters
        # TODO: replace "None" arg below with correct constraint function ref

        self.add_constraint(
            Constraint('Terminal points', None)
        )

    def set_tile_position(self, tile):
        pass

    def get_tile_position(self, tile):
        pass

    def get_total_num_tiles(self):
        return len(self.tiles)

    def get_num_tiles_left(self):
        pass

    @staticmethod
    def create_board(dim, tiles):
        """
        :param dim: dimensions of board
        :type dim: int
        :param tiles:  list of Tiles (initial domain for each variable in
            board)
        :type tiles: list[Tile]

        :return: n x n matrix, each element is a Variable with initial domain
            being the tiles array
        :rtype: list[list[Variable]]
        """
        tiles = set(tiles)
        return [Variable('V' + str((i, j)), tiles) for i in range(dim) for j in
                range(dim)]

    @staticmethod
    def get_adjacent_pairs(grid):
        # top-left to bottom-right BFS adjacent-pair-finding algorithm
        pairs = set()
        q = [(0, 0)]  # list of (x, y) tuples
        max_y, max_x = len(grid), len(grid[0])
        while q:
            x, y = q.pop(0)
            current_cell = grid[y][x]
            # Get successor pairs (0, 1, or 2)
            # TODO verify
            adjacent = {{current_cell, s} for s in TileBoard.get_grid_successors(x, y, max_x, max_y)}
            q.extend((pair for pair in adjacent if pair not in pairs))
            pairs.update(adjacent)
        return pairs

    @staticmethod
    def get_grid_successors(x, y, max_x, max_y):
        s = [(x + 1, y) if x < max_x else None,
             (x, y + 1) if y < max_y else None]
        return s


class Tile:
    """
    Class representing a game tile (tile_board variable domain value)
    """
    # Edge constants
    N, E, S, W = "n", "e", "s", "w"
    EDGES = (N, E, S, W)
    # Generic configurations
    CONFIGURATIONS = {1: set()}
    ORIENTATIONS = CONFIGURATIONS.keys()
    PATHS = None

    def __init__(self, tile_id, edges=set(), paths=None):
        self.id = tile_id
        self.edges_with_roads = edges
        # Default to paths between all edges unless otherwise specified
        self.paths = paths if paths is not None else \
            set(itertools.combinations(edges, 2))

    def get_edges(self):
        """
        :return: Set containing all road-edges on this tile
        :rtype: set[str]
        """
        return set(self.edges_with_roads)

    def has_edge(self, e):
        """
        :param e: Edge to check on this tile
        :return: True iff this tile has a road on edge e.
        :rtype: bool
        """
        return e in self.edges_with_roads

    def paths_from(self, e):
        """
        :param e: Starting edge
        :return: All edges on this tile that can be reached from edge e.
        :rtype: set[str]
        """
        return set(
            itertools.chain(
                *map(
                    lambda p: p.difference({e}),
                    {p for p in self.paths if e in p}
                )
            )
        )

    def has_path(self, e1, e2):
        """
        Check for a path on this tile between edge e1 and edge e2
        :type e1: str
        :type e2: str
        :return: True iff this tile has a road between edges e1 and e2.
        :rtype: bool
        """
        return {e1, e2} in self.paths

    def __str__(self):
        d = dict(zip(Tile.EDGES, ("|", "-", "|", "-")))
        edge_chars = map(lambda e: d[e] if e else " ",
                         map(lambda e: e in self.edges_with_roads,
                             Tile.EDGES))
        return " {}\n{}-{}\n {}".format(*edge_chars)

    @staticmethod
    def get_orientations_with_edges(tile_class, edges):
        """
        Return a tuple containing all orientations which support the given
        set of edges (specified by constants Tile.N/E/S/W).

        :type tile_class: Tile
        :type edges: set[str]
        :rtype: set[int]
        """
        return {o for o in tile_class.CONFIGURATIONS
                if all((e in tile_class.CONFIGURATIONS[o] for e in edges))}

    @staticmethod
    def get_orientations_with_paths(tile_class, paths):
        """
        Return a tuple containing all orientations which support the given set
        of paths (specified by pairs of the constants Tile.N/E/S/W).

        :type tile_class: Tile
        :type paths: set[str]
        :rtype: set[int]
        """
        if not tile_class.PATHS:
            return Tile.get_orientations_with_edges(
                tile_class, set(itertools.chain(*paths)))
        return {o for o in tile_class.PATHS
                if all((p in tile_class.PATHS[o] for p in paths))}


class TTile(Tile):
    """
    Represents a tile with a T-shaped road connecting 3 edges
    """
    CONFIGURATIONS = {1: {Tile.E, Tile.S, Tile.W},
                      2: {Tile.N, Tile.S, Tile.W},
                      3: {Tile.N, Tile.E, Tile.W},
                      4: {Tile.N, Tile.E, Tile.S}}

    ORIENTATIONS = CONFIGURATIONS.keys()

    def __init__(self, tile_id, orientation):
        super().__init__(tile_id, TTile.CONFIGURATIONS[orientation])


class CrossTile(Tile):
    """
    Represents a tile with crossroads connecting all four edges
    """
    CONFIGURATIONS = {1: set(Tile.EDGES)}

    def __init__(self, tile_id, orientation=1):
        super().__init__(tile_id, set(Tile.EDGES))

    # staticmethod get_orientations_for_edges(edges) is same as superclass


class CornerTile(Tile):
    """
    Represents a tile with one road between adjacent edges
    """
    CONFIGURATIONS = {1: {Tile.N, Tile.E},
                      2: {Tile.E, Tile.S},
                      3: {Tile.S, Tile.W},
                      4: {Tile.W, Tile.N}}
    ORIENTATIONS = CONFIGURATIONS.keys()

    def __init__(self, tile_id, orientation):
        super().__init__(tile_id, CornerTile.CONFIGURATIONS[orientation])


class LineTile(Tile):
    """
    Represents a tile with one road between opposite sides
    """
    CONFIGURATIONS = {1: {Tile.N, Tile.S},
                      2: {Tile.E, Tile.W}}
    ORIENTATIONS = CONFIGURATIONS.keys()

    def __init__(self, tile_id, orientation):
        super().__init__(tile_id, LineTile.CONFIGURATIONS[orientation])


class BridgeCrossTile(Tile):
    CONFIGURATIONS = CrossTile.CONFIGURATIONS
    PATHS = {{Tile.N, Tile.S}, {Tile.E, Tile.W}}

    def __init__(self, tile_id, orientation):
        super().__init__(tile_id,
                         CrossTile.CONFIGURATIONS[orientation],
                         BridgeCrossTile.PATHS)


class OppositeCornersTile(Tile):
    CONFIGURATIONS = {1: set(Tile.EDGES),
                      2: set(Tile.EDGES)}
    ORIENTATIONS = CONFIGURATIONS.keys()

    PATHS = {1: {{Tile.N, Tile.E}, {Tile.S, Tile.W}},
             2: {{Tile.N, Tile.W}, {Tile.S, Tile.E}}}

    def __init__(self, tile_id, orientation):
        super().__init__(tile_id,
                         CrossTile.CONFIGURATIONS[orientation],
                         OppositeCornersTile.PATHS[orientation])


def create_tiles(num_tiles):
    """
    IN:
        num_tiles: dictionary { Subclass of Tile : number of said tiles}

    OUT:
        list of Tiles
    """
    tiles = []

    count = 0
    for tile in num_tiles.keys():
        for i in range(num_tiles[tile]):
            id = 'id' + '-' + str(count)
            for orientation in tile.ORIENTATIONS:

                value = tile(id, orientation)
                tiles.append(value)
            count += 1

    return tiles
