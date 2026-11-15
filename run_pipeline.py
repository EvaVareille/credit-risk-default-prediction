"""Rebuild every output from the raw data with one command.

    python run_pipeline.py                # run all steps
    python run_pipeline.py --from train   # resume from a step
"""

import argparse
import sys

from credit_risk.data import clean, ingest, validate
from credit_risk.export import to_powerbi
from credit_risk.features import build_features
from credit_risk.models import evaluate, explain, train

STEPS = {
    "ingest": ingest.run,
    "clean": clean.run,
    "validate": validate.run,
    "features": build_features.run,
    "train": train.run,
    "evaluate": evaluate.run,
    "explain": explain.run,
    "export": to_powerbi.run,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from", dest="start", choices=STEPS, default="ingest", help="step to start from")
    args = parser.parse_args()

    names = list(STEPS)
    for name in names[names.index(args.start):]:
        print(f"==> {name}")
        try:
            STEPS[name]()
        except NotImplementedError as exc:
            print(f"    stopped: {exc}")
            return 1
    print("Pipeline complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
