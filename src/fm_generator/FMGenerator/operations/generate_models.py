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
            min_len = 1
            max_len = 50

            domain = Domain(ranges=[Range(min_len, max_len)], elements=None)

            length = random.randint(min_len, max_len)
            letters = string.ascii_letters + string.digits
            default = ''.join(random.choices(letters, k=length))

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

def create_relation(parent: Feature, children: list[Feature], rel_kind: str, params: Params) -> list[Relation]:
    size = len(children)
    relations = []
    if rel_kind == 'mand':
        # Una relación mandatory por cada hijo
        for child in children:
            rel = Relation(parent=parent, children=[child], card_min=1, card_max=1)
            relations.append(rel)
    elif rel_kind == 'opt':
        # Una relación optional por cada hijo
        for child in children:
            rel = Relation(parent=parent, children=[child], card_min=0, card_max=1)
            relations.append(rel)
    elif rel_kind == 'alt':
        rel = Relation(parent=parent, children=children, card_min=1, card_max=1)
        relations.append(rel)
    elif rel_kind == 'or':
        rel = Relation(parent=parent, children=children, card_min=1, card_max=size)
        relations.append(rel)
    else:
        # group cardinality
        min_bound = max(params.GROUP_CARDINALITY_MIN, 1)
        max_bound = size
        if min_bound > max_bound:
            min_bound = max_bound
        card_min = random.randint(min_bound, max_bound)
        card_max = random.randint(card_min, max_bound)
        rel = Relation(parent=parent, children=children, card_min=card_min, card_max=card_max)
        relations.append(rel)
    return relations

def add_relations_to_level(parents: list[Feature], children: list[Feature], params: Params) -> None:
    total = len(children)
    rel_types = select_relation_types(params, total)
    random.shuffle(rel_types)
    pool = children[:]
    parent_idx = 0
    while pool:
        rel_kind = rel_types[parent_idx % len(rel_types)]
        parent = parents[parent_idx % len(parents)]
        parent_idx += 1
        size = determine_group_size(len(pool), params)
        group = [pool.pop() for _ in range(size)]
        relations = create_relation(parent, group, rel_kind, params)
        for rel in relations:
            parent.add_relation(rel)
            # Relación puede ser con uno o varios hijos (pero mand/opt siempre de uno en uno)
            for child in rel.children:
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
    # -----------------------------
    # Pools de variables disponibles
    # -----------------------------
    attrs_bool: list[tuple[Feature, Attribute]] = []
    attrs_num: list[tuple[Feature, Attribute]] = []
    attrs_str: list[tuple[Feature, Attribute]] = []

    # Attributes usables en constraints (solo manuales marcados use_in_constraints)
    for feat in features:
        for attr in getattr(feat, "attributes", []):
            if hasattr(params, "ATTRIBUTES_LIST"):
                for attr_dict in params.ATTRIBUTES_LIST:
                    if (
                        attr_dict.get("name") == attr.name
                        and attr_dict.get("use_in_constraints", False)
                        and feat.name and attr.name
                    ):
                        t = (attr_dict.get("type", "") or "").lower()
                        if t == "boolean":
                            attrs_bool.append((feat, attr))
                        elif t in ("integer", "real"):
                            if getattr(params, "ARITHMETIC_LEVEL", False):
                                attrs_num.append((feat, attr))
                        elif t == "string":
                            if (
                                getattr(params, "TYPE_LEVEL", False)
                                and getattr(params, "STRING_CONSTRAINTS", False)
                            ):
                                attrs_str.append((feat, attr))
                        break

    # Features booleanas “clásicas” (sin atributos)
    feats_bool = [f for f in features if not getattr(f, "attributes", [])]

    # -----------------------------
    # Params y caps
    # -----------------------------
    def to_even_up(n: int) -> int:
        return n if n % 2 == 0 else n + 1

    def to_even_down(n: int) -> int:
        return n if n % 2 == 0 else n - 1

    min_vars = int(getattr(params, "MIN_VARS_PER_CONSTRAINT", 1))
    max_vars = int(getattr(params, "MAX_VARS_PER_CONSTRAINT", 2))

    min_vars = max(2, min_vars)
    max_vars = max(2, max_vars)

    # Forzamos paridad: siempre siguiente par
    min_vars = to_even_up(min_vars)
    max_vars = to_even_up(max_vars)

    # Sin hard cap artificial
    if min_vars > max_vars:
        min_vars = max_vars

    # ECR: ahora es <= max_vars (clamp), mínimo 1
    max_reps = int(getattr(params, "EXTRA_CONSTRAINT_REPRESENTATIVENESS", 1))
    max_reps = max(1, max_reps)
    max_reps = min(max_reps, max_vars)

    # MAX_FEATURES del step2: lo usamos como máximo de FEATURES DISTINTAS por constraint
    max_features_param = int(getattr(params, "MAX_FEATURES", 10))
    max_features_param = max(1, max_features_param)

    # -----------------------------
    # Helpers de operaciones
    # -----------------------------
    def pick_bool_op() -> ASTOperation:
        ops = [ASTOperation.AND, ASTOperation.OR, ASTOperation.IMPLIES, ASTOperation.EQUIVALENCE]
        weights = [
            float(getattr(params, "PROB_AND", 0.7)),
            float(getattr(params, "PROB_OR_CT", 0.1)),
            float(getattr(params, "PROB_IMPLICATION", 0.1)),
            float(getattr(params, "PROB_EQUIVALENCE", 0.1)),
        ]
        return random.choices(ops, weights=weights, k=1)[0]

    def maybe_not(node: Node) -> Node:
        if random.random() < float(getattr(params, "PROB_NOT", 0.0)):
            return Node(ASTOperation.NOT, node)
        return node

    def build_left_deep_bool_ast(nodes: list[Node]) -> Node:
        """(((n1 op n2) op n3) op n4) ..."""
        assert len(nodes) >= 2
        cur = Node(pick_bool_op(), nodes[0], nodes[1])
        for n in nodes[2:]:
            cur = Node(pick_bool_op(), cur, n)
        return cur

    # -----------------------------
    # ECR es por FEATURE (no por key)
    # key: "F12" o "F12.attr"
    # feature_id = "F12"
    # -----------------------------
    def feature_id_from_key(key: str) -> str:
        return key.split(".", 1)[0]

    def group_keys_by_feature(keys: list[str]) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        for k in keys:
            fid = feature_id_from_key(k)
            groups.setdefault(fid, []).append(k)
        return groups

    def distinct_feature_cap(groups: dict[str, list[str]]) -> int:
        return min(len(groups), max_features_param)

    def max_occurrences_possible(groups: dict[str, list[str]]) -> int:
        """
        Con ECR, si eliges X features distintas, máximo apariciones = X * ECR.
        Pero X está limitado por MAX_FEATURES (step2) y por cuántas features haya.
        """
        df_cap = distinct_feature_cap(groups)
        return df_cap * max_reps

    def choose_target_occurrences(groups: dict[str, list[str]]) -> int | None:
        if not groups:
            return None

        max_by_ecr = max_occurrences_possible(groups)

        effective_max = min(max_vars, max_by_ecr)
        effective_max = to_even_down(effective_max)

        effective_min = to_even_up(min_vars)

        if effective_max < effective_min:
            return None

        # número de valores pares disponibles en el rango
        num_even_values = ((effective_max - effective_min) // 2) + 1
        offset = random.randint(0, num_even_values - 1)
        return effective_min + (2 * offset)

    def sample_keys_with_ecr(groups: dict[str, list[str]], target_occ: int) -> list[str] | None:
        """
        Devuelve una lista de keys de longitud target_occ.
        Permite repetir keys, pero restringe por feature_id a max_reps apariciones.
        Además limita el número de features distintas usadas por MAX_FEATURES (step2).
        """
        if target_occ < 2 or target_occ % 2 == 1:
            return None

        df_cap = distinct_feature_cap(groups)
        if df_cap <= 0:
            return None

        # nº mínimo de features distintas necesarias para alcanzar target_occ con ECR
        min_distinct_needed = (target_occ + max_reps - 1) // max_reps
        if min_distinct_needed > df_cap:
            return None

        all_fids = list(groups.keys())

        # elegimos EXACTAMENTE las necesarias (para maximizar ocurrencias con ECR)
        distinct_count = min(df_cap, max(1, min_distinct_needed))
        chosen_fids = random.sample(all_fids, distinct_count)

        counts = {fid: 0 for fid in chosen_fids}
        out: list[str] = []

        # round-robin hasta llenar target_occ
        while len(out) < target_occ:
            progressed = False
            for fid in chosen_fids:
                if len(out) >= target_occ:
                    break
                if counts[fid] < max_reps:
                    out.append(random.choice(groups[fid]))
                    counts[fid] += 1
                    progressed = True
            if not progressed:
                break

        if len(out) != target_occ:
            return None

        random.shuffle(out)
        return out

    # -----------------------------
    # Numeric helpers
    # -----------------------------
    def pick_binary_arith_op() -> ASTOperation:
        ops = [
            ASTOperation.ADD,
            ASTOperation.SUB,
            ASTOperation.MUL,
            ASTOperation.DIV,
        ]
        weights = [
            float(getattr(params, "PROB_SUM", 0.7)),
            float(getattr(params, "PROB_SUBSTRACT", 0.2)),
            float(getattr(params, "PROB_MULTIPLY", 0.1)),
            float(getattr(params, "PROB_DIVIDE", 0.0)),
        ]
        return random.choices(ops, weights=weights, k=1)[0]

    def pick_cmp_op() -> ASTOperation:
        ops = [
            ASTOperation.EQUALS,
            ASTOperation.LOWER,
            ASTOperation.GREATER,
            ASTOperation.LOWER_EQUALS,
            ASTOperation.GREATER_EQUALS,
        ]
        weights = [
            float(getattr(params, "PROB_EQUALS", 0.1)),
            float(getattr(params, "PROB_LESS", 0.2)),
            float(getattr(params, "PROB_GREATER", 0.7)),
            float(getattr(params, "PROB_LESS_EQUALS", 0.0)),
            float(getattr(params, "PROB_GREATER_EQUALS", 0.0)),
        ]
        return random.choices(ops, weights=weights, k=1)[0]

    def pick_aggregate_name() -> str | None:
        if not getattr(params, "AGGREGATE_FUNCTIONS", False):
            return None

        prob_sum_function = float(getattr(params, "PROB_SUM_FUNCTION", 0.0))
        prob_avg_function = float(getattr(params, "PROB_AVG_FUNCTION", 0.0))

        total = prob_sum_function + prob_avg_function
        if total <= 0.0:
            return None

        names = ["sum", "avg"]
        weights = [prob_sum_function, prob_avg_function]
        return random.choices(names, weights=weights, k=1)[0]


    def build_function_node(func_name: str, keys: list[str]) -> Node:
        args = ", ".join(keys)
        return Node(f"{func_name}({args})")

    def build_plain_arith_expr(keys: list[str]) -> Node:
        cur = Node(keys[0])
        for k in keys[1:]:
            cur = Node(pick_binary_arith_op(), cur, Node(k))
        return cur

    def maybe_wrap_with_aggregate(expr: Node, keys: list[str]) -> Node:
        if not getattr(params, "AGGREGATE_FUNCTIONS", False):
            return expr

        # Solo tiene sentido aplicar aggregates si hay al menos 2 refs
        if len(keys) < 2:
            return expr

        prob_basic = (
            float(getattr(params, "PROB_SUM", 0.0)) +
            float(getattr(params, "PROB_SUBSTRACT", 0.0)) +
            float(getattr(params, "PROB_MULTIPLY", 0.0)) +
            float(getattr(params, "PROB_DIVIDE", 0.0))
        )
        prob_agg = (
            float(getattr(params, "PROB_SUM_FUNCTION", 0.0)) +
            float(getattr(params, "PROB_AVG_FUNCTION", 0.0))
        )

        total = prob_basic + prob_agg
        if total <= 0.0:
            return expr

        use_aggregate = random.random() < (prob_agg / total)
        if not use_aggregate:
            return expr

        agg_name = pick_aggregate_name()
        if agg_name is None:
            return expr

        return build_function_node(agg_name, keys)

    def build_arith_expr(keys: list[str]) -> Node:
        expr = build_plain_arith_expr(keys)
        expr = maybe_wrap_with_aggregate(expr, keys)
        return expr
    # -----------------------------
    # Generación de constraints
    # -----------------------------
    total_ctcs = random.randint(params.MIN_CONSTRAINTS, params.MAX_CONSTRAINTS)

    for i in range(total_ctcs):
        bool_pool = [f.name for f in feats_bool] + [f"{f.name}.{a.name}" for f, a in attrs_bool]
        num_pool = [f"{f.name}.{a.name}" for f, a in attrs_num]
        str_pool = [f"{f.name}.{a.name}" for f, a in attrs_str]

        bool_groups = group_keys_by_feature(list(set(bool_pool)))
        num_groups = group_keys_by_feature(list(set(num_pool)))
        str_groups = group_keys_by_feature(list(set(str_pool)))

        candidates: list[str] = []
        t_bool = choose_target_occurrences(bool_groups)
        if t_bool is not None:
            candidates.append("bool")

        t_num = choose_target_occurrences(num_groups)
        if t_num is not None:
            candidates.append("num")

        # string: también usamos choose_target_occurrences, pero requiere par (ya lo es)
        t_str = choose_target_occurrences(str_groups)
        if t_str is not None:
            candidates.append("string")

        if not candidates:
            # No hay manera de cumplir min_vars para ningún tipo => no generes una pequeña
            continue

        constraint_type = random.choice(candidates)

        # -----------------------------
        # BOOLEAN: N literales (N = target_occ)
        # -----------------------------
        if constraint_type == "bool":
            target_occ = choose_target_occurrences(bool_groups)
            if target_occ is None:
                continue

            chosen_keys = sample_keys_with_ecr(bool_groups, target_occ)
            if not chosen_keys:
                continue

            literals = [maybe_not(Node(k)) for k in chosen_keys]
            root = build_left_deep_bool_ast(literals)
            fm.ctcs.append(Constraint(name=f"ctc{i}", ast=AST(root)))

        # -----------------------------
        # NUMERIC: N refs totales (leafs) repartidas en left/right
        # Forma: (expr_left) <cmp> (expr_right)
        # -----------------------------
        elif constraint_type == "num":
            target_occ = choose_target_occurrences(num_groups)
            if target_occ is None:
                continue

            chosen_keys = sample_keys_with_ecr(num_groups, target_occ)
            if not chosen_keys:
                continue

            # split equilibrado, al menos 1 y 1
            split = len(chosen_keys) // 2
            left_keys = chosen_keys[:split]
            right_keys = chosen_keys[split:]
            if not left_keys or not right_keys:
                continue

            expr_left = build_arith_expr(left_keys)
            expr_right = build_arith_expr(right_keys)
            root = Node(pick_cmp_op(), expr_left, expr_right)
            fm.ctcs.append(Constraint(name=f"ctc{i}", ast=AST(root)))

        # -----------------------------
        # STRING: igualdades (k0==k1), (k2==k3)... combinadas
        # target_occ refs totales (PAR)
        # -----------------------------
        elif constraint_type == "string":
            target_occ = choose_target_occurrences(str_groups)
            if target_occ is None:
                continue

            chosen_keys = sample_keys_with_ecr(str_groups, target_occ)
            if not chosen_keys:
                continue

            eq_nodes: list[Node] = []
            for j in range(0, len(chosen_keys) - 1, 2):
                eq_nodes.append(Node(ASTOperation.EQUALS, Node(chosen_keys[j]), Node(chosen_keys[j + 1])))

            if len(eq_nodes) == 1:
                root = eq_nodes[0]
            else:
                root = build_left_deep_bool_ast(eq_nodes)

            fm.ctcs.append(Constraint(name=f"ctc{i}", ast=AST(root)))




def generate_single_model(params: Params, index: int) -> FeatureModel:
    random.seed(params.SEED + index)
    fm, feats = generate_hierarchy(params)
    if params.RANDOM_ATTRIBUTES:
        generate_random_attributes(params, feats)
    else:
        assign_manual_attributes(params, feats)
    add_constraints(fm, feats, params)
    return fm
