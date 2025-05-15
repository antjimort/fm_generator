import random
from enum import Enum
from dataclasses import dataclass, field
from flamapy.metamodels.fm_metamodel.models.feature_model import (
    FeatureModel, Feature, Relation, Constraint, Attribute, Domain, Range
)
from flamapy.core.models.ast import AST, ASTOperation, Node
from fm_generator.flamapy.metamodels.FMGenerator.models.config import Params

def generate_random_attributes(params: Params, features: list[Feature]) -> None:
    num_attributes = random.randint(params.MIN_ATTRIBUTES, params.MAX_ATTRIBUTES)
    for i in range(num_attributes):
        feature = random.choice(features)
        attr_name = f"Attr{i}"
        attr_type = random.choice(['boolean', 'integer', 'real', 'string'])

        if attr_type == 'boolean':
            domain = Domain(ranges=None, elements=[True, False])
            default = random.choice([True, False])
        elif attr_type == 'integer':
            min_val, max_val = random.randint(0, 50), random.randint(51, 100)
            domain = Domain(ranges=[Range(min_val, max_val)], elements=None)
            default = random.randint(min_val, max_val)
        elif attr_type == 'real':
            min_val, max_val = random.randint(0, 50), random.randint(51, 100)
            domain = Domain(ranges=[Range(min_val, max_val)], elements=None)
            default = round(random.uniform(min_val, max_val), 2)
        else:  # string
            options = ["low", "medium", "high"]
            domain = Domain(ranges=None, elements=options)
            default = random.choice(options)

        attribute = Attribute(name=attr_name, domain=domain, default_value=default)
        attribute.set_parent(feature)
        feature.add_attribute(attribute)

def assign_manual_attributes(params: Params, features: list[Feature]) -> None:
    assert params.MIN_ATTRIBUTES is None and params.MAX_ATTRIBUTES is None, (
        "MIN_ATTRIBUTES and MAX_ATTRIBUTES must be None when using manual attributes."
    )
    for attr, prob in zip(params.ATTRIBUTES_LIST, params.ATTRIBUTE_ATTACH_PROBS):
        for feature in features:
            if random.random() < prob:
                new_attr = Attribute(name=attr.name, domain=attr.domain, default_value=attr.default_value)
                new_attr.set_parent(feature)
                feature.add_attribute(new_attr)

def generate_single_model(params: Params, index: int) -> FeatureModel:
    """
    Generate a single feature model.
    """
    random.seed(params.SEED + index)

    # Crear la raíz del modelo
    root_feature = Feature(name=f"{params.NAME_PREFIX.upper()}_{index}")
    fm = FeatureModel(root=root_feature)

    # Generar features hijas
    num_features = random.randint(params.MIN_FEATURES, params.MAX_FEATURES)
    features: list[Feature] = []

    for i in range(1, num_features):
        fname = f"F{i}"
        feature = Feature(name=fname)
        features.append(feature)

    create_relations_with_cardinality(root_feature, features, params)

    # Atributos en Boolean level
    if params.RANDOM_ATTRIBUTES:
        generate_random_attributes(params, features)
    else:
        assign_manual_attributes(params, features)

    # Constraints simples: A => B
    for i in range(random.randint(params.MIN_CONSTRAINTS, params.MAX_CONSTRAINTS)):
        a, b = random.sample(features, 2)
        left = Node(a.name)
        right = Node(b.name)
        root = Node(ASTOperation.IMPLIES, left, right)
        ast = AST(root)
        constraint = Constraint(name=f"ctc{i}", ast=ast)
        fm.ctcs.append(constraint)

    return fm

def create_relations_with_cardinality(root_feature: Feature, features: list[Feature], params: Params) -> None:
    i = 0
    while i < len(features):
        max_group_size = min(params.GROUP_CARDINALITY_MAX, len(features) - i)

        if params.GROUP_CARDINALITY_MIN > max_group_size:
            group_size = max_group_size
        else:
            group_size = random.randint(params.GROUP_CARDINALITY_MIN, max_group_size)

        group = []
        for _ in range(group_size):
            if i >= len(features):
                break
            group.append(features[i])
            i += 1

        if len(group) == 1:
            rel_type = random.choices([(1, 1), (0, 1)], weights=[params.DIST_MANDATORY, params.DIST_OPTIONAL])[0]
            relation = Relation(parent=root_feature, children=group, card_min=rel_type[0], card_max=rel_type[1])
        else:
            max_cardinality = len(group)

            if (random.random() < params.DIST_GROUP_CARDINALITY and max_cardinality >= params.GROUP_CARDINALITY_MIN):
                min_bound = max(params.GROUP_CARDINALITY_MIN, 1)
                max_bound = min(params.GROUP_CARDINALITY_MAX, max_cardinality)
                min_c = random.randint(min_bound, max_bound)
                max_c = random.randint(min_c, max_bound)
                relation = Relation(parent=root_feature, children=group, card_min=min_c, card_max=max_c)
            else:
                rel_type = random.choices(
                    [(1, len(group)), (1, 1)],
                    weights=[params.DIST_OR, params.DIST_ALTERNATIVE]
                )[0]
                relation = Relation(parent=root_feature, children=group, card_min=rel_type[0], card_max=rel_type[1])

        root_feature.add_relation(relation)
