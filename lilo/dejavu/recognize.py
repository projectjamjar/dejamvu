import dejavu.fingerprint as fingerprint
import dejavu.decoder as decoder
import numpy as np
import pyaudio
import time


class BaseRecognizer(object):

    def __init__(self, dejavu):
        self.dejavu = dejavu
        self.Fs = fingerprint.DEFAULT_FS

    def _recognize(self, *data):
        # it's very simple -- ya got yer hashes and yer matches...
        matches = []
        hashes = []
        for d in data:
            _hashes, _matches = self.dejavu.find_matches(d, Fs=self.Fs)
            matches.extend(_matches)
            hashes.extend(_hashes)
        match = self.dejavu.align_matches(matches)
        return hashes, match

    def recognize(self):
        pass  # base class does nothing


class FileRecognizer(BaseRecognizer):
    def __init__(self, dejavu):
        super(FileRecognizer, self).__init__(dejavu)

    def recognize_file(self, filename):
        frames, self.Fs, file_hash, song_length = decoder.read(filename, self.dejavu.limit)

        t = time.time()
        hashes, match = self._recognize(*frames)
        t = time.time() - t

        if match:
            if self.dejavu.multiple_match:
                for track in match:
                    track['match_time'] = t/len(match)
            else:
                match['match_time'] = t

        return hashes, match

    def recognize(self, filename):
        return self.recognize_file(filename)

class NoRecordingError(Exception):
    pass
