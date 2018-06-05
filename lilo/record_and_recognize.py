__author__ = 'Mark'
from dejavu import Dejavu
from dejavu.recognize import FileRecognizer, MicrophoneRecognizer
import argparse
import os
import pprint

from lilo import Lilo, lilo_config


def main():
    # Set up our commang line arguments
    parser = argparse.ArgumentParser(
        description="Record some sound using the device microphone and recognize it with Dejavu.")
    args = parser.parse_args()

    djv = Dejavu(lilo_config.config)

    raw_input("Press enter to begin...\n")

    print "Listening..."
    results = djv.recognize(MicrophoneRecognizer)
    print "Listening complete."

    ordered_results = sorted(results[1], key=lambda x: x.get('confidence'), reverse=True)

    print [(t.get('song_name'), t.get('confidence')) for t in ordered_results]



if __name__ == '__main__':
    main()
