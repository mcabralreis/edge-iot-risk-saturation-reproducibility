#include "comnet/security-orchestrator.h"

#include <cmath>
#include <cstdint>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string_view>

namespace {

std::uint64_t positiveChecks = 0;
std::uint64_t negativeCases = 0;

void
Check(const bool condition,
      const char* message)
{
    if (!condition)
    {
        throw std::runtime_error(message);
    }

    ++positiveChecks;
}

template <typename Function>
void
ExpectInvalid(Function&& function,
              const char* message)
{
    bool rejected = false;

    try
    {
        function();
    }
    catch (const std::invalid_argument&)
    {
        rejected = true;
    }

    if (!rejected)
    {
        throw std::runtime_error(message);
    }

    ++negativeCases;
}

bool
NearlyEqual(const double left,
            const double right)
{
    return std::fabs(left - right) <= 1.0e-12;
}

void
SetObservationField(comnet::OrchestratorObservation& observation,
                    const std::size_t index,
                    const double value)
{
    switch (index)
    {
    case 0:
        observation.ddosProbability = value;
        return;
    case 1:
        observation.authenticationFailureRate = value;
        return;
    case 2:
        observation.edgeAnomalyScore = value;
        return;
    case 3:
        observation.queuePressure = value;
        return;
    case 4:
        observation.latencyPressure = value;
        return;
    case 5:
        observation.securityProcessingPressure = value;
        return;
    }

    throw std::logic_error("invalid observation field index");
}

void
SetWeightField(comnet::RiskWeights& weights,
               const std::size_t index,
               const double value)
{
    switch (index)
    {
    case 0:
        weights.ddosWeight = value;
        return;
    case 1:
        weights.authenticationWeight = value;
        return;
    case 2:
        weights.edgeWeight = value;
        return;
    }

    throw std::logic_error("invalid weight field index");
}

void
SetThresholdField(comnet::OrchestratorThresholds& thresholds,
                  const std::size_t index,
                  const double value)
{
    switch (index)
    {
    case 0:
        thresholds.recoveryRiskMaximum = value;
        return;
    case 1:
        thresholds.elevatedRiskThreshold = value;
        return;
    case 2:
        thresholds.criticalRiskThreshold = value;
        return;
    case 3:
        thresholds.recoveryPressureMaximum = value;
        return;
    case 4:
        thresholds.elevatedPressureThreshold = value;
        return;
    case 5:
        thresholds.criticalPressureThreshold = value;
        return;
    }

    throw std::logic_error("invalid threshold field index");
}

}  // namespace

int
main()
{
    try
    {
        using comnet::EdgeResponse;
        using comnet::FilteringPosture;
        using comnet::OrchestratorMemory;
        using comnet::OrchestratorObservation;
        using comnet::OrchestratorThresholds;
        using comnet::RiskWeights;
        using comnet::SecurityOrchestrator;
        using comnet::SecurityState;
        using comnet::TrafficTreatment;

        Check(
            SecurityOrchestrator::ComponentName() ==
                "SecurityOrchestrator",
            "component name mismatch");

        Check(
            SecurityOrchestrator::ToString(SecurityState::NORMAL) ==
                "NORMAL",
            "NORMAL string mismatch");
        Check(
            SecurityOrchestrator::ToString(SecurityState::ELEVATED) ==
                "ELEVATED",
            "ELEVATED string mismatch");
        Check(
            SecurityOrchestrator::ToString(SecurityState::CRITICAL) ==
                "CRITICAL",
            "CRITICAL string mismatch");
        Check(
            SecurityOrchestrator::ToString(SecurityState::RECOVERY) ==
                "RECOVERY",
            "RECOVERY string mismatch");

        Check(
            SecurityOrchestrator::ToString(
                FilteringPosture::AUTHENTICATION_REJECTION_ONLY) ==
                "AUTHENTICATION_REJECTION_ONLY",
            "normal filtering string mismatch");
        Check(
            SecurityOrchestrator::ToString(
                FilteringPosture::SOURCE_TOKEN_BUCKET) ==
                "SOURCE_TOKEN_BUCKET",
            "elevated filtering string mismatch");
        Check(
            SecurityOrchestrator::ToString(
                FilteringPosture::QUARANTINE_AND_STRICT_TOKEN_BUCKET) ==
                "QUARANTINE_AND_STRICT_TOKEN_BUCKET",
            "critical filtering string mismatch");
        Check(
            SecurityOrchestrator::ToString(
                FilteringPosture::CONSERVATIVE_RESIDUAL_FILTERING) ==
                "CONSERVATIVE_RESIDUAL_FILTERING",
            "recovery filtering string mismatch");

        Check(
            SecurityOrchestrator::ToString(
                TrafficTreatment::NORMAL_SCHEDULING) ==
                "NORMAL_SCHEDULING",
            "normal traffic string mismatch");
        Check(
            SecurityOrchestrator::ToString(
                TrafficTreatment::SECURITY_CONTROL_PRIORITY) ==
                "SECURITY_CONTROL_PRIORITY",
            "elevated traffic string mismatch");
        Check(
            SecurityOrchestrator::ToString(
                TrafficTreatment::HIGHEST_CONTROL_PRIORITY) ==
                "HIGHEST_CONTROL_PRIORITY",
            "critical traffic string mismatch");
        Check(
            SecurityOrchestrator::ToString(
                TrafficTreatment::ELEVATED_PRIORITY) ==
                "ELEVATED_PRIORITY",
            "recovery traffic string mismatch");

        Check(
            SecurityOrchestrator::ToString(
                EdgeResponse::PRIMARY_MEC) ==
                "PRIMARY_MEC",
            "normal edge string mismatch");
        Check(
            SecurityOrchestrator::ToString(
                EdgeResponse::PREPARE_ALTERNATE_MEC) ==
                "PREPARE_ALTERNATE_MEC",
            "elevated edge string mismatch");
        Check(
            SecurityOrchestrator::ToString(
                EdgeResponse::REROUTE_ELIGIBLE_FLOWS) ==
                "REROUTE_ELIGIBLE_FLOWS",
            "critical edge string mismatch");
        Check(
            SecurityOrchestrator::ToString(
                EdgeResponse::HYSTERESIS_GATED_RETURN_TO_PRIMARY) ==
                "HYSTERESIS_GATED_RETURN_TO_PRIMARY",
            "recovery edge string mismatch");

        const RiskWeights weights = {0.50, 0.30, 0.20};
        const OrchestratorThresholds thresholds = {
            0.20, 0.45, 0.75,
            0.25, 0.55, 0.85,
            3,
        };

        const OrchestratorObservation low = {
            0.10, 0.20, 0.30,
            0.10, 0.20, 0.30,
        };
        const OrchestratorObservation elevatedRisk = {
            0.80, 0.60, 0.00,
            0.10, 0.10, 0.10,
        };
        const OrchestratorObservation criticalPressure = {
            0.10, 0.10, 0.10,
            0.20, 0.90, 0.20,
        };
        const OrchestratorObservation intermediateRecovery = {
            0.30, 0.30, 0.30,
            0.30, 0.30, 0.30,
        };

        Check(
            NearlyEqual(
                SecurityOrchestrator::RiskScore(low, weights),
                0.17),
            "risk score mismatch");

        Check(
            NearlyEqual(
                SecurityOrchestrator::PressureScore(low),
                0.30),
            "pressure score mismatch");

        const auto normalDecision =
            SecurityOrchestrator::Advance(
                {SecurityState::NORMAL, 0},
                low,
                weights,
                thresholds);

        Check(
            normalDecision.state == SecurityState::NORMAL,
            "NORMAL should remain NORMAL");
        Check(
            !normalDecision.stateChanged,
            "unchanged NORMAL decision marked changed");
        Check(
            NearlyEqual(normalDecision.riskScore, 0.17),
            "decision risk mismatch");
        Check(
            NearlyEqual(normalDecision.pressureScore, 0.30),
            "decision pressure mismatch");

        const auto elevatedDecision =
            SecurityOrchestrator::Advance(
                {SecurityState::NORMAL, 0},
                elevatedRisk,
                weights,
                thresholds);

        Check(
            elevatedDecision.state == SecurityState::ELEVATED,
            "NORMAL did not enter ELEVATED");
        Check(
            elevatedDecision.stateChanged,
            "ELEVATED transition not marked changed");

        const auto criticalDecision =
            SecurityOrchestrator::Advance(
                {SecurityState::NORMAL, 0},
                criticalPressure,
                weights,
                thresholds);

        Check(
            criticalDecision.state == SecurityState::CRITICAL,
            "NORMAL did not enter CRITICAL");
        Check(
            criticalDecision.stateChanged,
            "CRITICAL transition not marked changed");

        const auto criticalDowngrade =
            SecurityOrchestrator::Advance(
                {SecurityState::CRITICAL, 0},
                elevatedRisk,
                weights,
                thresholds);

        Check(
            criticalDowngrade.state == SecurityState::ELEVATED,
            "CRITICAL did not downgrade to ELEVATED");

        const auto recoveryOne =
            SecurityOrchestrator::Advance(
                {SecurityState::ELEVATED, 0},
                {0.10, 0.10, 0.10, 0.10, 0.10, 0.10},
                weights,
                thresholds);

        Check(
            recoveryOne.state == SecurityState::RECOVERY,
            "ELEVATED did not enter RECOVERY");
        Check(
            recoveryOne.belowRecoveryThresholdWindows == 1,
            "first recovery count mismatch");

        const auto recoveryTwo =
            SecurityOrchestrator::Advance(
                {
                    recoveryOne.state,
                    recoveryOne.belowRecoveryThresholdWindows,
                },
                {0.10, 0.10, 0.10, 0.10, 0.10, 0.10},
                weights,
                thresholds);

        Check(
            recoveryTwo.state == SecurityState::RECOVERY,
            "RECOVERY ended too early");
        Check(
            recoveryTwo.belowRecoveryThresholdWindows == 2,
            "second recovery count mismatch");

        const auto returnedNormal =
            SecurityOrchestrator::Advance(
                {
                    recoveryTwo.state,
                    recoveryTwo.belowRecoveryThresholdWindows,
                },
                {0.10, 0.10, 0.10, 0.10, 0.10, 0.10},
                weights,
                thresholds);

        Check(
            returnedNormal.state == SecurityState::NORMAL,
            "RECOVERY did not return to NORMAL");
        Check(
            returnedNormal.belowRecoveryThresholdWindows == 0,
            "NORMAL recovery counter mismatch");

        auto oneWindowThresholds = thresholds;
        oneWindowThresholds.recoveryConsecutiveWindows = 1;

        const auto oneWindowFromElevated =
            SecurityOrchestrator::Advance(
                {SecurityState::ELEVATED, 0},
                {0.10, 0.10, 0.10, 0.10, 0.10, 0.10},
                weights,
                oneWindowThresholds);

        Check(
            oneWindowFromElevated.state == SecurityState::NORMAL,
            "one-window recovery from ELEVATED did not return to NORMAL");
        Check(
            oneWindowFromElevated.belowRecoveryThresholdWindows == 0,
            "one-window recovery from ELEVATED returned an invalid counter");
        Check(
            oneWindowFromElevated.stateChanged,
            "one-window recovery from ELEVATED was not marked changed");

        SecurityOrchestrator::ValidateMemory(
            {
                oneWindowFromElevated.state,
                oneWindowFromElevated.belowRecoveryThresholdWindows,
            },
            oneWindowThresholds);

        const auto oneWindowFromCritical =
            SecurityOrchestrator::Advance(
                {SecurityState::CRITICAL, 0},
                {0.10, 0.10, 0.10, 0.10, 0.10, 0.10},
                weights,
                oneWindowThresholds);

        Check(
            oneWindowFromCritical.state == SecurityState::NORMAL,
            "one-window recovery from CRITICAL did not return to NORMAL");
        Check(
            oneWindowFromCritical.belowRecoveryThresholdWindows == 0,
            "one-window recovery from CRITICAL returned an invalid counter");
        Check(
            oneWindowFromCritical.stateChanged,
            "one-window recovery from CRITICAL was not marked changed");

        SecurityOrchestrator::ValidateMemory(
            {
                oneWindowFromCritical.state,
                oneWindowFromCritical.belowRecoveryThresholdWindows,
            },
            oneWindowThresholds);

        const auto recoveryReset =
            SecurityOrchestrator::Advance(
                {SecurityState::RECOVERY, 2},
                intermediateRecovery,
                weights,
                thresholds);

        Check(
            recoveryReset.state == SecurityState::RECOVERY,
            "intermediate recovery should remain RECOVERY");
        Check(
            recoveryReset.belowRecoveryThresholdWindows == 0,
            "intermediate recovery did not reset counter");

        const auto recoveryEscalation =
            SecurityOrchestrator::Advance(
                {SecurityState::RECOVERY, 1},
                elevatedRisk,
                weights,
                thresholds);

        Check(
            recoveryEscalation.state == SecurityState::ELEVATED,
            "RECOVERY did not re-escalate");

        const auto normalProfile =
            SecurityOrchestrator::ActionProfile(
                SecurityState::NORMAL);
        const auto elevatedProfile =
            SecurityOrchestrator::ActionProfile(
                SecurityState::ELEVATED);
        const auto criticalProfile =
            SecurityOrchestrator::ActionProfile(
                SecurityState::CRITICAL);
        const auto recoveryProfile =
            SecurityOrchestrator::ActionProfile(
                SecurityState::RECOVERY);

        Check(
            NearlyEqual(normalProfile.detectorCadenceSeconds, 1.0),
            "normal cadence mismatch");
        Check(
            normalProfile.filtering ==
                FilteringPosture::AUTHENTICATION_REJECTION_ONLY,
            "normal filtering mismatch");
        Check(
            normalProfile.trafficTreatment ==
                TrafficTreatment::NORMAL_SCHEDULING,
            "normal traffic treatment mismatch");
        Check(
            normalProfile.edgeResponse ==
                EdgeResponse::PRIMARY_MEC,
            "normal edge response mismatch");

        Check(
            NearlyEqual(elevatedProfile.detectorCadenceSeconds, 0.5),
            "elevated cadence mismatch");
        Check(
            elevatedProfile.filtering ==
                FilteringPosture::SOURCE_TOKEN_BUCKET,
            "elevated filtering mismatch");
        Check(
            elevatedProfile.trafficTreatment ==
                TrafficTreatment::SECURITY_CONTROL_PRIORITY,
            "elevated traffic treatment mismatch");
        Check(
            elevatedProfile.edgeResponse ==
                EdgeResponse::PREPARE_ALTERNATE_MEC,
            "elevated edge response mismatch");

        Check(
            NearlyEqual(criticalProfile.detectorCadenceSeconds, 0.25),
            "critical cadence mismatch");
        Check(
            criticalProfile.filtering ==
                FilteringPosture::QUARANTINE_AND_STRICT_TOKEN_BUCKET,
            "critical filtering mismatch");
        Check(
            criticalProfile.trafficTreatment ==
                TrafficTreatment::HIGHEST_CONTROL_PRIORITY,
            "critical traffic treatment mismatch");
        Check(
            criticalProfile.edgeResponse ==
                EdgeResponse::REROUTE_ELIGIBLE_FLOWS,
            "critical edge response mismatch");

        Check(
            NearlyEqual(recoveryProfile.detectorCadenceSeconds, 0.5),
            "recovery cadence mismatch");
        Check(
            recoveryProfile.filtering ==
                FilteringPosture::CONSERVATIVE_RESIDUAL_FILTERING,
            "recovery filtering mismatch");
        Check(
            recoveryProfile.trafficTreatment ==
                TrafficTreatment::ELEVATED_PRIORITY,
            "recovery traffic treatment mismatch");
        Check(
            recoveryProfile.edgeResponse ==
                EdgeResponse::HYSTERESIS_GATED_RETURN_TO_PRIMARY,
            "recovery edge response mismatch");

        const double nan =
            std::numeric_limits<double>::quiet_NaN();

        for (std::size_t index = 0; index < 6; ++index)
        {
            for (const double invalid : {nan, -0.01, 1.01})
            {
                ExpectInvalid(
                    [=]() {
                        auto observation = low;
                        SetObservationField(
                            observation,
                            index,
                            invalid);
                        SecurityOrchestrator::ValidateObservation(
                            observation);
                    },
                    "invalid observation accepted");
            }
        }

        for (std::size_t index = 0; index < 3; ++index)
        {
            for (const double invalid : {nan, -0.01, 1.01})
            {
                ExpectInvalid(
                    [=]() {
                        auto invalidWeights = weights;
                        SetWeightField(
                            invalidWeights,
                            index,
                            invalid);
                        SecurityOrchestrator::ValidateWeights(
                            invalidWeights);
                    },
                    "invalid weight accepted");
            }
        }

        ExpectInvalid(
            [&]() {
                SecurityOrchestrator::ValidateWeights(
                    {0.50, 0.30, 0.19});
            },
            "non-unit weight sum accepted");

        for (std::size_t index = 0; index < 6; ++index)
        {
            ExpectInvalid(
                [=]() {
                    auto invalidThresholds = thresholds;
                    SetThresholdField(
                        invalidThresholds,
                        index,
                        nan);
                    SecurityOrchestrator::ValidateThresholds(
                        invalidThresholds);
                },
                "non-finite threshold accepted");
        }

        ExpectInvalid(
            [&]() {
                auto invalid = thresholds;
                invalid.recoveryRiskMaximum =
                    invalid.elevatedRiskThreshold;
                SecurityOrchestrator::ValidateThresholds(invalid);
            },
            "equal recovery/elevated risk accepted");

        ExpectInvalid(
            [&]() {
                auto invalid = thresholds;
                invalid.elevatedRiskThreshold =
                    invalid.criticalRiskThreshold;
                SecurityOrchestrator::ValidateThresholds(invalid);
            },
            "equal elevated/critical risk accepted");

        ExpectInvalid(
            [&]() {
                auto invalid = thresholds;
                invalid.recoveryPressureMaximum =
                    invalid.elevatedPressureThreshold;
                SecurityOrchestrator::ValidateThresholds(invalid);
            },
            "equal recovery/elevated pressure accepted");

        ExpectInvalid(
            [&]() {
                auto invalid = thresholds;
                invalid.elevatedPressureThreshold =
                    invalid.criticalPressureThreshold;
                SecurityOrchestrator::ValidateThresholds(invalid);
            },
            "equal elevated/critical pressure accepted");

        ExpectInvalid(
            [&]() {
                auto invalid = thresholds;
                invalid.recoveryConsecutiveWindows = 0;
                SecurityOrchestrator::ValidateThresholds(invalid);
            },
            "zero recovery duration accepted");

        ExpectInvalid(
            [&]() {
                SecurityOrchestrator::ValidateMemory(
                    {
                        static_cast<SecurityState>(255),
                        0,
                    },
                    thresholds);
            },
            "invalid state accepted");

        ExpectInvalid(
            [&]() {
                SecurityOrchestrator::ValidateMemory(
                    {SecurityState::NORMAL, 1},
                    thresholds);
            },
            "NORMAL accepted a recovery counter");

        ExpectInvalid(
            [&]() {
                SecurityOrchestrator::ValidateMemory(
                    {SecurityState::ELEVATED, 1},
                    thresholds);
            },
            "ELEVATED accepted a recovery counter");

        ExpectInvalid(
            [&]() {
                SecurityOrchestrator::ValidateMemory(
                    {SecurityState::CRITICAL, 1},
                    thresholds);
            },
            "CRITICAL accepted a recovery counter");

        ExpectInvalid(
            [&]() {
                SecurityOrchestrator::ValidateMemory(
                    {SecurityState::RECOVERY, 3},
                    thresholds);
            },
            "terminal recovery counter accepted");

        ExpectInvalid(
            [&]() {
                static_cast<void>(
                    SecurityOrchestrator::ActionProfile(
                        static_cast<SecurityState>(255)));
            },
            "invalid action-profile state accepted");

        std::cout
            << "SecurityOrchestrator interface test: PASS\n"
            << "positive_checks=" << positiveChecks << '\n'
            << "negative_cases=" << negativeCases << '\n'
            << "one_window_recovery_boundary_cases=2\n"
            << "controller_parameters_calibrated=NO\n"
            << "policy_actuation_executed=NO\n"
            << "scientific_values_generated=NO"
            << std::endl;

        return 0;
    }
    catch (const std::exception& error)
    {
        std::cerr
            << "SecurityOrchestrator interface test failed: "
            << error.what()
            << std::endl;
        return 1;
    }
}
