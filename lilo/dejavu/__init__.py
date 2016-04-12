from dejavu.database import get_database, Database
import dejavu.decoder as decoder
import fingerprint
import multiprocessing
import os
import traceback
import sys


class Dejavu(object):

    SONG_ID = "song_id"
    SONG_NAME = 'song_name'
    CONFIDENCE = 'confidence'
    MATCH_TIME = 'match_time'
    OFFSET = 'offset'
    VIDEO_ID = 'video_id'
    OFFSET_SECS = 'offset_seconds'

    def __init__(self, config):
        super(Dejavu, self).__init__()

        self.config = config

        # initialize db
        db_cls = get_database(config.get("database_type", None))

        self.db = db_cls(**config.get("database", {}))
        self.db.setup()

        self.multiple_match = config.get("multiple_match",False)

        # if we should limit seconds fingerprinted,
        # None|-1 means use entire track
        self.limit = self.config.get("fingerprint_limit", None)
        if self.limit == -1:  # for JSON compatibility
            self.limit = None
        self.get_fingerprinted_songs()

    def get_fingerprinted_songs(self):
        # get songs previously indexed
        self.songs = self.db.get_songs()
        self.songhashes_set = set()  # to know which ones we've computed before
        for song in self.songs:
            song_hash = song[Database.FIELD_FILE_SHA1]
            self.songhashes_set.add(song_hash)

    def fingerprint_file(self, filepath, video_id, song_name=None, cached_hashes=None):
        """
            If file has already been fingerprinted, return None.
            Else, return information about the file
        """
        songname = decoder.path_to_songname(filepath)
        song_hash = decoder.unique_hash(filepath)
        song_name = song_name or songname
        # don't refingerprint already fingerprinted files
        if song_hash in self.songhashes_set:
            print "%s already fingerprinted, continuing..." % song_name
            return None
        else:
            song_name, hashes, file_hash, length_in_seconds = _fingerprint_worker(
                filepath,
                self.limit,
                song_name=song_name,
                cached_hashes=cached_hashes
            )
            sid = self.db.insert_song(song_name, video_id, file_hash)

            self.db.insert_hashes(sid, hashes)
            self.db.set_song_fingerprinted(sid)
            self.get_fingerprinted_songs()

            return {
                "song_length" : length_in_seconds
            }

    def find_matches(self, samples, Fs=fingerprint.DEFAULT_FS):
        hashes = fingerprint.fingerprint(samples, Fs=Fs)
        hashes_list = list(hashes)
        matches = self.db.return_matches(hashes_list)

        return hashes_list, matches

    def align_matches(self, matches):
        """
            Finds hash matches that align in time with other matches and finds
            consensus about which hashes are "true" signal from the audio.

            Returns a dictionary with match information.

            If "multiple_match" is set to True in the config, this will return
            a list of dictionaries with match information.
        """
        # align by diffs
        diff_counter = {}

        if self.multiple_match:
            largest = {} # A dictionary of song id's to ???
            largest_count = {} # A dictionary of song id's to ???

            # Run through all of the (song id, offset)
            for tup in matches:
                # diff = database offset from original track - sample offset from recording
                # You can think of this as a possible offset for the sample track
                sid, diff = tup

                # If we haven't had any other matches with this offset yet, add it to the map
                if diff not in diff_counter:
                    diff_counter[diff] = {}

                # If we haven't had this offset with this song yet, add the song
                if sid not in diff_counter[diff]:
                    diff_counter[diff][sid] = 0

                # Increment the match count for this offset and song
                diff_counter[diff][sid] += 1

                # If we haven't matched with this song yet, add it to the count map
                if sid not in largest_count:
                    largest_count[sid] = 0
                    largest[sid] = 0

                # If we have more matches for this offset than any other offset in the song, update it
                if diff_counter[diff][sid] > largest_count[sid]:
                    largest[sid] = diff # The offset prediction for this song
                    largest_count[sid] = diff_counter[diff][sid] # The number of fingerprints we matched on for this offset

            # If we didn't match any songs, return none
            if len(largest_count) == 0:
                return None

            songs = []

            # Run through all of the songs that we matched with and add our best guess for the offset to the list of matched songs
            for song_id, count in largest_count.iteritems():
                # extract idenfication
                song = self.db.get_song_by_id(song_id)
                songname = song.get(Dejavu.SONG_NAME, None)

                # return match info
                nseconds = round(float(largest[song_id]) / fingerprint.DEFAULT_FS *
                                 fingerprint.DEFAULT_WINDOW_SIZE *
                                 fingerprint.DEFAULT_OVERLAP_RATIO, 5)

                # Our confidence is the number of fingerprint matches we had for the offset prediciton with the most matches
                song = {
                    Dejavu.SONG_ID: song_id,
                    Dejavu.SONG_NAME: songname,
                    Dejavu.CONFIDENCE: count,
                    Dejavu.OFFSET: int(largest[song_id]),
                    Dejavu.OFFSET_SECS: nseconds,
                    Dejavu.VIDEO_ID: song.get(Dejavu.VIDEO_ID, None),
                }

                songs.append(song)

            return songs
        else:
            largest = 0
            largest_count = 0
            song_id = -1
            for tup in matches:
                sid, diff = tup
                if diff not in diff_counter:
                    diff_counter[diff] = {}
                if sid not in diff_counter[diff]:
                    diff_counter[diff][sid] = 0
                diff_counter[diff][sid] += 1

                if diff_counter[diff][sid] > largest_count:
                    largest = diff
                    largest_count = diff_counter[diff][sid]
                    song_id = sid

            # extract idenfication
            song = self.db.get_song_by_id(song_id)
            if song:
                # TODO: Clarify what `get_song_by_id` should return.
                songname = song.get(Dejavu.SONG_NAME, None)
            else:
                return None

            # return match info
            nseconds = round(float(largest) / fingerprint.DEFAULT_FS *
                             fingerprint.DEFAULT_WINDOW_SIZE *
                             fingerprint.DEFAULT_OVERLAP_RATIO, 5)
            song = {
                Dejavu.SONG_ID : song_id,
                Dejavu.SONG_NAME : songname,
                Dejavu.CONFIDENCE : largest_count,
                Dejavu.OFFSET : int(largest),
                Dejavu.OFFSET_SECS : nseconds,
                Database.FIELD_FILE_SHA1 : song.get(Database.FIELD_FILE_SHA1, None),}
            return song

    def recognize(self, recognizer, *options, **kwoptions):
        r = recognizer(self)
        hashes, match = r.recognize(*options, **kwoptions)
        return hashes, match


def _fingerprint_worker(filename, limit=None, song_name=None, cached_hashes=None):
    # Pool.imap sends arguments as tuples so we have to unpack
    # them ourself.
    try:
        filename, limit = filename
    except ValueError:
        pass

    songname, extension = os.path.splitext(os.path.basename(filename))
    song_name = song_name or songname
    channels, Fs, file_hash, length_in_seconds = decoder.read(filename, limit)
    result = set()
    channel_amount = len(channels)

    if cached_hashes is None:
        for channeln, channel in enumerate(channels):
            # TODO: Remove prints or change them into optional logging.
            print("Fingerprinting channel %d/%d for %s" % (channeln + 1,
                                                           channel_amount,
                                                           filename))
            hashes = fingerprint.fingerprint(channel, Fs=Fs)

            print("Finished channel %d/%d for %s" % (channeln + 1, channel_amount,
                                                     filename))
            result |= set(hashes)
    else:
        result = set(cached_hashes)

    return song_name, result, file_hash, length_in_seconds


def chunkify(lst, n):
    """
    Splits a list into roughly n equal parts.
    http://stackoverflow.com/questions/2130016/splitting-a-list-of-arbitrary-size-into-only-roughly-n-equal-parts
    """
    return [lst[i::n] for i in xrange(n)]
