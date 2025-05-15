from flamapy.core.models import VariabilityModel
from flamapy.core.transformations import ModelModel

from flamapy.metamodels.Fmgenerator_metamodel.models.models import FmgeneratorModel


class TODOToFmgenerator(ModelToModel):

    @staticmethod
    def get_source_extension() -> str:
        return 'TODO'  # TODO: modify source extension

    @staticmethod
    def get_destination_extension() -> str:
        return 'uvl'

    def __init__(self, source_model: VariabilityModel):
        self.source_model = source_model
        self.destiny_model = FmgeneratorModel()

    def transform(self) -> FmgeneratorModel:
        # TODO: insert your code here
        return self.destiny_model
