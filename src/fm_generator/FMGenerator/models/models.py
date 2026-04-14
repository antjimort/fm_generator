from flamapy.core.models import VariabilityModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from fm_generator.FMGenerator.operations.generate_models import (
    generate_single_model,
)
from fm_generator.FMGenerator.models.config import Params
from pathlib import Path
from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import UVLWriter
import os


def prepend_uvl_includes(serialized_model: str, includes: list[str]) -> str:
    if not includes:
        return serialized_model

    include_block = "include\n" + "\n".join(f"\t{inc}" for inc in includes) + "\n"
    return include_block + serialized_model


class FmgeneratorModel(VariabilityModel):
    @staticmethod
    def get_extension() -> str:
        return "fm"

    def __init__(self, params: Params) -> None:
        self.params = params

    def generate_models(self, output_dir: str) -> list[FeatureModel]:
        print(self.params)
        fms = [
            generate_single_model(self.params, i) for i in range(self.params.NUM_MODELS)
        ]

        for i in range(len(fms)):
            output_file = Path(os.path.join(output_dir, f"{self.params.NAME_PREFIX}{i}.uvl"))

            # Serializar sin escribir directamente con el writer del framework
            serialized_model = UVLWriter(None, fms[i]).transform()

            # Añadir include si procede
            serialized_model = prepend_uvl_includes(
                serialized_model,
                getattr(fms[i], "uvl_includes", [])
            )

            # Escribir el fichero final
            with open(output_file, "w", encoding="utf8") as file:
                file.write(serialized_model)

            print(f"Modelo generado y exportado en: {output_file}")

        return fms