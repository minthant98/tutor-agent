"""Pure Mathematics syllabus topic lists for version 2026.1.

Source: Edexcel 9MA0 spec + Cambridge 9709 syllabus, distilled to topic IDs
the engine uses for mastery tracking + readiness calculation.
"""

SYLLABUS_VERSION = "2026.1"

EDEXCEL_9MA0_TOPICS: list[dict] = [
    {"topic_id": "algebra_indices_surds", "topic_name": "Algebra: indices and surds", "parent_topic_id": None, "ordinal": 1},
    {"topic_id": "algebra_quadratics", "topic_name": "Quadratics", "parent_topic_id": None, "ordinal": 2},
    {"topic_id": "algebra_inequalities", "topic_name": "Inequalities", "parent_topic_id": None, "ordinal": 3},
    {"topic_id": "algebra_polynomials", "topic_name": "Polynomials", "parent_topic_id": None, "ordinal": 4},
    {"topic_id": "algebra_graphs_transformations", "topic_name": "Graphs and transformations", "parent_topic_id": None, "ordinal": 5},
    {"topic_id": "coordinate_geometry_straight_lines", "topic_name": "Straight lines", "parent_topic_id": None, "ordinal": 6},
    {"topic_id": "coordinate_geometry_circles", "topic_name": "Circles", "parent_topic_id": None, "ordinal": 7},
    {"topic_id": "trigonometry_ratios", "topic_name": "Trigonometric ratios and identities", "parent_topic_id": None, "ordinal": 8},
    {"topic_id": "trigonometry_equations", "topic_name": "Trigonometric equations", "parent_topic_id": None, "ordinal": 9},
    {"topic_id": "exponentials_logarithms", "topic_name": "Exponentials and logarithms", "parent_topic_id": None, "ordinal": 10},
    {"topic_id": "differentiation_basics", "topic_name": "Differentiation: first principles and rules", "parent_topic_id": None, "ordinal": 11},
    {"topic_id": "differentiation_applications", "topic_name": "Differentiation applications (tangents, stationary points)", "parent_topic_id": None, "ordinal": 12},
    {"topic_id": "differentiation_chain_product_quotient", "topic_name": "Chain, product, quotient rules", "parent_topic_id": None, "ordinal": 13},
    {"topic_id": "integration_basics", "topic_name": "Integration: indefinite and definite", "parent_topic_id": None, "ordinal": 14},
    {"topic_id": "integration_substitution_parts", "topic_name": "Integration by substitution and by parts", "parent_topic_id": None, "ordinal": 15},
    {"topic_id": "integration_area", "topic_name": "Integration: area under curve", "parent_topic_id": None, "ordinal": 16},
    {"topic_id": "sequences_series", "topic_name": "Sequences and series", "parent_topic_id": None, "ordinal": 17},
    {"topic_id": "binomial_expansion", "topic_name": "Binomial expansion", "parent_topic_id": None, "ordinal": 18},
    {"topic_id": "functions", "topic_name": "Functions and inverse functions", "parent_topic_id": None, "ordinal": 19},
    {"topic_id": "vectors_2d_3d", "topic_name": "Vectors (2D and 3D)", "parent_topic_id": None, "ordinal": 20},
    {"topic_id": "numerical_methods", "topic_name": "Numerical methods", "parent_topic_id": None, "ordinal": 21},
    {"topic_id": "proof", "topic_name": "Proof (direct, contradiction, induction)", "parent_topic_id": None, "ordinal": 22},
]

CAMBRIDGE_9709_TOPICS: list[dict] = [
    {"topic_id": "algebra_quadratics", "topic_name": "Quadratics", "parent_topic_id": None, "ordinal": 1},
    {"topic_id": "algebra_functions", "topic_name": "Functions", "parent_topic_id": None, "ordinal": 2},
    {"topic_id": "coordinate_geometry", "topic_name": "Coordinate geometry", "parent_topic_id": None, "ordinal": 3},
    {"topic_id": "circular_measure", "topic_name": "Circular measure (radians)", "parent_topic_id": None, "ordinal": 4},
    {"topic_id": "trigonometry", "topic_name": "Trigonometry", "parent_topic_id": None, "ordinal": 5},
    {"topic_id": "series_binomial", "topic_name": "Series and binomial expansion", "parent_topic_id": None, "ordinal": 6},
    {"topic_id": "differentiation", "topic_name": "Differentiation", "parent_topic_id": None, "ordinal": 7},
    {"topic_id": "integration", "topic_name": "Integration", "parent_topic_id": None, "ordinal": 8},
    {"topic_id": "algebra_polynomials_partial_fractions", "topic_name": "Polynomials and partial fractions", "parent_topic_id": None, "ordinal": 9},
    {"topic_id": "logarithmic_exponential", "topic_name": "Logarithmic and exponential functions", "parent_topic_id": None, "ordinal": 10},
    {"topic_id": "trigonometry_advanced", "topic_name": "Trigonometry (advanced)", "parent_topic_id": None, "ordinal": 11},
    {"topic_id": "differentiation_advanced", "topic_name": "Differentiation (advanced rules + implicit + parametric)", "parent_topic_id": None, "ordinal": 12},
    {"topic_id": "integration_advanced", "topic_name": "Integration (advanced techniques)", "parent_topic_id": None, "ordinal": 13},
    {"topic_id": "numerical_solution_equations", "topic_name": "Numerical solution of equations", "parent_topic_id": None, "ordinal": 14},
    {"topic_id": "vectors", "topic_name": "Vectors", "parent_topic_id": None, "ordinal": 15},
    {"topic_id": "differential_equations", "topic_name": "Differential equations", "parent_topic_id": None, "ordinal": 16},
    {"topic_id": "complex_numbers", "topic_name": "Complex numbers", "parent_topic_id": None, "ordinal": 17},
]
