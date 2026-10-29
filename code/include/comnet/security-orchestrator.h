// COMNET_INTERFACE_IMPLEMENTATION
// Component: SecurityOrchestrator
// Responsibility: Deterministic finite-state transition and action-profile interface with externally calibrated controller parameters
// Ground-truth access: NO
#pragma once

#include "contracts.h"

#include <cstdint>
#include <string_view>

namespace comnet {

enum class FilteringPosture {
    AUTHENTICATION_REJECTION_ONLY,
    SOURCE_TOKEN_BUCKET,
    QUARANTINE_AND_STRICT_TOKEN_BUCKET,
    CONSERVATIVE_RESIDUAL_FILTERING
};

enum class TrafficTreatment {
    NORMAL_SCHEDULING,
    SECURITY_CONTROL_PRIORITY,
    HIGHEST_CONTROL_PRIORITY,
    ELEVATED_PRIORITY
};

enum class EdgeResponse {
    PRIMARY_MEC,
    PREPARE_ALTERNATE_MEC,
    REROUTE_ELIGIBLE_FLOWS,
    HYSTERESIS_GATED_RETURN_TO_PRIMARY
};

struct OrchestratorObservation final {
    double ddosProbability{0.0};
    double authenticationFailureRate{0.0};
    double edgeAnomalyScore{0.0};
    double queuePressure{0.0};
    double latencyPressure{0.0};
    double securityProcessingPressure{0.0};
};

struct RiskWeights final {
    double ddosWeight{0.0};
    double authenticationWeight{0.0};
    double edgeWeight{0.0};
};

struct OrchestratorThresholds final {
    double recoveryRiskMaximum{0.0};
    double elevatedRiskThreshold{0.0};
    double criticalRiskThreshold{0.0};
    double recoveryPressureMaximum{0.0};
    double elevatedPressureThreshold{0.0};
    double criticalPressureThreshold{0.0};
    std::uint32_t recoveryConsecutiveWindows{0};
};

struct OrchestratorMemory final {
    SecurityState state{SecurityState::NORMAL};
    std::uint32_t belowRecoveryThresholdWindows{0};
};

struct OrchestratorDecision final {
    SecurityState state{SecurityState::NORMAL};
    std::uint32_t belowRecoveryThresholdWindows{0};
    double riskScore{0.0};
    double pressureScore{0.0};
    bool stateChanged{false};
};

struct SecurityActionProfile final {
    double detectorCadenceSeconds{0.0};
    FilteringPosture filtering{
        FilteringPosture::AUTHENTICATION_REJECTION_ONLY};
    TrafficTreatment trafficTreatment{
        TrafficTreatment::NORMAL_SCHEDULING};
    EdgeResponse edgeResponse{EdgeResponse::PRIMARY_MEC};
};

class SecurityOrchestrator final {
  public:
    SecurityOrchestrator() = delete;

    static constexpr bool kImplemented = true;

    static std::string_view ComponentName() noexcept;
    static std::string_view ToString(SecurityState value) noexcept;
    static std::string_view ToString(FilteringPosture value) noexcept;
    static std::string_view ToString(TrafficTreatment value) noexcept;
    static std::string_view ToString(EdgeResponse value) noexcept;

    static void ValidateObservation(
        const OrchestratorObservation& observation);

    static void ValidateWeights(const RiskWeights& weights);

    static void ValidateThresholds(
        const OrchestratorThresholds& thresholds);

    static void ValidateMemory(
        const OrchestratorMemory& memory,
        const OrchestratorThresholds& thresholds);

    static double RiskScore(
        const OrchestratorObservation& observation,
        const RiskWeights& weights);

    static double PressureScore(
        const OrchestratorObservation& observation);

    static OrchestratorDecision Advance(
        const OrchestratorMemory& memory,
        const OrchestratorObservation& observation,
        const RiskWeights& weights,
        const OrchestratorThresholds& thresholds);

    static SecurityActionProfile ActionProfile(SecurityState state);
};

}  // namespace comnet
