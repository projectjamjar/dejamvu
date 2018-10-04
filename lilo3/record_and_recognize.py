__author__ = 'Mark'
from dejavu import Dejavu
from dejavu.recognize import MicrophoneRecognizer
import argparse
import csv

from lilo3 import lilo_config


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

    with open('library_lookup.csv') as fh:
        lines = csv.reader(fh, delimiter=' ')

        lookup = {l[2]: l[1] for l in lines}

        track_and_confidence = [(lookup.get(t.get('song_name')), t.get('confidence')) for t in ordered_results]

        print()

        top_results = track_and_confidence[0:5]

        for result in top_results:
            print("Match: {}, confidence: {}".format(result[0], result[1]))


if __name__ == '__main__':
    main()
