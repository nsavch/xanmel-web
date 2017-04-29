from collections import defaultdict

from xanmel.modules.xonotic.models import *

MAX_POS = 15
POS_CORRECTION_FUN = lambda n: (MAX_POS - n) ** 2
NUM_SKIP_BAD_MAPS = 3
NORMALIZE_BOUNDS = (100, 1000)
ITERATION_CORRECTION_FUN = lambda n: 2**(-n)


class PlayerRating:
    def __init__(self, server_id):
        self.server_id = server_id
        self.map_times = defaultdict(list)
        self.map_rating_iterations = []
        self.total_rating_iterations = []
        self.load_times()
        self.initial()
        self.current_iteration_number = 1

    def load_times(self):
        records = XDFTimeRecord.select().join(Map).order_by(XDFTimeRecord.position)
        for record in records:
            self.map_times[record.map].append(record)

    def __normalize(self, rating):
        lower = min(rating.values())
        for i in rating:
            rating[i] = (rating[i] - lower) + NORMALIZE_BOUNDS[0]

    def initial(self):
        map_rating = defaultdict(dict)  # player -> map -> rating
        for map, times in self.map_times.items():
            if len(times) == 0:
                continue
            record = times[0]
            for i in times:
                rating = 0
                for j in times:
                    if i.id != j.id:
                        rating += POS_CORRECTION_FUN(j.position) * ((j.time - i.time) / record.time)
                map_rating[i.player][map] = rating
        self.map_rating_iterations = [map_rating]
        total_rating = {}
        for player in map_rating:
            rating = 0
            skipped = NUM_SKIP_BAD_MAPS
            has_some = False
            for value in sorted(map_rating[player].values()):
                if value < 0 and skipped > 0:
                    skipped -= 1
                    continue
                rating += value
                has_some = True
            if has_some:
                total_rating[player] = rating / len(map_rating[player])
        self.__normalize(total_rating)
        for player, rating in sorted(total_rating.items(), key=lambda x: x[1], reverse=True):
            print(player.nickname, rating)
        self.total_rating_iterations = [total_rating]

    def next(self):
        # THIS DOESN'T WORK :(
        map_rating = defaultdict(dict)
        for map, times in self.map_times.items():
            if len(times) == 0:
                continue
            record = times[0]
            for i in times:
                rating = 0
                prev_rating = self.map_rating_iterations[-1][i.player][map]
                for j in times:
                    if i.id != j.id:
                        player_rating = self.total_rating_iterations[-1].get(i.player, NORMALIZE_BOUNDS[0])
                        opponent_rating = self.total_rating_iterations[-1].get(j.player, NORMALIZE_BOUNDS[0])
                        raw_rating = POS_CORRECTION_FUN(j.position) * ((j.time - i.time) / record.time)
                        if i.position < j.position:
                            rating += prev_rating + ITERATION_CORRECTION_FUN(self.current_iteration_number) * (opponent_rating - player_rating)
                        else:
                            rating += prev_rating + ITERATION_CORRECTION_FUN(self.current_iteration_number) * (player_rating - opponent_rating)
                map_rating[i.player][map] = rating
        self.map_rating_iterations.append(map_rating)
        total_rating = {}
        for player in map_rating:
            rating = 0
            skipped = NUM_SKIP_BAD_MAPS
            has_some = False
            for value in sorted(map_rating[player].values()):
                if value < 0 and skipped > 0:
                    skipped -= 1
                    continue
                rating += value
                has_some = True
            if has_some:
                total_rating[player] = rating / len(map_rating[player])
        self.__normalize(total_rating)
        for player, rating in sorted(total_rating.items(), key=lambda x: x[1], reverse=True):
            print(player.nickname, rating, rating - self.total_rating_iterations[-1].get(player, NORMALIZE_BOUNDS[0]))
        self.total_rating_iterations.append(total_rating)
        self.current_iteration_number += 1
