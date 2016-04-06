
# add dejavu to python path
import os, sys, inspect
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

from dejavu import Dejavu
from dejavu.recognize import FileRecognizer
from dejavu.database import get_database, Database
import argparse

class Lilo():
    """
    The class for JamJar which will be used to identify video matches and add fingerprints to the database
    """

    def __init__(self, config, filename, video_id):
        """
        usage:
            fingerprinter = Lilo('/path/to/video/file','unique_video_id')
        """
        self.djv = Dejavu(config)
        self.filename = filename
        self.video_id = video_id

        # cache these after first fingerprint
        self.hashes = None

    def recognize_track(self):
        # Try to match the song to the existing database
        hashes, songs = self.djv.recognize(FileRecognizer, self.filename)

        self.hashes = hashes

        return songs

    def fingerprint_song(self):
        # Now let's add this song to the DB
        data = self.djv.fingerprint_file(self.filename, self.video_id, cached_hashes=self.hashes)
        return data
