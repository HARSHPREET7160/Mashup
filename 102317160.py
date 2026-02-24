from __future__ import annotations

import sys

from mashup_core import MashupError, create_mashup, validate_positive_int


def print_usage() -> None:
    print(
        "Usage: python 102317160.py <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>"
    )


def main() -> int:
    if len(sys.argv) != 5:
        print("Error: Incorrect number of parameters.")
        print_usage()
        return 1

    singer_name = sys.argv[1]
    try:
        number_of_videos = validate_positive_int(sys.argv[2], 10, "NumberOfVideos")
        audio_duration = validate_positive_int(sys.argv[3], 20, "AudioDuration")
    except MashupError as exc:
        print(f"Input error: {exc}")
        print_usage()
        return 1

    output_file_name = sys.argv[4]

    try:
        output_path = create_mashup(
            singer_name=singer_name,
            number_of_videos=number_of_videos,
            audio_duration_sec=audio_duration,
            output_filename=output_file_name,
        )
        print(f"Mashup created successfully: {output_path}")
        return 0
    except MashupError as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
