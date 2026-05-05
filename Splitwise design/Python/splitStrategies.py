from abc import ABC
from typing import List
from models import Split, User


class SplitStrategyInterface(ABC):
    def split(self, total_amount: float, participants: List['User'], metadata: dict[User, float]) -> List['Split']:
        pass

class EqualSplitStrategy(SplitStrategyInterface):
    def split(self, total_amount: float, participants: List['User'], metadata: dict[User, float]) -> List['Split']:
        num_participants = len(participants)
        split_amount = total_amount / num_participants
        return [Split(user, split_amount) for user in participants]
    
class PercentSplitStrategy(SplitStrategyInterface):
    def split(self, total_amount: float, participants: List['User'], metadata: dict[User, float]) -> List['Split']:
        total_percentage = sum(metadata.values())
        if total_percentage != 100:
            raise ValueError("Total percentage must be 100")
        splits = []
        for user in participants:
            percentage = metadata.get(user, 0)
            split_amount = (percentage / 100) * total_amount
            splits.append(Split(user, split_amount))
        return splits