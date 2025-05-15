from flamapy.core.transformations import TextToModel

from flamapy.metamodels.Fmgenerator_metamodel.models.models import FmgeneratorModel


class FmgeneratorTextToModel(TextToModel):

    @staticmethod
    def get_source_extension() -> str:
        return 'uvl'

    def __init__(self, path: str, model: FmgeneratorModel):
        self.path = path
        self.model = model

    def transform(self) -> FmgeneratorModel:
        # TODO: insert your code here
        return self.model
