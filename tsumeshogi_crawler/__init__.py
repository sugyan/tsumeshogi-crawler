from argparse import ArgumentParser
from pathlib import Path

from .crawler import Crawler


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--target-year", type=int)
    parser.add_argument("outdir", type=Path)
    args = parser.parse_args()

    Crawler(args.outdir, args.target_year, args.verbose).run()


if __name__ == "__main__":
    main()
