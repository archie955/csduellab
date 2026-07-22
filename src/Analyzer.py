from pathlib import Path

from awpy import Demo


class Analyzer:
    def __init__(self, rel_path: str):
        self.path = Path(__file__).parent.joinpath(rel_path)
        self.demo = Demo(self.path).parse()
        self.model = Path(__file__).parent.joinpath("./data/duel_gradient_booster.json")

    # this is a private, inaccessible function from outside
    def __filter_demo(self, player_name: str):
        pass
