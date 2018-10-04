__author__ = 'Mark'
import argparse
import os
import pprint

from lilo import Lilo
from lilo3 import lilo_config


def main():
    # Set up our commang line arguments
    parser = argparse.ArgumentParser(description="Take in a folder of video and/or audio files and find the alignment"
                                                 "of them all.")
    parser.add_argument("folder",type=str,help="The folder containing your audio and video files, relative to the current directory.")
    args = parser.parse_args()

    # Get the files in our folder
    dir = os.path.expanduser(args.folder)
    files = os.listdir(dir)

    alignment_data = {}

    # Iterate through the files
    for index, filename in enumerate(files):
        full_path = os.path.join(dir,filename)

        # For now we'll assume all the files are valid audio or video
        if (os.path.isfile(full_path)):

            print("Attempting to match {0}...".format(filename))

            lilo = Lilo(lilo_config.config, full_path, filename)

            # Try to match the song to the existing database
            songs = lilo.recognize_track()

            if not songs:
                print("No matches found.")

            alignment_data[filename] = songs

            print("Adding {0} to database...".format(filename))

            # Now let's add this song to the DB
            lilo.fingerprint_song()

            print("Fingerprinting of {0} complete.".format(filename))

    pprint.pprint(alignment_data)


if __name__ == '__main__':
    main()