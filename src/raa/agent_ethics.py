"""Syllabus-aligned agent architecture and ethics specification for Risk-Aware Abstention."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskEnvironment:
    """Formal PEAS task environment description in the Russell & Norvig AI framework."""

    performance_measure: str
    environment: str
    actuators: str
    sensors: str
    observability: str
    determinism: str
    episodicity: str
    dynamism: str
    continuity: str


@dataclass(frozen=True)
class AgentArchitecture:
    """Formal agent classification and mathematical decision policy specification."""

    agent_type: str
    internal_state: tuple[str, ...]
    percept_sequence: tuple[str, ...]
    action_space: tuple[str, ...]
    utility_function: str
    decision_policy: str


@dataclass(frozen=True)
class EthicsPerspective:
    """Analysis of agent choices through a classical normative ethical theory."""

    framework_name: str
    core_principle: str
    agent_manifestation: str
    concrete_tradeoff: str
    regulatory_clinical_alignment: str


def get_task_environment() -> TaskEnvironment:
    """Return the formal PEAS specification for the RAA decision agent."""
    return TaskEnvironment(
        performance_measure=(
            "Expected multi-objective clinical utility: maximize true positive detection; "
            "heavily penalize false negatives (asymmetric clinical loss); minimize unneeded "
            "human review workload while preserving human reviewer cognitive capacity; "
            "strictly penalize dishonest or ungrounded certainty."
        ),
        environment=(
            "Semi-structured clinical screening environment. Biopsy histopathology is not "
            "directly observed at imaging intake. Patient records arrive asynchronously with "
            "varying completeness and measurement noise."
        ),
        actuators=(
            "Tripartite routing actuator: emits discrete action in {Automatic, Assisted, "
            "Human Review}; dual explanation emitter (class rationale + route risk breakdown); "
            "immutable audit record emitter."
        ),
        sensors=(
            "Structured clinical feature sensors: patient scan age (continuous), mass shape "
            "(categorical), mass margin (categorical), tissue density (ordinal), plus missingness "
            "masks and range validation flags."
        ),
        observability=(
            "Partially observable (latent histology and malignancy state cannot be directly "
            "sensed)."
        ),
        determinism=(
            "Stochastic (biological variability, inter-observer report ambiguity, "
            "random forest ensembles)."
        ),
        episodicity=(
            "Episodic (each patient mammogram evaluation constitutes an independent episode)."
        ),
        dynamism=("Static during single-case evaluation; semidynamic across population drift."),
        continuity=(
            "Continuous percept state (age, probabilities) mapped into a discrete action space."
        ),
    )


def get_agent_architecture() -> AgentArchitecture:
    """Return formal specification of the agent as a utility-based decision agent."""
    return AgentArchitecture(
        agent_type="Utility-Based Decision Agent with Epistemic State Estimation",
        internal_state=(
            "Posterior class distribution: P(malignant | x)",
            "Predictive uncertainty / ensemble disagreement: U(x) from bootstrap variance",
            "Data novelty / unusualness: A(x) from Isolation Forest score",
            "Asymmetric clinical consequence: C(x) reflecting cost of potential diagnostic error",
            "Composite risk metric: R(x) = 0.5*U + 0.2*A + 0.3*C",
            "Empirical threshold calibrators: (t_automatic, t_assisted) from validation "
            "percentiles",
        ),
        percept_sequence=(
            "Feature vector x in R^d",
            "Missingness indicator mask m in {0, 1}^d",
            "Historical validation risk quantile distribution",
        ),
        action_space=("Automatic", "Assisted", "Human Review"),
        utility_function=(
            "U(action, y, y_hat, x) = -Risk(x, action), where Risk balances asymmetric clinical "
            "loss L_clinical(y, y_hat) with cognitive human review cost C_review(action)."
        ),
        decision_policy=(
            "pi(x) = 'Automatic' if R(x) <= t_automatic else "
            "('Assisted' if R(x) <= t_assisted else 'Human Review'). "
            "Epistemic override: if any feature is missing (m_i = 1), pi(x) forces 'Human Review'."
        ),
    )


def get_ethics_perspectives() -> dict[str, EthicsPerspective]:
    """Return tripartite ethical analyses: Utilitarian, Deontological, and Virtue Ethics."""
    return {
        "utilitarian": EthicsPerspective(
            framework_name="Utilitarianism (Consequentialist Ethics)",
            core_principle=(
                "Actions are morally right in proportion as they tend to promote overall "
                "well-being, minimizing net societal suffering and clinical harm."
            ),
            agent_manifestation=(
                "The agent's objective function explicitly operationalizes asymmetric clinical "
                "consequence: missing a malignant tumor (false negative) causes severe health "
                "deterioration or death, so predicting benign receives a high consequence penalty "
                "(C=1.0) compared to predicting malignant (C=0.4). Furthermore, human reviewer "
                "capacity is treated as a scarce resource; indiscriminate referral causes "
                "radiologist burnout and patient queues, so the agent automates low-risk "
                "predictions (R <= t_auto) to preserve expert bandwidth."
            ),
            concrete_tradeoff=(
                "Weighing the catastrophic harm of an unreviewed false negative against the "
                "collective harm of clinical exhaustion and delayed treatment for other patients."
            ),
            regulatory_clinical_alignment=(
                "Aligns with cost-benefit health economic evaluations, NICE decision thresholds, "
                "and clinical triaging guidelines in oncology."
            ),
        ),
        "deontological": EthicsPerspective(
            framework_name="Deontology (Duty-Based Ethics)",
            core_principle=(
                "Actions are morally mandatory or forbidden by fundamental duties and rules, "
                "independent of their consequences. Human autonomy and truthfulness are inviolable."
            ),
            agent_manifestation=(
                "1. Duty of Epistemic Honesty: The system has a strict duty never to convey "
                "certainty when it is uncertain. It explicitly exposes model disagreement (U) "
                "and anomaly (A), forbidding deceptive overconfidence. "
                "2. Duty of Non-Usurpation and Scope Integrity: The agent must not practice "
                "medicine autonomously without clinical licensure. It classifies inputs into "
                "non-diagnostic estimates and routes decisions rather than diagnosing a patient. "
                "3. Duty of Non-Deception: Natural language reports are forbidden from using "
                "diagnostic declaratives ('you have cancer') or confabulated assertions."
            ),
            concrete_tradeoff=(
                "Even if an overconfident prediction would statistically placate an anxious "
                "patient, the agent is duty-bound to report uncertainty honestly and mandate "
                "human oversight."
            ),
            regulatory_clinical_alignment=(
                "Aligns with EU AI Act Article 13 (Transparency and provision of information to "
                "users), FDA Good Machine Learning Practice, and the GMC Duty of Candour."
            ),
        ),
        "virtue_ethics": EthicsPerspective(
            framework_name="Virtue Ethics (Character and Practical Wisdom)",
            core_principle=(
                "Moral behavior stems from cultivating virtues such as phronesis (practical "
                "wisdom), temperance, intellectual humility, and diligence."
            ),
            agent_manifestation=(
                "1. Intellectual Humility (Epistemic Self-Knowledge): The agent recognizes the "
                "boundaries of its training distribution. When an input is unusual or missing, it "
                "exercises restraint by abstaining rather than making reckless guesses. "
                "2. Prudence (Phronesis): Balancing confidence against conservative validation "
                "thresholds (p70/p90) rather than maximizing reckless raw throughput. "
                "3. Diligence and Integrity: Enforcing rule checkers, fidelity tests, and stable "
                "explanations before presenting results to human stakeholders."
            ),
            concrete_tradeoff=(
                "Resisting the temptation of intellectual hubris (claiming universal predictive "
                "power) in favor of transparent epistemic modesty."
            ),
            regulatory_clinical_alignment=(
                "Reflects the medical virtue ethics tradition of the Hippocratic Oath, clinical "
                "humility, and shared clinician-patient decision making."
            ),
        ),
    }


def format_agent_ethics_summary() -> dict[str, Any]:
    """Return a serializable dictionary containing the full agent and ethics analysis."""
    env = get_task_environment()
    arch = get_agent_architecture()
    ethics = get_ethics_perspectives()
    return {
        "task_environment": {
            "performance_measure": env.performance_measure,
            "environment": env.environment,
            "actuators": env.actuators,
            "sensors": env.sensors,
            "properties": {
                "observability": env.observability,
                "determinism": env.determinism,
                "episodicity": env.episodicity,
                "dynamism": env.dynamism,
                "continuity": env.continuity,
            },
        },
        "agent_architecture": {
            "type": arch.agent_type,
            "internal_state": list(arch.internal_state),
            "percept_sequence": list(arch.percept_sequence),
            "action_space": list(arch.action_space),
            "utility_function": arch.utility_function,
            "decision_policy": arch.decision_policy,
        },
        "ethics_frameworks": {
            key: {
                "name": item.framework_name,
                "principle": item.core_principle,
                "manifestation": item.agent_manifestation,
                "tradeoff": item.concrete_tradeoff,
                "alignment": item.regulatory_clinical_alignment,
            }
            for key, item in ethics.items()
        },
    }
