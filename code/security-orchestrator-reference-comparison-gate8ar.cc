#include "comnet/security-orchestrator.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <stdexcept>

namespace {

bool
NearlyEqual(const double left,
            const double right)
{
    return std::fabs(left - right) <= 1.0e-12;
}

struct ReferenceDecision final {
    comnet::SecurityState state;
    std::uint32_t counter;
};

ReferenceDecision
ReferenceAdvance(
    const comnet::OrchestratorMemory& memory,
    const double risk,
    const double pressure,
    const comnet::OrchestratorThresholds& thresholds)
{
    const bool critical =
        risk >= thresholds.criticalRiskThreshold ||
        pressure >= thresholds.criticalPressureThreshold;

    const bool elevated =
        risk >= thresholds.elevatedRiskThreshold ||
        pressure >= thresholds.elevatedPressureThreshold;

    const bool belowRecovery =
        risk <= thresholds.recoveryRiskMaximum &&
        pressure <= thresholds.recoveryPressureMaximum;

    switch (memory.state)
    {
    case comnet::SecurityState::NORMAL:
        if (critical)
        {
            return {comnet::SecurityState::CRITICAL, 0};
        }
        if (elevated)
        {
            return {comnet::SecurityState::ELEVATED, 0};
        }
        return {comnet::SecurityState::NORMAL, 0};

    case comnet::SecurityState::ELEVATED:
        if (critical)
        {
            return {comnet::SecurityState::CRITICAL, 0};
        }
        if (elevated)
        {
            return {comnet::SecurityState::ELEVATED, 0};
        }
        if (belowRecovery &&
            thresholds.recoveryConsecutiveWindows == 1U)
        {
            return {comnet::SecurityState::NORMAL, 0};
        }
        return {
            comnet::SecurityState::RECOVERY,
            belowRecovery ? 1U : 0U,
        };

    case comnet::SecurityState::CRITICAL:
        if (critical)
        {
            return {comnet::SecurityState::CRITICAL, 0};
        }
        if (elevated)
        {
            return {comnet::SecurityState::ELEVATED, 0};
        }
        if (belowRecovery &&
            thresholds.recoveryConsecutiveWindows == 1U)
        {
            return {comnet::SecurityState::NORMAL, 0};
        }
        return {
            comnet::SecurityState::RECOVERY,
            belowRecovery ? 1U : 0U,
        };

    case comnet::SecurityState::RECOVERY:
        if (critical)
        {
            return {comnet::SecurityState::CRITICAL, 0};
        }
        if (elevated)
        {
            return {comnet::SecurityState::ELEVATED, 0};
        }
        if (!belowRecovery)
        {
            return {comnet::SecurityState::RECOVERY, 0};
        }

        {
            const std::uint32_t next =
                memory.belowRecoveryThresholdWindows + 1U;

            if (next >= thresholds.recoveryConsecutiveWindows)
            {
                return {comnet::SecurityState::NORMAL, 0};
            }

            return {comnet::SecurityState::RECOVERY, next};
        }
    }

    throw std::runtime_error("invalid reference state");
}

std::uint64_t
Next(std::uint64_t& state)
{
    state = state * 6364136223846793005ULL +
        1442695040888963407ULL;
    return state;
}

double
Ratio(std::uint64_t& state)
{
    return static_cast<double>(Next(state) % 1000001ULL) /
        1000000.0;
}

}  // namespace

int
main()
{
    try
    {
        const comnet::RiskWeights weights = {
            0.50,
            0.30,
            0.20,
        };

        const comnet::OrchestratorThresholds thresholds = {
            0.20, 0.45, 0.75,
            0.25, 0.55, 0.85,
            5,
        };

        constexpr std::uint64_t riskCases = 500001;
        constexpr std::uint64_t pressureCases = 500001;
        constexpr std::uint64_t transitionCases = 400000;

        for (std::uint64_t index = 0;
             index < riskCases;
             ++index)
        {
            const double ddos =
                static_cast<double>(index % 1001ULL) / 1000.0;
            const double auth =
                static_cast<double>((index * 17ULL) % 1001ULL) /
                1000.0;
            const double edge =
                static_cast<double>((index * 29ULL) % 1001ULL) /
                1000.0;

            const comnet::OrchestratorObservation observation = {
                ddos, auth, edge, 0.0, 0.0, 0.0,
            };

            const double reference =
                0.50 * ddos +
                0.30 * auth +
                0.20 * edge;

            const double actual =
                comnet::SecurityOrchestrator::RiskScore(
                    observation,
                    weights);

            if (!NearlyEqual(actual, reference))
            {
                throw std::runtime_error(
                    "risk reference mismatch");
            }
        }

        for (std::uint64_t index = 0;
             index < pressureCases;
             ++index)
        {
            const double queue =
                static_cast<double>(index % 1001ULL) / 1000.0;
            const double latency =
                static_cast<double>((index * 31ULL) % 1001ULL) /
                1000.0;
            const double security =
                static_cast<double>((index * 43ULL) % 1001ULL) /
                1000.0;

            const comnet::OrchestratorObservation observation = {
                0.0, 0.0, 0.0,
                queue, latency, security,
            };

            const double reference =
                std::max({queue, latency, security});

            const double actual =
                comnet::SecurityOrchestrator::PressureScore(
                    observation);

            if (!NearlyEqual(actual, reference))
            {
                throw std::runtime_error(
                    "pressure reference mismatch");
            }
        }

        std::uint64_t randomState =
            0x5A17C3D429E8B601ULL;

        for (std::uint64_t index = 0;
             index < transitionCases;
             ++index)
        {
            auto caseThresholds = thresholds;
            caseThresholds.recoveryConsecutiveWindows =
                1U + static_cast<std::uint32_t>(
                    Next(randomState) % 7ULL);

            const auto stateValue =
                static_cast<comnet::SecurityState>(
                    Next(randomState) % 4ULL);

            const std::uint32_t counter =
                stateValue == comnet::SecurityState::RECOVERY
                    ? static_cast<std::uint32_t>(
                          Next(randomState) %
                          caseThresholds.recoveryConsecutiveWindows)
                    : 0U;

            const comnet::OrchestratorMemory memory = {
                stateValue,
                counter,
            };

            const comnet::OrchestratorObservation observation = {
                Ratio(randomState),
                Ratio(randomState),
                Ratio(randomState),
                Ratio(randomState),
                Ratio(randomState),
                Ratio(randomState),
            };

            const double risk =
                0.50 * observation.ddosProbability +
                0.30 * observation.authenticationFailureRate +
                0.20 * observation.edgeAnomalyScore;

            const double pressure =
                std::max(
                    {
                        observation.queuePressure,
                        observation.latencyPressure,
                        observation.securityProcessingPressure,
                    });

            const auto reference =
                ReferenceAdvance(
                    memory,
                    risk,
                    pressure,
                    caseThresholds);

            const auto actual =
                comnet::SecurityOrchestrator::Advance(
                    memory,
                    observation,
                    weights,
                    caseThresholds);

            if (actual.state != reference.state ||
                actual.belowRecoveryThresholdWindows !=
                    reference.counter ||
                !NearlyEqual(actual.riskScore, risk) ||
                !NearlyEqual(actual.pressureScore, pressure) ||
                actual.stateChanged !=
                    (reference.state != memory.state))
            {
                throw std::runtime_error(
                    "transition reference mismatch");
            }
        }

        const auto normal =
            comnet::SecurityOrchestrator::ActionProfile(
                comnet::SecurityState::NORMAL);
        const auto elevated =
            comnet::SecurityOrchestrator::ActionProfile(
                comnet::SecurityState::ELEVATED);
        const auto critical =
            comnet::SecurityOrchestrator::ActionProfile(
                comnet::SecurityState::CRITICAL);
        const auto recovery =
            comnet::SecurityOrchestrator::ActionProfile(
                comnet::SecurityState::RECOVERY);

        if (!NearlyEqual(normal.detectorCadenceSeconds, 1.0) ||
            !NearlyEqual(elevated.detectorCadenceSeconds, 0.5) ||
            !NearlyEqual(critical.detectorCadenceSeconds, 0.25) ||
            !NearlyEqual(recovery.detectorCadenceSeconds, 0.5))
        {
            throw std::runtime_error(
                "action-profile reference mismatch");
        }

        std::cout
            << "SecurityOrchestrator independent reference comparison: PASS\n"
            << "risk_cases=" << riskCases << '\n'
            << "pressure_cases=" << pressureCases << '\n'
            << "transition_cases=" << transitionCases << '\n'
            << "recovery_window_values_tested=1_TO_7\n"
            << "action_profile_cases=4\n"
            << "controller_parameters_calibrated=NO\n"
            << "policy_actuation_executed=NO\n"
            << "scientific_values_generated=NO"
            << std::endl;

        return 0;
    }
    catch (const std::exception& error)
    {
        std::cerr
            << "SecurityOrchestrator reference comparison failed: "
            << error.what()
            << std::endl;
        return 1;
    }
}
