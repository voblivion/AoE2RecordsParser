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

    def read(self, count=1):
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
        return rep.decode('utf-8')

    def read(self, *args, **kwargs):
        return self.data.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self.data.seek(*args, **kwargs)

    def readUntil(self, *args, **kwargs):
        return self.data.readUntil(*args, **kwargs)

    def unpack(self, format, length):
        return struct.unpack(format, self.data.read(length))[0]

        

class DataParser:
    def __init__(self, data):
        self.data = DataWrapper(data)

    def run(self):
        raise NotImplementedError

class GameRecordParser(DataParser):
    # FIXME
    def run(self, idx):
        data = self.data

        header_len = data.readInt()
        #data.seek(-4, 1)
        #print(' '.join('{:02x}'.format(x) for x in data.read(4)), header_len)
        next_pos = data.readInt()
        
        compressed = data.read(header_len - 8)
        header_data = zlib.decompress(compressed, -zlib.MAX_WBITS)

        hp = HeaderParser(header_data)
        # FIXME
        return hp.run(idx)

class HeaderParser(DataParser):
    # FIXME
    def run(self, idx):
        data = self.data

        version_name = data.readString()
        sub_version = data.readFloat(2)

        version = data.readFloat() # 1000 for 4.7, 1004 for 4.8, 1005 for 5.1 and 5.2
        ukn = data.readInt() # 1000
        if version != 1005:
            return []

        has_special_dlcs = data.readBool(4)
        games_count = data.readInt()
        games_ids = []
        for k in range(0, games_count):
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
        ukn = data.readInt() # 1604517888

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
            ukn3 = data.readInt() # 0, 1, 3 ?

            # ----
            civilisation = data.readInt()

            ai_type_size = data.readShort()
            cst = data.read(2) # 2656
            ai_type = data.readChars(ai_type_size)
            
            # ----
            ukn4 = data.readTiny() # Random number for AI ?

            ai_name_size = data.readShort()
            cst = data.read(2) # 2656
            ai_name = data.readChars(ai_name_size)

            player_name_size = data.readShort()
            cst = data.read(2) # 2656
            player_name = data.readChars(player_name_size)

            hummanity = data.readInt() # 1 = None, 2 = Player, 4 = AI
            steam_id = data.readLongLong() # related to name ?

            player_id = data.readInt()

            players.append({
                    'id': player_id,
                    'num': player_num,
                    'civilisation': civilisation,
                    'ai_type': ai_type,
                    'ai_name': ai_name,
                    'name': player_name,
                    'hummanity': hummanity,
                    'steam_id': steam_id
                })

        ukn = data.readInt()
        ukn = data.readInt()
        ukn = data.readBool()
        ukn = data.readBool()
        ukn = data.readBool()
        ukn = data.readBool()

        cst = data.readInt() # 155555

        ukn = data.readBool()
        ukn = data.readBool()
        ukn0 = data.readInt()
        ukn1 = data.read(4)

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
        ukn_name = data.readChars(ukn_name_size)

        ukn6 = data.read(4)
        ukn7 = data.read(4)
        ukn8 = data.read(16)

        game_name_size = data.readShort()
        cst = data.read(2) # 2656
        game_name = data.readChars(game_name_size)

        ukn_name_size = data.readShort()
        cst = data.read(2) # 2656
        ukn_name = data.readChars(ukn_name_size)

        ukn9 = data.read(4)
        ukn10 = data.read(4)

        ukn_name_size = data.readShort()
        cst = data.read(2) # 2656
        ukn_name = data.readChars(ukn_name_size)

        ukn1 = data.read(4)
        ukn2 = data.read(4)
        ukn3 = data.readShort() # ?
        entries_count = data.readShort()
        ukn4 = data.read(4)

        for k in range(0, entries_count):
            ukn_name_size = data.readShort()
            cst = data.read(2) # 0000
            ukn_name = data.readChars(ukn_name_size)
    
        ukn = data.readShort()
        ukn = data.readShort()
        ukn = data.readShort()
        ukn = data.read(16)
        ukn = data.read(4)
        ukn = data.read(4)

        return [ukn, data.read(idx)]

def pretty(data, force=False):
    if isinstance(data, bytes) and (True or force):
        return ' '.join('{:02x}'.format(x) for x in data)
    else:
        return data
# 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 26, 27, 38, 39, 40, 41, 45 -> 0
# 33, 34, 35, 36 -> 22
# 21 -> 50
# 19 -> 225
# 14, 16, 17 -> 229
# 0 -> 924

if __name__ == '__main__':
    files_start = 0
    files_count = 49
    max_idx = 8
    exceptions = [12, 13, 30, 31, 32, 44]
    files = []
    grps = []
    vals = []
    for k in range(0, files_count):
        f = open('records/game{:03}.aoe2record'.format(files_start+k), 'rb')
        files.append(f)
        grps.append(GameRecordParser(f))

    idx = 1
    keep = True
    counter = 22
    reps = []
    while keep:
        reps = []
        diff = False
        for k in range(0, files_count):
            files[k].seek(0)
            rep = grps[k].run(idx)
            reps.append(rep)
            if k not in exceptions and len(reps) > 0 and reps[0][-1] != rep[-1]:
                diff = True
        if diff:
            counter -= 1
            if counter < 0:
                keep = False
        idx += 1
        if idx > max_idx:
            keep = False

    print(idx - 1)
    for k in range(0, files_count):
        if k not in exceptions:
            print('{:02}'.format(files_start+k), [pretty(x) for x in reps[k]])
