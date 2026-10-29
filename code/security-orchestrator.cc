// COMNET_INTERFACE_IMPLEMENTATION
#include "comnet/security-orchestrator.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace comnet {
namespace {

constexpr double kWeightTolerance = 1.0e-12;

void
ValidateNormalized(const double value,
                   const char* message)
{
    if (!std::isfinite(value) ||
        value < 0.0 ||
        value > 1.0)
    {
        throw std::invalid_argument(message);
    }
}

bool
IsStateValid(const SecurityState state) noexcept
{
    switch (state)
    {
    case SecurityState::NORMAL:
    case SecurityState::ELEVATED:
    case SecurityState::CRITICAL:
    case SecurityState::RECOVERY:
        return true;
    }

    return false;
}

std::uint32_t
IncrementRecoveryCounter(const std::uint32_t value) noexcept
{
    if (value == std::numeric_limits<std::uint32_t>::max())
    {
        return value;
    }

    return value + 1;
}

}  // namespace

std::string_view
SecurityOrchestrator::ComponentName() noexcept
{
    return "SecurityOrchestrator";
}

std::string_view
SecurityOrchestrator::ToString(const SecurityState value) noexcept
{
    switch (value)
    {
    case SecurityState::NORMAL:
        return "NORMAL";
    case SecurityState::ELEVATED:
        return "ELEVATED";
    case SecurityState::CRITICAL:
        return "CRITICAL";
    case SecurityState::RECOVERY:
        return "RECOVERY";
    }

    return "UNKNOWN_SECURITY_STATE";
}

std::string_view
SecurityOrchestrator::ToString(const FilteringPosture value) noexcept
{
    switch (value)
    {
    case FilteringPosture::AUTHENTICATION_REJECTION_ONLY:
        return "AUTHENTICATION_REJECTION_ONLY";
    case FilteringPosture::SOURCE_TOKEN_BUCKET:
        return "SOURCE_TOKEN_BUCKET";
    case FilteringPosture::QUARANTINE_AND_STRICT_TOKEN_BUCKET:
        return "QUARANTINE_AND_STRICT_TOKEN_BUCKET";
    case FilteringPosture::CONSERVATIVE_RESIDUAL_FILTERING:
        return "CONSERVATIVE_RESIDUAL_FILTERING";
    }

    return "UNKNOWN_FILTERING_POSTURE";
}

std::string_view
SecurityOrchestrator::ToString(const TrafficTreatment value) noexcept
{
    switch (value)
    {
    case TrafficTreatment::NORMAL_SCHEDULING:
        return "NORMAL_SCHEDULING";
    case TrafficTreatment::SECURITY_CONTROL_PRIORITY:
        return "SECURITY_CONTROL_PRIORITY";
    case TrafficTreatment::HIGHEST_CONTROL_PRIORITY:
        return "HIGHEST_CONTROL_PRIORITY";
    case TrafficTreatment::ELEVATED_PRIORITY:
        return "ELEVATED_PRIORITY";
    }

    return "UNKNOWN_TRAFFIC_TREATMENT";
}

std::string_view
SecurityOrchestrator::ToString(const EdgeResponse value) noexcept
{
    switch (value)
    {
    case EdgeResponse::PRIMARY_MEC:
        return "PRIMARY_MEC";
    case EdgeResponse::PREPARE_ALTERNATE_MEC:
        return "PREPARE_ALTERNATE_MEC";
    case EdgeResponse::REROUTE_ELIGIBLE_FLOWS:
        return "REROUTE_ELIGIBLE_FLOWS";
    case EdgeResponse::HYSTERESIS_GATED_RETURN_TO_PRIMARY:
        return "HYSTERESIS_GATED_RETURN_TO_PRIMARY";
    }

    return "UNKNOWN_EDGE_RESPONSE";
}

void
SecurityOrchestrator::ValidateObservation(
    const OrchestratorObservation& observation)
{
    ValidateNormalized(
        observation.ddosProbability,
        "DDoS probability must be finite and in [0, 1]");
    ValidateNormalized(
        observation.authenticationFailureRate,
        "authentication failure rate must be finite and in [0, 1]");
    ValidateNormalized(
        observation.edgeAnomalyScore,
        "edge anomaly score must be finite and in [0, 1]");
    ValidateNormalized(
        observation.queuePressure,
        "queue pressure must be finite and in [0, 1]");
    ValidateNormalized(
        observation.latencyPressure,
        "latency pressure must be finite and in [0, 1]");
    ValidateNormalized(
        observation.securityProcessingPressure,
        "security-processing pressure must be finite and in [0, 1]");
}

void
SecurityOrchestrator::ValidateWeights(const RiskWeights& weights)
{
    ValidateNormalized(
        weights.ddosWeight,
        "DDoS risk weight must be finite and in [0, 1]");
    ValidateNormalized(
        weights.authenticationWeight,
        "authentication risk weight must be finite and in [0, 1]");
    ValidateNormalized(
        weights.edgeWeight,
        "edge risk weight must be finite and in [0, 1]");

    const double total =
        weights.ddosWeight +
        weights.authenticationWeight +
        weights.edgeWeight;

    if (!std::isfinite(total) ||
        std::fabs(total - 1.0) > kWeightTolerance)
    {
        throw std::invalid_argument(
            "risk weights must sum to one");
    }
}

void
SecurityOrchestrator::ValidateThresholds(
    const OrchestratorThresholds& thresholds)
{
    ValidateNormalized(
        thresholds.recoveryRiskMaximum,
        "recovery risk maximum must be finite and in [0, 1]");
    ValidateNormalized(
        thresholds.elevatedRiskThreshold,
        "elevated risk threshold must be finite and in [0, 1]");
    ValidateNormalized(
        thresholds.criticalRiskThreshold,
        "critical risk threshold must be finite and in [0, 1]");
    ValidateNormalized(
        thresholds.recoveryPressureMaximum,
        "recovery pressure maximum must be finite and in [0, 1]");
    ValidateNormalized(
        thresholds.elevatedPressureThreshold,
        "elevated pressure threshold must be finite and in [0, 1]");
    ValidateNormalized(
        thresholds.criticalPressureThreshold,
        "critical pressure threshold must be finite and in [0, 1]");

    if (!(thresholds.recoveryRiskMaximum <
              thresholds.elevatedRiskThreshold &&
          thresholds.elevatedRiskThreshold <
              thresholds.criticalRiskThreshold))
    {
        throw std::invalid_argument(
            "risk thresholds must satisfy "
            "recovery < elevated < critical");
    }

    if (!(thresholds.recoveryPressureMaximum <
              thresholds.elevatedPressureThreshold &&
          thresholds.elevatedPressureThreshold <
              thresholds.criticalPressureThreshold))
    {
        throw std::invalid_argument(
            "pressure thresholds must satisfy "
            "recovery < elevated < critical");
    }

    if (thresholds.recoveryConsecutiveWindows == 0)
    {
        throw std::invalid_argument(
            "recovery hysteresis requires at least one window");
    }
}

void
SecurityOrchestrator::ValidateMemory(
    const OrchestratorMemory& memory,
    const OrchestratorThresholds& thresholds)
{
    ValidateThresholds(thresholds);

    if (!IsStateValid(memory.state))
    {
        throw std::invalid_argument(
            "security state is invalid");
    }

    if (memory.state != SecurityState::RECOVERY &&
        memory.belowRecoveryThresholdWindows != 0)
    {
        throw std::invalid_argument(
            "non-recovery states must have a zero recovery counter");
    }

    if (memory.state == SecurityState::RECOVERY &&
        memory.belowRecoveryThresholdWindows >=
            thresholds.recoveryConsecutiveWindows)
    {
        throw std::invalid_argument(
            "recovery counter must be below the return-to-normal threshold");
    }
}

double
SecurityOrchestrator::RiskScore(
    const OrchestratorObservation& observation,
    const RiskWeights& weights)
{
    ValidateObservation(observation);
    ValidateWeights(weights);

    const double score =
        weights.ddosWeight * observation.ddosProbability +
        weights.authenticationWeight *
            observation.authenticationFailureRate +
        weights.edgeWeight * observation.edgeAnomalyScore;

    if (!std::isfinite(score))
    {
        throw std::overflow_error(
            "risk score is not finite");
    }

    return std::clamp(score, 0.0, 1.0);
}

double
SecurityOrchestrator::PressureScore(
    const OrchestratorObservation& observation)
{
    ValidateObservation(observation);

    return std::max(
        {
            observation.queuePressure,
            observation.latencyPressure,
            observation.securityProcessingPressure,
        });
}

OrchestratorDecision
SecurityOrchestrator::Advance(
    const OrchestratorMemory& memory,
    const OrchestratorObservation& observation,
    const RiskWeights& weights,
    const OrchestratorThresholds& thresholds)
{
    ValidateMemory(memory, thresholds);

    const double risk = RiskScore(observation, weights);
    const double pressure = PressureScore(observation);

    const bool critical =
        risk >= thresholds.criticalRiskThreshold ||
        pressure >= thresholds.criticalPressureThreshold;

    const bool elevated =
        risk >= thresholds.elevatedRiskThreshold ||
        pressure >= thresholds.elevatedPressureThreshold;

    const bool belowRecovery =
        risk <= thresholds.recoveryRiskMaximum &&
        pressure <= thresholds.recoveryPressureMaximum;

    SecurityState nextState = memory.state;
    std::uint32_t nextCounter = 0;

    switch (memory.state)
    {
    case SecurityState::NORMAL:
        if (critical)
        {
            nextState = SecurityState::CRITICAL;
        }
        else if (elevated)
        {
            nextState = SecurityState::ELEVATED;
        }
        else
        {
            nextState = SecurityState::NORMAL;
        }
        break;

    case SecurityState::ELEVATED:
        if (critical)
        {
            nextState = SecurityState::CRITICAL;
        }
        else if (elevated)
        {
            nextState = SecurityState::ELEVATED;
        }
        else if (belowRecovery &&
                 thresholds.recoveryConsecutiveWindows == 1U)
        {
            nextState = SecurityState::NORMAL;
        }
        else
        {
            nextState = SecurityState::RECOVERY;
            nextCounter = belowRecovery ? 1U : 0U;
        }
        break;

    case SecurityState::CRITICAL:
        if (critical)
        {
            nextState = SecurityState::CRITICAL;
        }
        else if (elevated)
        {
            nextState = SecurityState::ELEVATED;
        }
        else if (belowRecovery &&
                 thresholds.recoveryConsecutiveWindows == 1U)
        {
            nextState = SecurityState::NORMAL;
        }
        else
        {
            nextState = SecurityState::RECOVERY;
            nextCounter = belowRecovery ? 1U : 0U;
        }
        break;

    case SecurityState::RECOVERY:
        if (critical)
        {
            nextState = SecurityState::CRITICAL;
        }
        else if (elevated)
        {
            nextState = SecurityState::ELEVATED;
        }
        else if (belowRecovery)
        {
            const std::uint32_t candidateCounter =
                IncrementRecoveryCounter(
                    memory.belowRecoveryThresholdWindows);

            if (candidateCounter >=
                thresholds.recoveryConsecutiveWindows)
            {
                nextState = SecurityState::NORMAL;
                nextCounter = 0;
            }
            else
            {
                nextState = SecurityState::RECOVERY;
                nextCounter = candidateCounter;
            }
        }
        else
        {
            nextState = SecurityState::RECOVERY;
            nextCounter = 0;
        }
        break;
    }

    return {
        nextState,
        nextCounter,
        risk,
        pressure,
        nextState != memory.state,
    };
}

SecurityActionProfile
SecurityOrchestrator::ActionProfile(const SecurityState state)
{
    switch (state)
    {
    case SecurityState::NORMAL:
        return {
            1.0,
            FilteringPosture::AUTHENTICATION_REJECTION_ONLY,
            TrafficTreatment::NORMAL_SCHEDULING,
            EdgeResponse::PRIMARY_MEC,
        };

    case SecurityState::ELEVATED:
        return {
            0.5,
            FilteringPosture::SOURCE_TOKEN_BUCKET,
            TrafficTreatment::SECURITY_CONTROL_PRIORITY,
            EdgeResponse::PREPARE_ALTERNATE_MEC,
        };

    case SecurityState::CRITICAL:
        return {
            0.25,
            FilteringPosture::QUARANTINE_AND_STRICT_TOKEN_BUCKET,
            TrafficTreatment::HIGHEST_CONTROL_PRIORITY,
            EdgeResponse::REROUTE_ELIGIBLE_FLOWS,
        };

    case SecurityState::RECOVERY:
        return {
            0.5,
            FilteringPosture::CONSERVATIVE_RESIDUAL_FILTERING,
            TrafficTreatment::ELEVATED_PRIORITY,
            EdgeResponse::HYSTERESIS_GATED_RETURN_TO_PRIMARY,
        };
    }

    throw std::invalid_argument(
        "security state is invalid");
}

}  // namespace comnet
