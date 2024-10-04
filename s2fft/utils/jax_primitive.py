from functools import partial
from typing import Callable
from jax import core
from jax.interpreters import ad, batching, xla, mlir


def register_primitive(
    name: str,
    multiple_results: bool,
    abstract_evaluation: Callable,
    lowering_per_platform: dict[None | str, Callable],
    batcher: None | Callable = None,
    jacobian_vector_product: None | Callable = None,
    transpose: None | Callable = None,
):
    """Register a new custom JAX primitive.

    Args:
        name: Name for primitive.
        multiple_results: Whether primitive returns multiple values.
        abstract_evaluation: Abstract evaluation rule for primitive.
        lowering_per_platform: Dictionary mapping from platform names (or `None` for
            platform-independent) to lowering rules.
        batcher: Optional batched evaluation rule for primitive.
        jacobian_vector_product: Optional Jacobian vector product for primitive for
            forward-mode automatic differentiation.
        transpose: Optional rule for evaluation transpose rule for primitive for
            reverse-mode automatic differentiation.

    Returns:
        Registered custom primtive.
    """
    primitive = core.Primitive(name)
    primitive.multiple_results = multiple_results
    primitive.def_impl(partial(xla.apply_primitive, primitive))
    primitive.def_abstract_eval(abstract_evaluation)
    for platform, lowering in lowering_per_platform.items():
        mlir.register_lowering(primitive, lowering, platform=platform)
    if batcher is not None:
        batching.primitive_batchers[primitive] = batcher
    if jacobian_vector_product is not None:
        ad.primitive_jvps[primitive] = jacobian_vector_product
    if transpose is not None:
        ad.primitive_transposes[primitive] = transpose
    return primitive
