import random
import string
from enum import Enum
from dataclasses import dataclass, field
from flamapy.metamodels.fm_metamodel.models.feature_model import (
    FeatureModel, Feature, Relation, Constraint, Attribute, Domain, Range
)
from flamapy.core.models.ast import AST, ASTOperation, Node
from fm_generator.FMGenerator.models.config import Params

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
        else:
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
    attr_dicts = params.ATTRIBUTES_LIST

    for attr in attr_dicts:
        name = attr.get("name")
        type_ = attr.get("type", "").strip().lower()
        value = attr.get("value")
        min_value = attr.get("min_value")
        max_value = attr.get("max_value")
        attach_prob = attr.get("attach_probability", 1.0)  # Por defecto 1.0 (seguro se añade)

        if type_ == "boolean":
            domain_values = value
            if not isinstance(domain_values, list):
                if domain_values in [True, False]:
                    domain_values = [domain_values]
                elif isinstance(domain_values, str):
                    v = domain_values.strip().lower()
                    if v == "true":
                        domain_values = [True]
                    elif v == "false":
                        domain_values = [False]
                    else:
                        domain_values = [True, False]
                else:
                    domain_values = [True, False]
            domain = Domain(ranges=None, elements=domain_values)
            def gen_default():
                return random.choice(domain_values)

        elif type_ == "integer":
            try:
                min_v = int(min_value)
            except Exception:
                min_v = 0
            try:
                max_v = int(max_value)
            except Exception:
                max_v = 10
            domain = Domain(ranges=[Range(min_v, max_v)], elements=None)
            def gen_default():
                return random.randint(min_v, max_v)

        elif type_ == "real":
            try:
                min_v = float(min_value)
            except Exception:
                min_v = 0.0
            try:
                max_v = float(max_value)
            except Exception:
                max_v = 1.0
            domain = Domain(ranges=[Range(min_v, max_v)], elements=None)
            def gen_default():
                return round(random.uniform(min_v, max_v), 3)

        elif type_ == "string":
            try:
                min_len = int(min_value)
            except Exception:
                min_len = 1
            try:
                max_len = int(max_value)
            except Exception:
                max_len = 10
            domain = Domain(ranges=[Range(min_len, max_len)], elements=None)
            def gen_default():
                length = random.randint(min_len, max_len)
                letters = string.ascii_letters + string.digits
                return ''.join(random.choices(letters, k=length))

        else:
            continue

        for feature in features:
            if random.random() < float(attach_prob):
                default = gen_default()
                attribute = Attribute(name=name, domain=domain, default_value=default)
                attribute.set_parent(feature)
                feature.add_attribute(attribute)




def select_relation_types(params: Params, total: int) -> list[str]:
    return random.choices(
        population=['mand', 'opt', 'alt', 'or', 'group'],
        weights=[
            params.DIST_MANDATORY,
            params.DIST_OPTIONAL,
            params.DIST_ALTERNATIVE,
            params.DIST_OR,
            params.DIST_GROUP_CARDINALITY
        ],
        k=total
    )

def determine_group_size(pool_size: int, params: Params) -> int:
    return random.randint(1, min(params.GROUP_CARDINALITY_MAX, pool_size))

def create_relation(parent: Feature, children: list[Feature], rel_kind: str, params: Params) -> Relation:
    size = len(children)
    if rel_kind == 'mand': # Revisar
        return Relation(parent=parent, children=children, card_min=size, card_max=size)
    if rel_kind == 'opt':
        if size == 1: # Revisar
            return Relation(parent=parent, children=children, card_min=0, card_max=1)
        else:
            return Relation(parent=parent, children=children, card_min=0, card_max=size)
    if rel_kind == 'alt':
        return Relation(parent=parent, children=children, card_min=1, card_max=1)
    if rel_kind == 'or':
        return Relation(parent=parent, children=children, card_min=1, card_max=size)

    # group cardinality
    min_bound = max(params.GROUP_CARDINALITY_MIN, 1)
    max_bound = size
    if min_bound > max_bound:
        min_bound = max_bound
    card_min = random.randint(min_bound, max_bound)
    card_max = random.randint(card_min, max_bound)

    return Relation(parent=parent, children=children, card_min=card_min, card_max=card_max)

def add_relations_to_level(parents: list[Feature], children: list[Feature], params: Params) -> None:
    total = len(children)
    rel_types = select_relation_types(params, total)
    random.shuffle(rel_types)
    pool = children[:]
    parent_idx = 0
    for rel_kind in rel_types:
        if not pool:
            break
        parent = parents[parent_idx % len(parents)]
        parent_idx += 1
        size = determine_group_size(len(pool), params)
        group = [pool.pop() for _ in range(size)]
        rel = create_relation(parent, group, rel_kind, params)
        parent.add_relation(rel)
        for child in group:
            child.parent = parent

def generate_hierarchy(params: Params) -> tuple[FeatureModel, list[Feature]]:
    root = Feature(name="F0")
    fm = FeatureModel(root=root)
    numFeats = random.randint(params.MIN_FEATURES, params.MAX_FEATURES)
    names = [f"F{i+1}" for i in range(numFeats)]
    features = [Feature(name=n) for n in names]
    levels = {0: [root]}
    idx = 0
    total = 0
    max_depth = params.MAX_TREE_DEPTH

    for depth in range(1, max_depth + 1):
        remaining = numFeats - total
        if remaining <= 0:
            break
        parents = levels.get(depth - 1, [])
        if not parents:
            break
        levels_left = max_depth - depth + 1
        level_count = max(1, remaining // levels_left)
        if depth == max_depth:
            level_count = remaining
        level_feats = features[idx: idx + level_count]
        levels[depth] = level_feats
        idx += level_count
        total += level_count
        add_relations_to_level(parents, level_feats, params)

    connected = {f.name for f in fm.get_features()}
    return fm, [f for f in features if f.name in connected]



def add_constraints(fm: FeatureModel, features: list[Feature], params: Params) -> None:
    # Recopilar todos los attributes presentes en el FM y que son usables en constraints
    attrs_bool = []
    attrs_num = []
    attrs_str = []

    for feat in features:
        for attr in getattr(feat, "attributes", []):
            # Buscar en la lista de attributes manuales si está marcado como usable en constraints
            if hasattr(params, "ATTRIBUTES_LIST"):
                for attr_dict in params.ATTRIBUTES_LIST:
                    if (attr_dict.get("name") == attr.name 
                        and attr_dict.get("use_in_constraints", False)
                        and feat.name and attr.name):
                        t = attr_dict.get("type", "").lower()
                        if t == "boolean":
                            attrs_bool.append((feat, attr))
                        elif t == "integer" or t == "real":
                            attrs_num.append((feat, attr))
                        elif t == "string":
                            attrs_str.append((feat, attr))
                        break

    # Siempre pueden usarse features booleanas clásicas
    feats_bool = [f for f in features if hasattr(f, "attributes") and not getattr(f, "attributes", [])]
    feats_bool += [f for f in features if getattr(f, "attributes", []) and all(a.name.lower() != "enabled" for a in f.attributes)]

    # --- NUEVO: contadores de apariciones
    max_reps = getattr(params, "EXTRA_CONSTRAINT_REPRESENTATIVENESS", 1)
    appear_counts = {}  # key: str (feature o feature.attr), value: count

    def can_add(key):
        return appear_counts.get(key, 0) < max_reps

    def inc(key):
        appear_counts[key] = appear_counts.get(key, 0) + 1

    total_ctcs = random.randint(params.MIN_CONSTRAINTS, params.MAX_CONSTRAINTS)
    for i in range(total_ctcs):
        # Elige el tipo de constraint: bool, numérica, string
        types_avail = []
        if len(attrs_bool) + len(feats_bool) >= 2:
            types_avail.append("bool")
        if len(attrs_num) >= 2:
            types_avail.append("num")
        if len(attrs_str) >= 2:
            types_avail.append("string")

        if not types_avail:
            break  # No se puede hacer nada

        constraint_type = random.choice(types_avail)

        if constraint_type == "bool":
            # Features y attributes booleanos se pueden combinar
            pool = [(f.name,) for f in feats_bool] + [(f.name, a.name) for f, a in attrs_bool]
            # --- Filtrar según representativeness
            valid = [tpl for tpl in pool if can_add(".".join(tpl))]
            if len(valid) < 2:
                continue
            left_ids, right_ids = random.sample(valid, 2)
            def id_to_str(tpl):
                if len(tpl) == 1:
                    return tpl[0]
                else:
                    return f"{tpl[0]}.{tpl[1]}"
            left_key = id_to_str(left_ids)
            right_key = id_to_str(right_ids)
            left = Node(left_key)
            right = Node(right_key)
            op = random.choice([ASTOperation.IMPLIES, ASTOperation.AND, ASTOperation.OR, ASTOperation.EQUIVALENCE])
            if random.random() < params.PROB_NOT:
                left = Node(ASTOperation.NOT, left)
            if random.random() < params.PROB_NOT:
                right = Node(ASTOperation.NOT, right)
            root = Node(op, left, right)
            fm.ctcs.append(Constraint(name=f"ctc{i}", ast=AST(root)))
            inc(left_key)
            inc(right_key)

        elif constraint_type == "num":
            pool = [(f.name, a.name) for f, a in attrs_num]
            # --- Filtrar según representativeness
            valid = [tpl for tpl in pool if can_add(f"{tpl[0]}.{tpl[1]}")]
            if len(valid) < 4:
                continue
            selected = random.sample(valid, 4)
            (f1, a1), (f2, a2), (f3, a3), (f4, a4) = selected
            left_key = f"{f1}.{a1}"
            right_key = f"{f2}.{a2}"
            left = Node(left_key)
            right = Node(right_key)
            # Operadores aritméticos y comparadores
            arithmetic_ops = [ASTOperation.ADD, ASTOperation.SUB, ASTOperation.MUL, ASTOperation.DIV]
            cmp_ops = [ASTOperation.EQUALS, ASTOperation.GREATER, ASTOperation.LOWER, ASTOperation.GREATER_EQUALS, ASTOperation.LOWER_EQUALS]
            op1 = random.choice(arithmetic_ops)
            op2 = random.choice(arithmetic_ops)
            cmp_op = random.choice(cmp_ops)
            expr_left = Node(op1, left, right)
            third_key = f"{f3}.{a3}"
            fourth_key = f"{f4}.{a4}"
            expr_right = Node(op2, Node(third_key), Node(fourth_key))
            root = Node(cmp_op, expr_left, expr_right)
            fm.ctcs.append(Constraint(name=f"ctc{i}", ast=AST(root)))
            inc(left_key)
            inc(right_key)
            inc(third_key)
            inc(fourth_key)

        elif constraint_type == "string":
            pool = [(f.name, a.name) for f, a in attrs_str]
            valid = [tpl for tpl in pool if can_add(f"{tpl[0]}.{tpl[1]}")]
            if len(valid) < 2:
                continue
            (f1, a1), (f2, a2) = random.sample(valid, 2)
            left_key = f"{f1}.{a1}"
            right_key = f"{f2}.{a2}"
            left = Node(left_key)
            right = Node(right_key)
            root = Node(ASTOperation.EQUALS, left, right)
            fm.ctcs.append(Constraint(name=f"ctc{i}", ast=AST(root)))
            inc(left_key)
            inc(right_key)




def generate_single_model(params: Params, index: int) -> FeatureModel:
    random.seed(params.SEED + index)
    fm, feats = generate_hierarchy(params)
    if params.RANDOM_ATTRIBUTES:
        generate_random_attributes(params, feats)
    else:
        assign_manual_attributes(params, feats)
    add_constraints(fm, feats, params)
    return fm
