from flamapy.core.models import VariabilityModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from fm_generator.flamapy.metamodels.FMGenerator.operations.generate_models import (
    generate_single_model,
)
from fm_generator.flamapy.metamodels.FMGenerator.models.config import Params
from pathlib import Path
from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import UVLWriter


class FmgeneratorModel(VariabilityModel):
    @staticmethod
    def get_extension() -> str:
        return "fm"

    def __init__(self, params: Params) -> None:
        self.params = params

    def generate_models(self) -> list[FeatureModel]:
        fms = [
            generate_single_model(self.params, i) for i in range(self.params.NUM_MODELS)
        ]
        for i in range(len(fms)):
            output_file = Path(f"test_models/{self.params.NAME_PREFIX}{i}.uvl")
            UVLWriter(str(output_file), fms[i]).transform()
            print(f"Modelo generado y exportado en: {output_file}")

