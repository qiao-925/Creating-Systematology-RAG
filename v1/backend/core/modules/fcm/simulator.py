"""Systematology FCM simulator: Kosko iteration for FCM state convergence.

Uses NumPy directly (fcmpy has tqdm version conflict).
Convergence threshold: |Δstate| < 1e-6.
"""

from __future__ import annotations

import numpy as np

from backend.core.models import SharedCLD, WeightedFCM
from backend.infrastructure.logger import get_logger

logger = get_logger("systematology.fcm.simulator")

DEFAULT_MAX_ITERATIONS = 100
DEFAULT_CONVERGENCE_THRESHOLD = 1e-6


def run_simulation(
    weighted_fcm: WeightedFCM,
    shared_cld: SharedCLD | None = None,
    initial_state: list[float] | None = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    convergence_threshold: float = DEFAULT_CONVERGENCE_THRESHOLD,
) -> list[float]:
    """Run Kosko FCM simulation until convergence.

    Kosko update rule: state(t+1) = sigmoid(W^T @ state(t))
    where sigmoid(x) = 1 / (1 + exp(-x))

    Args:
        weighted_fcm: The WeightedFCM with weight matrix.
        shared_cld: Optional SharedCLD for node labels (diagnostics only).
        initial_state: Initial activation state (defaults to baseline_state).
        max_iterations: Maximum iterations before giving up.
        convergence_threshold: Convergence threshold for |Δstate|.

    Returns:
        Final state vector.

    Raises:
        RuntimeError: If simulation doesn't converge within max_iterations.
    """
    W = np.array(weighted_fcm.weight_matrix)
    n = W.shape[0]

    if initial_state is not None:
        state = np.array(initial_state, dtype=float)
    else:
        state = np.array(weighted_fcm.baseline_state, dtype=float)

    if len(state) != n:
        raise ValueError(f"State length {len(state)} doesn't match matrix size {n}")

    for iteration in range(max_iterations):
        # Kosko update: new_state = sigmoid(W^T @ state)
        new_state = _sigmoid(W.T @ state)

        # Check convergence
        delta = np.linalg.norm(new_state - state)
        state = new_state

        if delta < convergence_threshold:
            logger.info(
                "FCM simulation converged",
                iterations=iteration + 1,
                final_delta=delta,
            )
            return state.tolist()

    raise RuntimeError(
        f"FCM simulation did not converge after {max_iterations} iterations. "
        f"Final delta: {delta:.2e}"
    )


def _sigmoid(x: np.ndarray) -> np.ndarray:
    """Sigmoid activation function: 1 / (1 + exp(-x))."""
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def run_scenario_comparison(
    weighted_fcm: WeightedFCM,
    scenarios: dict[str, list[float]],
    shared_cld: SharedCLD | None = None,
) -> dict[str, list[float]]:
    """Run multiple intervention scenarios and compare results.

    Args:
        weighted_fcm: The WeightedFCM to simulate.
        scenarios: Dict mapping scenario name to initial state override.
        shared_cld: Optional SharedCLD for diagnostics.

    Returns:
        Dict mapping scenario name to final state vector.
    """
    results: dict[str, list[float]] = {}

    # Baseline
    baseline = run_simulation(weighted_fcm, shared_cld)
    results["baseline"] = baseline

    # Each scenario
    for name, initial_state in scenarios.items():
        try:
            result = run_simulation(weighted_fcm, shared_cld, initial_state=initial_state)
            results[name] = result
        except RuntimeError as exc:
            logger.warning("Scenario failed", scenario=name, error=str(exc))
            results[name] = baseline  # Fallback to baseline

    return results
