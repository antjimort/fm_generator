from flamapy.core.transformations import ModelToText

from flamapy.metamodels.Fmgenerator_metamodel.models.models import FmgeneratorModel


class FmgeneratorModelToText(ModelToText):

    @staticmethod
    def get_destination_extension() -> str:
        return 'uvl'

    def __init__(self, path: str, model: FmgeneratorModel):
        self.path = path
        self.model = FmgeneratorModel()

    def transform(self) -> str:
        # TODO: insert your code here
        return self.path
