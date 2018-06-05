__author__ = 'Mark'
from dejavu import Dejavu
from dejavu.recognize import FileRecognizer, MicrophoneRecognizer
import argparse
import os
import pprint
import csv

from lilo import Lilo, lilo_config


def main():
    # Set up our commang line arguments
    parser = argparse.ArgumentParser(
        description="Record some sound using the device microphone and recognize it with Dejavu.")
    args = parser.parse_args()

    djv = Dejavu(lilo_config.config)

    input("Press enter to begin...\n")

    print("Listening...")
    results = djv.recognize(MicrophoneRecognizer, seconds=3)
    print("Listening complete.")

    ordered_results = sorted(results[1], key=lambda x: x.get('confidence'), reverse=True)

    print([(t.get('song_name'), t.get('confidence')) for t in ordered_results])

    top_result = ordered_results[0]

    with open('library_lookup.csv') as fh:
        lines = csv.reader(fh, delimiter=' ')
        lookup = {l[2]: l[1] for l in lines}

        print("Best match: {}, confidence: {}".format(lookup.get(top_result.get('song_name')),
                                                      top_result.get('confidence')))


if __name__ == '__main__':
    main()
