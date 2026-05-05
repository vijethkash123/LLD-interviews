from models import SplitType
from splitStrategies import EqualSplitStrategy, PercentSplitStrategy, SplitStrategyInterface
class SplitStrategyFactory:
    @staticmethod
    def get_split_strategy(split_type: SplitType) -> 'SplitStrategyInterface':
        if split_type == SplitType.EQUAL:
            return EqualSplitStrategy()
        elif split_type == SplitType.PERCENTAGE:
            return PercentSplitStrategy()
        else:
            raise ValueError("Invalid split type")