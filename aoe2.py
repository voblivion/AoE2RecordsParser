import struct
import os
import zlib
import base64
import sys
import re

class ObjectWrapper:
    def __init__(self, object):
        self.pos = 0
        self.data = object

    def read(self, count=None):
        if count is None:
            count = len(self.data) - self.pos
        rep = self.data[self.pos:self.pos+count]
        self.pos += count
        return rep

    def seek(self, offset, whence=0):
        if whence == 0:
            self.pos = offset
        elif whence == 1:
            self.pos += offset
        elif whence == 2:
            self.pos = len(self.data) + offset

    def readUntil(self, pattern, included=True):
        length = len(pattern)
        pos = self.data.find(pattern, self.pos)
        if included:
            rep = self.data[self.pos:pos+length]
            self.pos = pos + length
            return rep
        rep = self.data[self.pos:pos]
        self.pos = pos
        return rep

    def tell(self):
        return self.pos

class StreamWrapper:
    def __init__(self, stream):
        self.data = stream

    def read(self, *args):
        return self.data.read(*args)

    def seek(self, offset, whence=0):
        return self.data.seek(offset, whence)

    def readUntil(self, pattern, included=True):
        length = len(pattern)
        check = self.data.read(length)
        rep = ''
        if isinstance(pattern, bytes):
            rep = b''
        while check != pattern:
            rep = rep + check[0]
            check = check[1:] + self.data.read(1)
        if included:
            return rep + check
        self.data.seek(-length, 1)
        return rep

    def tell(self):
        return self.data.tell()


class DataWrapper:
    """
    A wrapper for wrapping aoe2 data
    """
    def __init__(self, data):
        if hasattr(data, 'read'):
            self.data = StreamWrapper(data)
        else:
            self.data = ObjectWrapper(data)

    def tell(self):
        return self.data.tell()

    def readBool(self, length=1):
        rep = struct.unpack('?', self.data.read(1))[0]
        if length > 1:
            self.data.read(length - 1)
        return rep

    def readChar(self):
        return self.data.read(1).decode('utf-8')

    def readChars(self, length):
        return self.data.read(length).decode('utf-8')

    def readTiny(self):
        return struct.unpack('<B', self.data.read(1))[0]

    def readShort(self):
        return struct.unpack('<H', self.data.read(2))[0]

    def readInt(self):
        return struct.unpack('<I', self.data.read(4))[0]

    def readLongLong(self):
        return struct.unpack('<Q', self.data.read(8))[0]

    def readFloat(self, decimals=-1):
        if decimals == -1:
            return struct.unpack('<f', self.data.read(4))[0]
        return round(struct.unpack('<f', self.data.read(4))[0], decimals)

    def readDouble(self):
        return struct.unpack('<d', self.data.read(8))[0]

    def readString(self, length_size=0):
        rep = self.data.readUntil(b'\x00')
        return rep[:-1].decode('utf-8')

    def read(self, *args, **kwargs):
        return self.data.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self.data.seek(*args, **kwargs)

    def readUntil(self, *args, **kwargs):
        return self.data.readUntil(*args, **kwargs)

    def unpack(self, format, length):
        return struct.unpack(format, self.data.read(length))[0]

class DataParser:
    def __init__(self, data, meta=None):
        self.data = DataWrapper(data)
        self.meta = meta

    def run(self):
        raise NotImplementedError

class GameRecordParser(DataParser):
    def run(self):
        data = self.data

        header_len = data.readInt()
        next_pos = data.readInt()
        
        compressed = data.read(header_len - 8)
        header_data = zlib.decompress(compressed, -zlib.MAX_WBITS)

        hp = HeaderParser(header_data)     
        hp.run()

        return {}

class HeaderParser(DataParser):
    # FIXME
    def run(self):
        data = self.data

        version_name = data.readString()
        sub_version = data.readFloat(2)

        version = data.readFloat() # 1000 for 4.7, 1004 for 4.8, 1005 for 5.1 and 5.2
        ukn = data.readInt() # 1000
        if version != 1005:
            return {}

        has_special_dlcs = data.readBool(4)
        games_count = data.readInt()
        games_ids = []
        for _ in range(0, games_count):
            games_ids.append(data.readInt())

        difficulty = data.readInt()
        map_size = data.readInt()
        map_id = data.readInt()
        visibility = data.readInt()
        victory_conditions = data.readInt()
        resources_level = data.readInt()
        starting_age = data.readInt()
        ending_age = data.readInt()
        game_type = data.readInt()

        cst = data.readInt() # int 155555

        # Starting here, 4.X is different from 5.X

        cst = data.readInt() # 155555

        speed = data.readFloat()
        treaty_length = data.readInt()
        population_limit = data.readInt()
        players_count = data.readShort()

        ukn = data.read(6) # 0

        victory_limit_value = data.readShort()
        ukn42 = data.readInt() # 1604517888

        ukn = data.readShort() # 2
        ukn = data.readShort() # 1

        team_together = not data.readBool() # 5.X no team together ?
        all_techs = data.readBool()

        ukn = data.readBool()

        lock_teams = data.readBool()
        lock_speed = data.readBool()

        ukn = data.readBool() # 1

        allow_cheats = data.readBool()

        ukn = data.readBool() # True
        ukn = data.readBool() # True
        ukn = data.readBool() # True

        cst = data.read(4) # 5.X int 155555

        players = []
        for k in range(0, 8):
            # ----
            ukn1 = data.readInt() # 3 ?
            
            player_num = data.readInt() + 1
            
            # ----
            ukn2 = data.read(1) # ff ?

            team = data.readTiny() - 1
            dat_file_crc = data.readInt()
            mp_game_version = data.readTiny()

            # ----
            ukn3 = data.readInt() # 0, 1, 3 ? AI Script ID ?

            # ----
            civilization = data.readInt()

            ai_type_size = data.readShort()
            cst = data.read(2) # 2656
            ai_type = data.readChars(ai_type_size)
            
            # ----
            ukn4 = data.readTiny() # Random number for AI ?

            tribe_name_size = data.readShort()
            cst = data.read(2) # 2656
            tribe_name = data.readChars(tribe_name_size)

            player_name_size = data.readShort()
            cst = data.read(2) # 2656
            player_name = data.readChars(player_name_size)

            hummanity = data.readInt() # 1 = None, 2 = Player, 4 = AI
            steam_id = data.readLongLong()

            player_id = data.readInt()

            players.append({
                    'id': player_id,
                    'num': player_num,
                    'civilization': civilization,
                    'ai_type': ai_type,
                    'tribe_name': tribe_name,
                    'name': player_name,
                    'hummanity': hummanity,
                    'steam_id': steam_id
                })

        ukn = data.readInt() # 0
        ukn = data.readInt() # 0
        ukn = data.readBool()
        ukn = data.readBool()
        ukn = data.readBool()
        ukn = data.readBool()

        cst = data.readInt() # 155555

        ukn = data.readBool()
        ukn = data.readBool()
        ukn0 = data.readInt() # 0
        ukn1 = data.read(4) # != 0 if SP game

        scenario_name_size = data.readShort()
        cst = data.read(2) # 2656
        scenario_name = data.readChars(scenario_name_size)

        ukn2 = data.read(4)
        ukn3 = data.read(4)

        map_name_size = data.readShort()
        cst = data.read(2) # 2656
        map_name = data.readChars(map_name_size)

        ukn4 = data.read(4)
        ukn5 = data.read(4)

        ukn_name_size = data.readShort()
        cst = data.read(2) # 2656
        ukn_name0 = data.readChars(ukn_name_size)

        ukn6 = data.read(4)
        ukn7 = data.read(4)
        ukn8 = data.read(16)

        game_name_size = data.readShort()
        cst = data.read(2) # 2656
        game_name = data.readChars(game_name_size)

        ukn_name_size = data.readShort()
        cst = data.read(2) # 2656
        ukn_name1 = data.readChars(ukn_name_size)

        ukn9 = data.read(4)
        ukn10 = data.read(4)

        ukn_name_size = data.readShort()
        cst = data.read(2) # 2656
        ukn_name2 = data.readChars(ukn_name_size)

        ukn1 = data.read(4)
        contains_ai_scripts = data.readBool(4)
        if contains_ai_scripts:
            ukn3 = data.readShort() # ?
            entries_count = data.readShort()
            ukn4 = data.read(2)
            ukn5 = data.read(2)

            ai_strings = []
            for k in range(0, entries_count):
                ai_string_size = data.readShort()
                cst = data.read(2) # 0000
                ai_string = data.readChars(ai_string_size)
                ai_strings.append(ai_string)

            ukn9 = data.read(6) # 3 uknown shorts

            ais = []
            for _ in range(0, 8):
                is_ai = data.readBool(4)
                ai_id = data.readInt()
                ukn = data.read(2)
                ai_rules_count = data.readShort()
                ukn = data.read(4)
                ai_rules = []
                for _ in range(0, ai_rules_count):
                    rule_data = data.read(784)
                    pass # FIXME
                    arp = AIRuleParser(rule_data)
                    rule = arp.run()
                    ai_rules.append(rule)

                ais.append({
                    'id': ai_id,
                    'rules_count': ai_rules_count,
                    'rules': ai_rules,
                })

            for k in range(0, 8):
                ukn = data.readInt() # 100
                ukn = data.read(4) # random ?
            ukn = data.readFloat() # ~(2)0.14 ?
            ukn0 = data.readFloat() # ~(2)0.29 ?
            ukn = data.read(6756) # ? To work on

        ukn = data.read(26) # 00 ...
        ukn1 = data.readFloat(4) # Again ??
        ukn = data.read(1) # ?
        ukn = data.readInt() # [1800, 6100]
        ukn = data.read(4) # fe ff ff ff
        ukn = data.readInt() # [0, 33000]
        ukn = data.readInt() # [0, 33000]
        point_of_view = data.readShort() # 1 -> 8
        all_players_count = data.readTiny() # includes Gaïa

        ukn = data.read(60)
        map_width = data.readInt()
        map_height = data.readInt()
        map_zones_count = data.readInt()
        map_zones = []
        for _ in range(0, map_zones_count):
            ukn0 = data.readInt() # <= map_width * map_height
            ukn1 = data.read(map_width*map_height*2) # ?
            ukn = data.read(2044)
            ukn2 = data.readInt()
            for _ in range(0, ukn2):
                ukn = data.readFloat() # 1.0, 2.0, 3.0, etc. ? then ?
            ukn3 = data.readInt()

        ukn = data.readTiny() # visibility ?
        ukn = data.readTiny() # fog of war ?

        map_infos = []
        ukn = data.read(map_width*map_height*2) # id + élévation

        ukn_count = data.readInt() # 3 or 5 ?
        ukn0 = data.readInt() # 8 ?

        for _ in range(0, ukn_count):
            ukn = data.readShort()
            ukn = data.readShort()

        for _ in range(0, 5):
            ukn = data.read(4)
            ukn = data.read(4)
            ukn = data.read(4)

        ukn = data.read(4)

        for _ in range(0, ukn_count):
            ukn = data.read(4)
            ukn = data.read(4)
            ukn = data.read(4)

        map_width = data.readInt()
        map_height = data.readInt()

        ukn = data.read(map_height * map_width * 4)

        ukn = data.read(8) # 00 ..
        ukn = data.readInt() # 40600 ?

        ukn = data.read(2) # 02 0b

        players_info = []
        for _ in range(0, 1):
            diplomacy_from = []
            for _ in range(0, players_count + 1):
                diplomacy = data.readTiny()
                diplomacy_from.append(diplomacy)

            diplomacy_to = []
            for _ in range(0, 9):
                diplomacy = data.readInt()
                diplomacy_to.append(diplomacy)

            ukn = data.read(5)

            name_size = data.readShort()
            name = data.readString() #

            ukn1 = data.readTiny() # 22
            civilization_headers_count = data.readInt()
            ukn3 = data.readTiny() # 33

            # Civilization's header
            food = data.readFloat()
            wood = data.readFloat()
            stone = data.readFloat()
            gold = data.readFloat()
            headroom = data.readFloat() # FAIL ?
            ukn1 = data.readFloat()
            ukn2 = data.readFloat()
            ukn3 = data.readFloat()
            ukn4 = data.readFloat()
            ukn5 = data.readFloat()
            ukn6 = data.readFloat()
            population = data.readFloat()
            for _ in range(0, 20):
                ukn = data.readFloat()
            max_population = data.readFloat() # FAIL ?
            ukn = data.readFloat()
            ukn = data.readFloat()
            ukn = data.readFloat() # 1.6
            farm_food_amount = data.readFloat() # FAIL ?
            civilian_population = data.readFloat() # FAIL ?
            ukn = data.readFloat() # 0
            ukn = data.readFloat() # 178
            military_population = data.readFloat() # FAIL ?
            for _ in range(0, 50):
                ukn = data.readFloat()
            food_bonus = data.readFloat()
            wood_bonus = data.readFloat()
            stone_bonus = data.readFloat()
            gold_bonus = data.readFloat()

            for _ in range(0, 103):
                ukn = data.readFloat()

            if has_special_dlcs:
                for _ in range(0, 13):
                    ukn = data.readFloat()

        ukn = data.read(1) # 0b
        ukn = data.readFloat()
        ukn = data.readFloat()
        ukn = data.read(9)
        ukn = data.read(4)

        return {}

class WorkingParser(DataParser):
    def run(self, depth):
        pass

class AIRuleParser(DataParser):
    def run(self):
        data = self.data


        ukn = data.read(4) # 01 00 00 00
        ukn = data.read(4) # 01 00 00 00
        id = data.readShort()
        sep = data.read(2) # ff ff
        conditions_count = data.readTiny()
        terms_count = data.readTiny()
        terms = []
        for _ in range(0, terms_count):
            term_data = data.read(24)
            artp = AIRuleTermParser(term_data)
            term = artp.run()
            terms.append(term)

        # Then there is few times 00 00 00 00 ff ff ff ff 00 00 00 00 00 00 00 00

        return {
            'id': id,
            'conditions_count': conditions_count,
            'terms_count': terms_count,
            'terms': terms,
        }

class AIRuleTermParser(DataParser):
    def run(self):
        data = self.data
        argument_0 = data.read(4)
        argument_1 = data.read(4)
        argument_2 = data.read(4)
        argument_3 = data.read(4)
        argument_4 = data.read(4)
        argument_5 = data.read(4)

        # FIXME
        return {
            '0': pretty(argument_0),
            '1': pretty(argument_1),
            '2': pretty(argument_2),
            '3': pretty(argument_3),
            '4': pretty(argument_4),
            '5': pretty(argument_5),
        }

def pretty(data, force=False):
    if isinstance(data, bytes) and (True or force):
        return ' '.join('{:02x}'.format(x) for x in data)
    else:
        return data

if __name__ == '__main__':
    # Select which records to use
    start = 0
    count = 48
    exceptions = [12, 13, 30, 31, 32]
    ids = [k for k in range(start, count) if k not in exceptions]

    # Choose analyze depth
    depth = 20
    max_depth = 20
    depth_step = 1
    depth_after = 20
    partial = False

    records = {}
    partials = {}
    remains = {}
    parsers = {}
    results = {}

    # Execute parsers
    for k in ids:
        if partial:
            partials[k] = open('tmp/game{:03}.partial'.format(k), 'r')
            remains[k] = open('tmp/game{:03}.remain'.format(k), 'rb')
            parsers[k] = WorkingParser(remains[k], partials[k])
        else:
            records[k] = open('records/game{:03}.aoe2record'.format(k), 'rb')
            partials[k] = open('tmp/game{:03}.partial'.format(k), 'w')
            remains[k] = open('tmp/game{:03}.remain'.format(k), 'wb')
            parsers[k] = GameRecordParser(records[k])

        parsers[k].run()

    # Search for next difference
    all_same = True
    while all_same and depth <= max_depth:
        results = {}
        prev = None
        for k in ids:
            results[k] = parsers[k].data.read(depth)
            parsers[k].data.seek(-depth, 1)
            if prev is not None and results[k] != prev:
                all_same = False
            prev = results[k]
        depth += depth_step

    # Read few more characters and close files
    for k in ids:
        print(k, pretty(parsers[k].data.read(depth+depth_after)))
        parsers[k].data.seek(-(depth+depth_after), 1)

        if not partial:
            remains[k].write(parsers[k].data.read())
            records[k].close()
        remains[k].close()
        partials[k].close()
